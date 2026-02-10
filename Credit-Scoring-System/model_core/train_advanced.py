import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score, f1_score, precision_recall_curve
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import re
import gc

DATA_PATH = '../data/application_train.csv'
MODEL_PATH = 'lgbm_credit_model_final.pkl'
N_FOLDS = 5

def load_and_preprocess_data():
    print("Đang tải và xử lý dữ liệu nâng cao...")
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
    
    # XỬ LÝ DỮ LIỆU THIẾU
    missing_cols = df.columns[df.isnull().mean() > 0.5]
    df = df.drop(columns=missing_cols)
    
    # NATIVE CATEGORICAL HANDLING 
    # Thay vì One-Hot, chuyển về dạng 'category' để LightGBM tự xử lý tối ưu
    categorical_cols = [col for col in df.columns if df[col].dtype == 'object']
    for col in categorical_cols:
        df[col] = df[col].astype('category')
        
    # Sửa tên cột (Loại bỏ ký tự đặc biệt để tránh lỗi JSON sau này)
    df = df.rename(columns = lambda x:re.sub('[^A-Za-z0-9_]+', '', x))
    
    return df, categorical_cols

def find_optimal_threshold(y_true, y_pred_proba):
    """Tìm ngưỡng (threshold) để F1-Score cao nhất"""
    precision, recall, thresholds = precision_recall_curve(y_true, y_pred_proba)
    fscore = (2 * precision * recall) / (precision + recall)
    ix = np.argmax(fscore)
    best_thresh = thresholds[ix]
    print(f'Ngưỡng tối ưu (Best Threshold): {best_thresh:.4f}, F1-Score: {fscore[ix]:.4f}')
    return best_thresh

def train_kfold_model(df, cat_feats):
    X = df.drop(columns=['TARGET', 'SK_ID_CURR'])
    y = df['TARGET']
    feature_names = X.columns.tolist()
    
    # Stratified K-Fold: Đảm bảo tỷ lệ nợ xấu ở mỗi fold là như nhau (8%)
    folds = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=42)
    
    oof_preds = np.zeros(X.shape[0]) # Lưu dự đoán Out-of-Fold
    models = []
    
    print(f"Bắt đầu training {N_FOLDS}-Fold Cross Validation...")
    
    for n_fold, (train_idx, valid_idx) in enumerate(folds.split(X, y)):
        X_train, y_train = X.iloc[train_idx], y.iloc[train_idx]
        X_valid, y_valid = X.iloc[valid_idx], y.iloc[valid_idx]
        
        # Cấu hình LightGBM tối ưu cho Imbalanced Data
        clf = lgb.LGBMClassifier(
            n_estimators=2000,
            learning_rate=0.03,      # Giảm LR để học kỹ hơn
            num_leaves=31,
            max_depth=8,             # Tránh overfitting
            objective='binary', 
            class_weight='balanced', # Quan trọng để xử lý mất cân bằng
            random_state=42,
            n_jobs=-1,
            verbose=-1
        )
        
        clf.fit(
            X_train, y_train, 
            eval_set=[(X_valid, y_valid)], 
            eval_metric='auc',
            categorical_feature=cat_feats, # Chỉ định cột category
            callbacks=[lgb.early_stopping(stopping_rounds=100), lgb.log_evaluation(0)] # Tắt log rác
        )
        
        y_pred_valid = clf.predict_proba(X_valid)[:, 1]
        oof_preds[valid_idx] = y_pred_valid
        
        score = roc_auc_score(y_valid, y_pred_valid)
        print(f"   Fold {n_fold+1} | AUC: {score:.5f}")
        
        models.append(clf)
        
        # Clean RAM
        del X_train, y_train, X_valid, y_valid
        gc.collect()

    # Đánh giá tổng thể
    total_auc = roc_auc_score(y, oof_preds)
    print(f"\nFINAL AVG AUC: {total_auc:.5f}")
    
    # Tìm ngưỡng tối ưu
    best_threshold = find_optimal_threshold(y, oof_preds)

    # Retrain Full Model để Deploy (Ở đây lưu model tốt nhất trong các fold hoặc train lại)
    # Để đơn giản và hiệu quả, lưu model của Fold có AUC cao nhất hoặc retrain toàn bộ
    # Ở đây chọn cách Retrain toàn bộ với số rounds trung bình của các folds
    print("Đang retrain model trên toàn bộ dữ liệu để deploy...")
    final_model = lgb.LGBMClassifier(
        n_estimators=1500, learning_rate=0.03, num_leaves=31, max_depth=8,
        objective='binary', class_weight='balanced', random_state=42
    )
    final_model.fit(X, y, categorical_feature=cat_feats)
    
    # Lưu Model & Metadata
    joblib.dump(final_model, MODEL_PATH)
    
    # Lưu danh sách feature và ngưỡng tối ưu để API dùng
    metadata = {
        'features': feature_names,
        'threshold': best_threshold,
        'cat_features': cat_feats
    }
    joblib.dump(metadata, 'model_metadata.pkl')
    print(f"Đã lưu model và metadata. Sẵn sàng deploy.")
    
    return final_model, feature_names

def plot_feature_importance(model, feature_names):
    # Vẽ biểu đồ Feature Importance
    importance = model.feature_importances_
    feature_imp = pd.DataFrame(sorted(zip(importance, feature_names)), columns=['Value','Feature'])
    
    plt.figure(figsize=(10, 8))
    sns.barplot(x="Value", y="Feature", data=feature_imp.sort_values(by="Value", ascending=False).head(20))
    plt.title('Top 20 Features quan trọng nhất (LightGBM)')
    plt.tight_layout()
    plt.savefig('feature_importance.png') 
    print("Đã lưu biểu đồ Feature Importance vào 'feature_importance.png'")

if __name__ == "__main__":
    df, cat_feats = load_and_preprocess_data()
    model, features = train_kfold_model(df, cat_feats)
    plot_feature_importance(model, features)