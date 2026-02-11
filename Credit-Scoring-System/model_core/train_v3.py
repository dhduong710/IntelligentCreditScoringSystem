import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score, precision_recall_curve
import joblib
import gc
import os

# CẤU HÌNH ĐƯỜNG DẪN
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'application_train.csv')
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lgbm_credit_model_v3.pkl')
META_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model_metadata_v3.pkl')

def train_v3_kfold_model():
    print("Đang tải dữ liệu V3 (K-Fold)...")
    df = pd.read_csv(DATA_PATH)
    
    # CHỌN FEATURE CHUẨN NGHIỆP VỤ
    # Kết hợp Tài chính + Hành vi + Lịch sử tín dụng
    input_cols = [
        'TARGET',
        'AMT_INCOME_TOTAL',
        'AMT_CREDIT', 
        'AMT_ANNUITY',
        'DAYS_BIRTH',
        'DAYS_EMPLOYED',
        'NAME_HOUSING_TYPE',       # Quan trọng: Nhà thuê hay nhà riêng
        'NAME_FAMILY_STATUS',      # Quan trọng: Ổn định gia đình
        'EXT_SOURCE_2',            # QUAN TRỌNG NHẤT: Điểm tín dụng CIC
        'EXT_SOURCE_3'             # Điểm phụ
    ]
    
    # Lọc lấy các cột tồn tại
    existing_cols = [c for c in input_cols if c in df.columns]
    df = df[existing_cols]

    # 2. XỬ LÝ DỮ LIỆU
    # Điền dữ liệu thiếu cho EXT_SOURCE bằng Median
    df['EXT_SOURCE_2'] = df['EXT_SOURCE_2'].fillna(df['EXT_SOURCE_2'].median())
    df['EXT_SOURCE_3'] = df['EXT_SOURCE_3'].fillna(df['EXT_SOURCE_3'].median())
    
    # Xử lý biến Category
    categorical_feats = ['NAME_HOUSING_TYPE', 'NAME_FAMILY_STATUS']
    for col in categorical_feats:
        if col in df.columns:
            df[col] = df[col].astype('category')
            
    # Feature Engineering
    # Tỷ lệ vay / thu nhập
    df['CREDIT_INCOME_PERCENT'] = df['AMT_CREDIT'] / df['AMT_INCOME_TOTAL']
    # Tỷ lệ trả hàng tháng / thu nhập
    df['ANNUITY_INCOME_PERCENT'] = df['AMT_ANNUITY'] / (df['AMT_INCOME_TOTAL'] / 12)
    # Thời hạn vay
    df['CREDIT_TERM'] = df['AMT_CREDIT'] / df['AMT_ANNUITY']
    # Thâm niên / Tuổi
    df['DAYS_EMPLOYED_PERCENT'] = df['DAYS_EMPLOYED'] / df['DAYS_BIRTH']

    # Xử lý vô cực
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    
    print(f"Bắt đầu train V3 với {df.shape[1]} features sử dụng 5-Fold CV...")

    X = df.drop(columns=['TARGET'])
    y = df['TARGET']
    
    # 3. TRAINING VỚI STRATIFIED K-FOLD 
    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    oof_preds = np.zeros(X.shape[0])
    
    for n_fold, (train_idx, valid_idx) in enumerate(folds.split(X, y)):
        X_train, y_train = X.iloc[train_idx], y.iloc[train_idx]
        X_valid, y_valid = X.iloc[valid_idx], y.iloc[valid_idx]
        
        clf = lgb.LGBMClassifier(
            n_estimators=2000,
            learning_rate=0.02,
            num_leaves=31,
            max_depth=8,
            objective='binary', 
            class_weight='balanced', 
            random_state=42,
            n_jobs=-1,
            verbose=-1
        )
        
        clf.fit(
            X_train, y_train, 
            eval_set=[(X_valid, y_valid)], 
            eval_metric='auc',
            callbacks=[lgb.early_stopping(100)]
        )
        
        # Dự đoán trên tập validation
        oof_preds[valid_idx] = clf.predict_proba(X_valid)[:, 1]
        
        fold_auc = roc_auc_score(y_valid, oof_preds[valid_idx])
        print(f"Fold {n_fold+1} AUC: {fold_auc:.5f}")

    # Đánh giá tổng thể
    total_auc = roc_auc_score(y, oof_preds)
    print(f"\nFINAL V3 AUC: {total_auc:.5f}")
    
    # Tìm ngưỡng tối ưu (Best Threshold)
    precision, recall, thresholds = precision_recall_curve(y, oof_preds)
    fscore = (2 * precision * recall) / (precision + recall)
    # Xử lý trường hợp chia cho 0 nếu có
    fscore = np.nan_to_num(fscore)
    best_thresh = thresholds[np.argmax(fscore)]
    print(f"Ngưỡng tối ưu (Best Threshold): {best_thresh:.4f}")

    # 4. RETRAIN FULL MODEL & SAVE 
    print("Đang retrain model trên toàn bộ dữ liệu...")
    final_model = lgb.LGBMClassifier(
        n_estimators=2000, learning_rate=0.02, num_leaves=31, max_depth=8,
        objective='binary', class_weight='balanced', random_state=42
    )
    final_model.fit(X, y)
    
    # Lưu Model
    joblib.dump(final_model, MODEL_PATH)
    
    # Lưu Metadata (Gồm cả tên các cột category để xử lý ở backend)
    joblib.dump({
        'features': X.columns.tolist(),
        'cat_features': categorical_feats,
        'threshold': best_thresh
    }, META_PATH)
    
    print("Đã lưu Model V3 chuẩn K-Fold.")

if __name__ == "__main__":
    train_v3_kfold_model()