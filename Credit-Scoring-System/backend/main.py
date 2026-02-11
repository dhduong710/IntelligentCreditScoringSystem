from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import numpy as np
import joblib
import os
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="HUST Bank AI Core", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sử dụng đường dẫn tuyệt đối dựa trên vị trí của file hiện tại
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, 'model_core', 'lgbm_credit_model_focused.pkl')
META_PATH = os.path.join(BASE_DIR, 'model_core', 'model_metadata_focused.pkl')

print("Loading Focused Model...")
try:
    model = joblib.load(MODEL_PATH)
    metadata = joblib.load(META_PATH)
    EXPECTED_FEATURES = metadata['features']
    THRESHOLD = metadata['threshold']
    print(f"Model loaded! Threshold: {THRESHOLD:.4f}")
except Exception as e:
    print(f"Error: {e}")
    THRESHOLD = 0.5

# Cấu hình ngưỡng cứng 
MIN_INCOME = 3_000_000        # Lương tối thiểu 3 triệu/tháng mới được vay
MAX_DTI = 0.7                 # Tổng nợ/Thu nhập không quá 70%
MAX_LOAN_TO_INCOME = 15       # Không vay quá 15 lần thu nhập năm 
MIN_AGE = 20
MAX_AGE = 60

class CreditApplication(BaseModel):
    AMT_INCOME_TOTAL: float
    AMT_CREDIT: float
    AMT_ANNUITY: float
    DAYS_BIRTH: int       # Input là số âm từ UI
    DAYS_EMPLOYED: int    # Input là số âm từ UI
    
    CODE_GENDER: str = 'M' 
    EDUCATION: str = 'University'

@app.post("/predict")
def predict_credit_score(data: CreditApplication):
    # LAYER 1: KIỂM TRA DỮ LIỆU RÁC
    if data.AMT_INCOME_TOTAL < MIN_INCOME * 12: # So sánh theo năm
        return {
            "status": "REJECT",
            "probability": 1.0,
            "credit_score": 300,
            "message": f"Thu nhập không đủ điều kiện tối thiểu ({MIN_INCOME:,.0f} VND/tháng)."
        }
    
    # LAYER 2: LUẬT CỨNG NGÂN HÀNG
    # Rule A: Debt-to-Income (DTI) Ratio
    # Khả năng trả nợ (Annuity) không được chiếm quá 70% thu nhập tháng
    monthly_income = data.AMT_INCOME_TOTAL / 12
    dti_ratio = data.AMT_ANNUITY / monthly_income
    
    if dti_ratio > MAX_DTI:
        return {
            "status": "REJECT",
            "probability": 0.95,
            "credit_score": 350,
            "message": f"Gánh nặng nợ quá cao! Khoản trả hàng tháng chiếm {dti_ratio:.1%} thu nhập (Max: {MAX_DTI:.0%})."
        }

    # Rule B: Loan-to-Income Ratio
    # Vay 100 tỷ với lương 1 triệu -> Chặn ngay
    loan_income_ratio = data.AMT_CREDIT / data.AMT_INCOME_TOTAL
    if loan_income_ratio > MAX_LOAN_TO_INCOME:
        return {
            "status": "REJECT",
            "probability": 0.99,
            "credit_score": 320,
            "message": f"Khoản vay quá lớn ({loan_income_ratio:.1f} lần thu nhập). Giới hạn tối đa: {MAX_LOAN_TO_INCOME} lần."
        }

    # Rule C: Age Check
    age = abs(data.DAYS_BIRTH) / 365
    if age < MIN_AGE or age > MAX_AGE:
        return {
            "status": "REJECT",
            "probability": 0.80,
            "credit_score": 400,
            "message": f"Độ tuổi {age:.1f} không nằm trong khung hỗ trợ tín dụng ({MIN_AGE}-{MAX_AGE})."
        }

    # LAYER 3: AI SCORING 
    try:
        # Chuẩn bị dữ liệu cho Model 
        input_data = pd.DataFrame([{
            'AMT_INCOME_TOTAL': data.AMT_INCOME_TOTAL,
            'AMT_CREDIT': data.AMT_CREDIT,
            'AMT_ANNUITY': data.AMT_ANNUITY,
            'DAYS_BIRTH': data.DAYS_BIRTH,
            'DAYS_EMPLOYED': data.DAYS_EMPLOYED
        }])
        
        # Feature Engineering
        input_data['CREDIT_INCOME_PERCENT'] = input_data['AMT_CREDIT'] / input_data['AMT_INCOME_TOTAL']
        input_data['ANNUITY_INCOME_PERCENT'] = input_data['AMT_ANNUITY'] / (input_data['AMT_INCOME_TOTAL'] / 12)
        input_data['CREDIT_TERM'] = input_data['AMT_CREDIT'] / input_data['AMT_ANNUITY']
        input_data['DAYS_EMPLOYED_PERCENT'] = input_data['DAYS_EMPLOYED'] / input_data['DAYS_BIRTH']
        
        # Đảm bảo đủ cột
        for col in EXPECTED_FEATURES:
            if col not in input_data.columns:
                input_data[col] = 0
                
        # Dự đoán
        prob_default = model.predict_proba(input_data[EXPECTED_FEATURES])[0][1]
        
        # MODEL CALIBRATION (HIỆU CHỈNH)
        # Vì model hiện tại đang trả về xác suất rất thấp (do mất cân bằng dữ liệu)
        # Dùng một ngưỡng threshold hợp lý hơn bằng tay thay vì 0.9043 
        REALISTIC_THRESHOLD = 0.15 # Nếu xác suất vỡ nợ > 15% là coi như Rủi ro cao 
        
        status = "REJECT" if prob_default >= REALISTIC_THRESHOLD else "APPROVE"
        
        # Tính điểm Score (Mapping 0-15% xác suất sang thang điểm 600-850)
        # Logic: Xác suất càng thấp điểm càng cao
        normalized_score = int(850 - (prob_default / REALISTIC_THRESHOLD) * 250)
        if normalized_score < 300: normalized_score = 300
        
        msg = f"Hồ sơ tín dụng tốt. Đủ điều kiện phê duyệt. Xác suất rủi ro: {prob_default:.1%}." if status == "APPROVE" else f"Hồ sơ nằm trong vùng rủi ro cao theo đánh giá AI. Xác suất rủi ro: {prob_default:.1%}."

        return {
            "status": status,
            "probability": float(prob_default),
            "threshold": float(REALISTIC_THRESHOLD),
            "credit_score": normalized_score,
            "message": msg
        }
        
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Lỗi xử lý AI")