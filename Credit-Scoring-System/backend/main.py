from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import numpy as np
import joblib
import os
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="HUST Bank Intelligent System", version="Final")

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

# NGHIỆP VỤ NGÂN HÀNG 
MIN_INCOME = 5_000_000          # Lương tối thiểu 5 triệu
MAX_DTI = 0.6                   # Trả nợ không quá 60% thu nhập
MAX_LOAN_TERM_MONTHS = 360      # Vay tối đa 30 năm (Ngăn chặn nhập trả hàng tháng quá nhỏ)
MIN_LOAN_TERM_MONTHS = 3        # Vay tối thiểu 3 tháng (Ngăn chặn nhập trả hàng tháng quá lớn)
AI_STRICT_THRESHOLD = 0.15      # Ngưỡng AI: Rủi ro > 15% là TỪ CHỐI

print("Loading AI Core...")
try:
    model = joblib.load(MODEL_PATH)
    metadata = joblib.load(META_PATH)
    EXPECTED_FEATURES = metadata['features']
    CAT_FEATURES = metadata.get('cat_features', [])
    print("System Ready!")
except Exception as e:
    print(f"❌ Error: {e}")

class CreditApplication(BaseModel):
    AMT_INCOME_TOTAL: float
    AMT_CREDIT: float
    AMT_ANNUITY: float
    DAYS_BIRTH: int       # Số âm
    DAYS_EMPLOYED: int    # Số âm
    NAME_HOUSING_TYPE: str
    NAME_FAMILY_STATUS: str
    EXT_SOURCE_2: float   # Điểm tín dụng

@app.post("/predict")
def predict_credit_score(data: CreditApplication):
    # LAYER 1: BUSINESS LOGIC CHECK
    
    # 1. Kiểm tra Thời hạn vay 
    if data.AMT_ANNUITY <= 0:
        return {"status": "REJECT", "probability": 1.0, "credit_score": 300, "message": "Số tiền trả hàng tháng không hợp lệ."}
    
    term_months = data.AMT_CREDIT / data.AMT_ANNUITY
    term_years = term_months / 12
    
    if term_months > MAX_LOAN_TERM_MONTHS:
        return {
            "status": "REJECT",
            "probability": 1.0,
            "threshold": AI_STRICT_THRESHOLD,
            "credit_score": 300,
            "message": f"Thời gian trả nợ kéo dài {term_years:.1f} năm là không hợp lệ. Tối đa cho phép: 30 năm."
        }
        
    if term_months < MIN_LOAN_TERM_MONTHS:
        return {
            "status": "REJECT", 
            "probability": 0.9, 
            "credit_score": 350, 
            "message": "Thời gian vay quá ngắn (dưới 3 tháng)."
        }

    # 2. Kiểm tra Gánh nặng nợ 
    monthly_income = data.AMT_INCOME_TOTAL / 12
    dti_ratio = data.AMT_ANNUITY / monthly_income
    
    if dti_ratio > MAX_DTI:
        return {
            "status": "REJECT",
            "probability": 0.85 + (dti_ratio * 0.1),
            "threshold": AI_STRICT_THRESHOLD,
            "credit_score": 350,
            "message": f"Số tiền trả hàng tháng chiếm {dti_ratio:.1%} thu nhập (Nhiều nhất: {MAX_DTI:.0%})."
        }

    # 3. Kiểm tra Thu nhập tối thiểu
    if data.AMT_INCOME_TOTAL < MIN_INCOME * 12:
        return {"status": "REJECT", "probability": 1.0, "credit_score": 300, "message": "Thu nhập không đủ điều kiện vay."}

    # LAYER 2: AI PREDICTION
    try:
        input_dict = {
            'AMT_INCOME_TOTAL': [data.AMT_INCOME_TOTAL],
            'AMT_CREDIT': [data.AMT_CREDIT],
            'AMT_ANNUITY': [data.AMT_ANNUITY],
            'DAYS_BIRTH': [data.DAYS_BIRTH],
            'DAYS_EMPLOYED': [data.DAYS_EMPLOYED],
            'NAME_HOUSING_TYPE': [data.NAME_HOUSING_TYPE],
            'NAME_FAMILY_STATUS': [data.NAME_FAMILY_STATUS],
            'EXT_SOURCE_2': [data.EXT_SOURCE_2],
            'EXT_SOURCE_3': [data.EXT_SOURCE_2] # Giả lập nguồn 3 giống nguồn 2
        }
        df = pd.DataFrame(input_dict)
        
        # Xử lý Category
        for col in CAT_FEATURES:
            if col in df.columns:
                df[col] = df[col].astype('category')

        # Feature Engineering 
        df['CREDIT_INCOME_PERCENT'] = df['AMT_CREDIT'] / df['AMT_INCOME_TOTAL']
        df['ANNUITY_INCOME_PERCENT'] = df['AMT_ANNUITY'] / (df['AMT_INCOME_TOTAL'] / 12)
        df['CREDIT_TERM'] = df['AMT_CREDIT'] / df['AMT_ANNUITY']
        df['DAYS_EMPLOYED_PERCENT'] = df['DAYS_EMPLOYED'] / df['DAYS_BIRTH']
        
        # Fill missing & Select columns
        for col in EXPECTED_FEATURES:
            if col not in df.columns: df[col] = 0
        df = df[EXPECTED_FEATURES]
        
        # DỰ ĐOÁN
        prob_default = model.predict_proba(df)[0][1]
        
        # QUYẾT ĐỊNH CUỐI CÙNG
        status = "REJECT" if prob_default >= AI_STRICT_THRESHOLD else "APPROVE"
        
        # Tính điểm Score (Logic: Risk càng thấp điểm càng cao)
        # Risk < 15% -> Score 700-850
        # Risk > 15% -> Score 300-699
        if prob_default <= AI_STRICT_THRESHOLD:
            score = int(850 - (prob_default / AI_STRICT_THRESHOLD) * 150)
        else:
            score = int(700 - ((prob_default - AI_STRICT_THRESHOLD) / (1 - AI_STRICT_THRESHOLD)) * 400)
            
        if score < 300: score = 300

        msg = f"Hồ sơ tín dụng Rất Tốt. Rủi ro: {prob_default:.1%}"
        if status == "REJECT":
            msg = f"Rủi ro tín dụng cao ({prob_default:.1%}) dựa trên phân tích hành vi & lịch sử."

        return {
            "status": status,
            "probability": float(prob_default),
            "threshold": float(AI_STRICT_THRESHOLD),
            "credit_score": score,
            "message": msg
        }
        
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Lỗi xử lý AI")