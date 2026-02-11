from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import numpy as np
import joblib
import os
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="HUST Bank AI Core", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, 'model_core', 'lgbm_credit_model_v3.pkl')
META_PATH = os.path.join(BASE_DIR, 'model_core', 'model_metadata_v3.pkl')

print("Loading Model V3...")
try:
    model = joblib.load(MODEL_PATH)
    metadata = joblib.load(META_PATH)
    
    EXPECTED_FEATURES = metadata['features']
    # Threshold từ training là 0.6591, nhưng để an toàn trong thực tế, 
    # nên dùng mức bảo thủ hơn (ví dụ 0.5) hoặc dùng đúng ngưỡng tối ưu
    THRESHOLD = metadata.get('threshold', 0.5) 
    CAT_FEATURES = metadata.get('cat_features', [])
    
    print(f"Model V3 Loaded! Threshold: {THRESHOLD:.4f}")
except Exception as e:
    print(f"❌ Error: {e}")
    THRESHOLD = 0.5

# ĐỊNH NGHĨA INPUT MỚI
class CreditApplication(BaseModel):
    # Tài chính
    AMT_INCOME_TOTAL: float
    AMT_CREDIT: float
    AMT_ANNUITY: float
    DAYS_BIRTH: int       # Số âm
    DAYS_EMPLOYED: int    # Số âm
    
    # Hành vi & Lịch sử 
    NAME_HOUSING_TYPE: str   # House / apartment, Rented apartment...
    NAME_FAMILY_STATUS: str  # Married, Single...
    EXT_SOURCE_2: float      # Điểm tín dụng giả lập (0.1 - 0.9)

@app.post("/predict")
def predict_credit_score(data: CreditApplication):
    # LAYER 1: HARD RULES 
    if data.AMT_INCOME_TOTAL < 10_000_000: # Ví dụ chặn dưới 10tr/năm
        return {"status": "REJECT", "probability": 1.0, "credit_score": 300, "message": "Thu nhập dưới chuẩn tối thiểu."}
        
    income_credit_ratio = data.AMT_CREDIT / data.AMT_INCOME_TOTAL
    if income_credit_ratio > 20:
        return {"status": "REJECT", "probability": 0.99, "credit_score": 300, "message": f"Khoản vay gấp {income_credit_ratio:.1f} lần thu nhập."}

    # LAYER 2: AI PREDICTION (V3) 
    try:
        # 1. Tạo DataFrame từ Input
        # Lưu ý: Gán EXT_SOURCE_3 bằng EXT_SOURCE_2 (giả định 2 nguồn tin giống nhau)
        input_dict = {
            'AMT_INCOME_TOTAL': [data.AMT_INCOME_TOTAL],
            'AMT_CREDIT': [data.AMT_CREDIT],
            'AMT_ANNUITY': [data.AMT_ANNUITY],
            'DAYS_BIRTH': [data.DAYS_BIRTH],
            'DAYS_EMPLOYED': [data.DAYS_EMPLOYED],
            'NAME_HOUSING_TYPE': [data.NAME_HOUSING_TYPE],
            'NAME_FAMILY_STATUS': [data.NAME_FAMILY_STATUS],
            'EXT_SOURCE_2': [data.EXT_SOURCE_2],
            'EXT_SOURCE_3': [data.EXT_SOURCE_2] 
        }
        df = pd.DataFrame(input_dict)
        
        # 2. Convert Category
        for col in CAT_FEATURES:
            if col in df.columns:
                df[col] = df[col].astype('category')

        # 3. Feature Engineering 
        df['CREDIT_INCOME_PERCENT'] = df['AMT_CREDIT'] / df['AMT_INCOME_TOTAL']
        df['ANNUITY_INCOME_PERCENT'] = df['AMT_ANNUITY'] / (df['AMT_INCOME_TOTAL'] / 12)
        df['CREDIT_TERM'] = df['AMT_CREDIT'] / df['AMT_ANNUITY']
        df['DAYS_EMPLOYED_PERCENT'] = df['DAYS_EMPLOYED'] / df['DAYS_BIRTH']
        
        # 4. Đảm bảo đủ cột và đúng thứ tự
        for col in EXPECTED_FEATURES:
            if col not in df.columns:
                df[col] = 0 # Fill cột thiếu nếu có
        
        df = df[EXPECTED_FEATURES]
        
        # 5. Dự đoán
        prob_default = model.predict_proba(df)[0][1]
        
        # 6. Kết luận
        # Nếu xác suất vỡ nợ > Threshold -> Từ chối
        status = "REJECT" if prob_default >= THRESHOLD else "APPROVE"
        
        # Mapping Score: 
        # Xác suất 0.65 (ngưỡng) -> Score 600 (trung bình)
        # Xác suất 0.1 -> Score 800 (tốt)
        # Xác suất 0.9 -> Score 300 (tệ)
        score = int(850 - (prob_default * 500)) 
        
        msg = f"Hồ sơ tín dụng Tốt. Rủi ro: {prob_default:.1%}"
        if status == "REJECT":
            msg = f"Rủi ro cao ({prob_default:.1%}) do lịch sử tín dụng hoặc yếu tố hành vi."

        return {
            "status": status,
            "probability": float(prob_default),
            "threshold": float(THRESHOLD),
            "credit_score": score,
            "message": msg
        }
        
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Lỗi xử lý AI Core")