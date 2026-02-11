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
    # BUSINESS RULES CHECK (LUẬT CỨNG) - Bắt các case vô lý
    # Rule 1: Vay gấp 20 lần thu nhập năm -> REJECT NGAY
    income_credit_ratio = data.AMT_CREDIT / data.AMT_INCOME_TOTAL
    if income_credit_ratio > 20:
        return {
            "status": "REJECT",
            "probability": 0.99, # Max risk
            "threshold": THRESHOLD,
            "credit_score": 300,
            "message": f"TỪ CHỐI TỰ ĐỘNG: Khoản vay gấp {income_credit_ratio:.1f} lần thu nhập (Giới hạn: 20x)."
        }

    # Rule 2: Tuổi quá cao hoặc quá thấp (dưới 18 hoặc trên 70)
    age = abs(data.DAYS_BIRTH) / 365
    if age < 18 or age > 70:
        return {
            "status": "REJECT",
            "probability": 0.85,
            "threshold": THRESHOLD,
            "credit_score": 450,
            "message": f"Độ tuổi {age:.1f} không nằm trong chính sách hỗ trợ (18-70 tuổi)."
        }
        
    # Rule 3: Thất nghiệp (DAYS_EMPLOYED = 365243 là mã thất nghiệp trong dataset này, hoặc 0)
    if data.DAYS_EMPLOYED == 0 or data.DAYS_EMPLOYED > 0:
         return {
            "status": "REJECT",
            "probability": 0.90,
            "threshold": THRESHOLD,
            "credit_score": 350,
            "message": "Khách hàng không chứng minh được thâm niên làm việc."
        }

    # AI MODEL PREDICTION (Nếu qua được vòng trên)
    try:
        # Tạo DataFrame chỉ với các cột model cần
        input_data = {
            'AMT_INCOME_TOTAL': [data.AMT_INCOME_TOTAL],
            'AMT_CREDIT': [data.AMT_CREDIT],
            'AMT_ANNUITY': [data.AMT_ANNUITY],
            'DAYS_BIRTH': [data.DAYS_BIRTH],
            'DAYS_EMPLOYED': [data.DAYS_EMPLOYED]
        }
        df = pd.DataFrame(input_data)
        
        # Feature Engineering 
        df['CREDIT_INCOME_PERCENT'] = df['AMT_CREDIT'] / df['AMT_INCOME_TOTAL']
        df['ANNUITY_INCOME_PERCENT'] = df['AMT_ANNUITY'] / (df['AMT_INCOME_TOTAL'] / 12)
        df['CREDIT_TERM'] = df['AMT_CREDIT'] / df['AMT_ANNUITY']
        df['DAYS_EMPLOYED_PERCENT'] = df['DAYS_EMPLOYED'] / df['DAYS_BIRTH']
        
        # Sắp xếp cột
        df = df[EXPECTED_FEATURES]
        
        # Dự đoán
        prob_default = model.predict_proba(df)[0][1]
        
        # Kết quả
        status = "REJECT" if prob_default >= THRESHOLD else "APPROVE"
        
        # Tính điểm giả lập (Probability càng cao điểm càng thấp)
        # Thang 300 - 850
        score = int(850 - (prob_default * 550))
        
        # Tin nhắn động
        msg = ""
        if status == "REJECT":
            msg = f"Rủi ro tín dụng cao ({prob_default:.1%}). Cần thẩm định thêm tài sản đảm bảo."
        else:
            msg = f"Hồ sơ tín dụng tốt. Xác suất rủi ro thấp ({prob_default:.1%})."

        return {
            "status": status,
            "probability": float(prob_default),
            "threshold": float(THRESHOLD),
            "credit_score": score,
            "message": msg
        }
        
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Lỗi xử lý AI Core")