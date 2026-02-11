import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score, precision_recall_curve
import joblib
import gc
import os

# Sử dụng đường dẫn tuyệt đối dựa trên vị trí của file hiện tại
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'application_train.csv')
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lgbm_credit_model_focused.pkl')
META_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model_metadata_focused.pkl')

def train_focused_model():
    print("Đang tải dữ liệu...")
    df = pd.read_csv(DATA_PATH)
    
    # CHỈ GIỮ LẠI CÁC CỘT UI CÓ THỂ CUNG CẤP + TARGET
    # Đây là bước quan trọng nhất để model không bị "loãng"
    keep_cols = [
        'TARGET', 
        'AMT_INCOME_TOTAL', 
        'AMT_CREDIT', 
        'AMT_ANNUITY', 
        'DAYS_BIRTH', 
        'DAYS_EMPLOYED'
    ]
    df = df[keep_cols]
    
    # FEATURE ENGINEERING (Tạo đặc trưng từ những gì đang có)
    # Tỷ lệ nợ / thu nhập
    df['CREDIT_INCOME_PERCENT'] = df['AMT_CREDIT'] / df['AMT_INCOME_TOTAL']
    # Tỷ lệ trả hàng tháng / thu nhập tháng
    df['ANNUITY_INCOME_PERCENT'] = df['AMT_ANNUITY'] / (df['AMT_INCOME_TOTAL'] / 12)
    # Thời hạn vay (tháng)
    df['CREDIT_TERM'] = df['AMT_CREDIT'] / df['AMT_ANNUITY']
    # Tỷ lệ làm việc / tuổi
    df['DAYS_EMPLOYED_PERCENT'] = df['DAYS_EMPLOYED'] / df['DAYS_BIRTH']

    # Xử lý vô cực nếu có chia cho 0
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.fillna(0, inplace=True)

    print(f"Bắt đầu train model tập trung trên {df.shape[1]} features...")
    
    X = df.drop(columns=['TARGET'])
    y = df['TARGET']
    
    # Train 5-Fold
    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    oof_preds = np.zeros(X.shape[0])
    
    for n_fold, (train_idx, valid_idx) in enumerate(folds.split(X, y)):
        X_train, y_train = X.iloc[train_idx], y.iloc[train_idx]
        X_valid, y_valid = X.iloc[valid_idx], y.iloc[valid_idx]
        
        clf = lgb.LGBMClassifier(
            n_estimators=1000,
            learning_rate=0.05,
            num_leaves=31,
            max_depth=5,            # Giảm độ sâu để tránh học vẹt
            objective='binary', 
            class_weight='balanced', # BẮT BUỘC để bắt người nợ xấu
            random_state=42,
            n_jobs=-1,
            verbose=-1
        )
        
        clf.fit(X_train, y_train, eval_set=[(X_valid, y_valid)], callbacks=[lgb.early_stopping(50)])
        oof_preds[valid_idx] = clf.predict_proba(X_valid)[:, 1]

    # Tìm ngưỡng tối ưu mới
    precision, recall, thresholds = precision_recall_curve(y, oof_preds)
    fscore = (2 * precision * recall) / (precision + recall)
    best_thresh = thresholds[np.argmax(fscore)]
    
    auc = roc_auc_score(y, oof_preds)
    print(f"\nFOCUSED MODEL AUC: {auc:.5f}")
    print(f"Ngưỡng tối ưu mới: {best_thresh:.4f}")
    
    # Retrain Full Model
    final_model = lgb.LGBMClassifier(
        n_estimators=1000, learning_rate=0.05, num_leaves=31, max_depth=5,
        objective='binary', class_weight='balanced', random_state=42
    )
    final_model.fit(X, y)
    
    # Lưu
    joblib.dump(final_model, MODEL_PATH)
    joblib.dump({
        'features': X.columns.tolist(),
        'threshold': best_thresh
    }, META_PATH)
    print("Đã lưu model tinh gọn!")

if __name__ == "__main__":
    train_focused_model()