import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report
import joblib
import gc

DATA_PATH = '../data/application_train.csv'
MODEL_PATH = 'lgbm_credit_model.pkl'

def load_and_preprocess_data():
    print("Đang tải dữ liệu...")
    df = pd.read_csv(DATA_PATH)
    
    # FEATURE ENGINEERING (TẠO ĐẶC TRƯNG MỚI)
    # Tỷ lệ: Tống số tiền vay / Thu nhập hàng năm (Vay nhiều quá mức lương?)
    df['CREDIT_INCOME_PERCENT'] = df['AMT_CREDIT'] / df['AMT_INCOME_TOTAL']
    # Tỷ lệ: Tiền trả hàng tháng / Thu nhập hàng tháng (Gánh nặng hàng tháng)
    df['ANNUITY_INCOME_PERCENT'] = df['AMT_ANNUITY'] / (df['AMT_INCOME_TOTAL'] / 12)
    # Tỷ lệ: Thời hạn vay (tháng)
    df['CREDIT_TERM'] = df['AMT_CREDIT'] / df['AMT_ANNUITY']
    # Tỷ lệ: Số ngày đi làm / Số ngày tuổi (Mức độ ổn định công việc)
    df['DAYS_EMPLOYED_PERCENT'] = df['DAYS_EMPLOYED'] / df['DAYS_BIRTH']
    
    # XỬ LÝ DỮ LIỆU THIẾU & DƯ THỪA
    # Loại bỏ các cột thiếu > 50% dữ liệu 
    missing_cols = df.columns[df.isnull().mean() > 0.5]
    print(f"Đang loại bỏ {len(missing_cols)} cột thiếu quá nhiều dữ liệu...")
    df = df.drop(columns=missing_cols)
    
    # Xử lý biến Categorical (One-Hot Encoding đơn giản)
    # Chỉ lấy các biến số (Numeric) và biến Categorical ít giá trị để demo nhanh
    categorical_cols = [col for col in df.columns if df[col].dtype == 'object']
    df = pd.get_dummies(df, columns=categorical_cols, dummy_na=True)
    
    # Điền dữ liệu thiếu còn lại bằng Median (cho an toàn)
    # Lưu ý: LightGBM tự xử lý được NaN, nhưng điền vào để đảm bảo tính ổn định khi Deploy
    df = df.fillna(df.median())
    
    # Đổi tên các cột (LightGBM không thích dấu cách hoặc ký tự lạ trong tên cột)
    df = df.rename(columns = lambda x:re.sub('[^A-Za-z0-9_]+', '', x))

    return df

def train_model(df):
    # Tách Features và Target
    X = df.drop(columns=['TARGET', 'SK_ID_CURR']) # Bỏ ID và Target
    y = df['TARGET']
    
    # Chia tập Train/Test (80% - 20%)
    # stratify=y để đảm bảo tập Test cũng có tỷ lệ nợ xấu 8% giống tập Train
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print(f"Bắt đầu train model với {X_train.shape[1]} features...")
    
    # Cấu hình LightGBM
    model = lgb.LGBMClassifier(
        n_estimators=1000,      # số cây tối đa.
        learning_rate=0.05,     # Tốc độ học. Thấp (0.01-0.05) thường tốt hơn nhưng chạy lâu hơn.
        num_leaves=31,          # Số lượng lá tối đa trên 1 cây. Đây là tham số quan trọng nhất để chỉnh độ phức tạp.
                                # Với LightGBM, num_leaves quan trọng hơn max_depth.
        objective='binary',     # Bài toán nhị phân (0: Trả tốt, 1: Nợ xấu).
        class_weight='balanced',# Cực quan trọng cho Credit Scoring: Cân bằng lại mẫu nợ xấu/tốt.
        random_state=42,        # Để kết quả chạy lại y hệt lần trước.
        n_jobs=-1               # Dùng tất cả nhân CPU để chạy cho nhanh.
)
    
    # Training
    model.fit(
        X_train, y_train, 
        eval_set=[(X_test, y_test)], 
        eval_metric='auc',
        callbacks=[lgb.early_stopping(stopping_rounds=100), lgb.log_evaluation(100)]
    )
    
    # Đánh giá
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, y_pred_proba)
    print(f"\nTraining hoàn tất! AUC Score: {auc:.4f}")
    
    if auc < 0.7:
        print("Model chưa tốt lắm (AUC < 0.7). Cần Feature Engineering thêm.")
    else:
        print("Model đạt chất lượng tốt (AUC > 0.7).")

    # Lưu model và danh sách features
    joblib.dump(model, MODEL_PATH)
    joblib.dump(X.columns.tolist(), 'model_features.pkl') # Lưu tên cột để lúc dự đoán dùng đúng thứ tự
    print(f"Đã lưu model tại: {MODEL_PATH}")

if __name__ == "__main__":
    import re # Import regex để sửa tên cột
    df = load_and_preprocess_data()
    train_model(df)