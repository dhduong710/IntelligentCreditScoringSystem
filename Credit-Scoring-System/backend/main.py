from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import numpy as np
import joblib
import shap
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="HUST Bank Intelligent System", version="Final + SHAP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, '../model_core/lgbm_credit_model_v3.pkl')
META_PATH = os.path.join(BASE_DIR, '../model_core/model_metadata_v3.pkl')

# HARD RULES
MIN_INCOME = 5_000_000
MAX_DTI = 0.6
MAX_LOAN_TERM_MONTHS = 360
MIN_LOAN_TERM_MONTHS = 3
FINAL_THRESHOLD = 0.15 

print("Loading AI Core & Explainer...")
try:
    model = joblib.load(MODEL_PATH)
    metadata = joblib.load(META_PATH)
    EXPECTED_FEATURES = metadata['features']
    CAT_FEATURES = metadata.get('cat_features', [])
    
    # KHỞI TẠO SHAP EXPLAINER (Chỉ làm 1 lần khi start server)
    # TreeExplainer rất nhanh với LightGBM
    explainer = shap.TreeExplainer(model)
    
    print("System Ready with Explainable AI!")
except Exception as e:
    print(f"❌ Error: {e}")

# MAPPING TÊN CỘT SANG TIẾNG VIỆT
FEATURE_NAME_MAP = {
    'AMT_INCOME_TOTAL': 'Tổng thu nhập',
    'AMT_CREDIT': 'Số tiền vay',
    'AMT_ANNUITY': 'Số tiền trả hàng tháng',
    'DAYS_BIRTH': 'Tuổi tác',
    'DAYS_EMPLOYED': 'Thâm niên làm việc',
    'NAME_HOUSING_TYPE': 'Loại hình nhà ở',
    'NAME_FAMILY_STATUS': 'Tình trạng hôn nhân',
    'EXT_SOURCE_2': 'Điểm lịch sử tín dụng',
    'EXT_SOURCE_3': 'Điểm tín dụng phụ',
    'CREDIT_INCOME_PERCENT': 'Tỷ lệ Vay / Thu nhập',
    'ANNUITY_INCOME_PERCENT': 'Gánh nặng nợ / Thu nhập',
    'CREDIT_TERM': 'Thời hạn vay',
    'DAYS_EMPLOYED_PERCENT': 'Tỷ lệ Thâm niên / Tuổi'
}

class CreditApplication(BaseModel):
    AMT_INCOME_TOTAL: float
    AMT_CREDIT: float
    AMT_ANNUITY: float
    DAYS_BIRTH: int
    DAYS_EMPLOYED: int
    NAME_HOUSING_TYPE: str
    NAME_FAMILY_STATUS: str
    EXT_SOURCE_2: float

def get_top_reasons(shap_values, feature_names, is_reject):
    """
    Hàm tìm ra Top 3 lý do quan trọng nhất.
    - Nếu REJECT (Rủi ro cao): Tìm các feature đẩy xác suất TĂNG (SHAP dương lớn nhất).
    - Nếu APPROVE (An toàn): Tìm các feature kéo xác suất GIẢM (SHAP âm bé nhất).
    """
    # shap_values[1] là tác động lên lớp 1 (Vỡ nợ)
    # shap_values trả về mảng shape (1, n_features) -> lấy [0]
    vals = shap_values[0] if isinstance(shap_values, list) else shap_values
    
    # Tạo list (tên feature, giá trị shap)
    feature_impacts = list(zip(feature_names, vals))
    
    if is_reject:
        # Sắp xếp giảm dần (Lấy cái dương lớn nhất - Nguyên nhân gây rủi ro)
        sorted_impacts = sorted(feature_impacts, key=lambda x: x[1], reverse=True)
    else:
        # Sắp xếp tăng dần (Lấy cái âm bé nhất - Nguyên nhân giúp an toàn)
        sorted_impacts = sorted(feature_impacts, key=lambda x: x[1])
        
    top_3 = sorted_impacts[:3]
    
    reasons = []
    for feat, impact in top_3:
        # Chỉ lấy những lý do có tác động đáng kể (absolute > 0.01)
        if abs(impact) > 0.01:
            vn_name = FEATURE_NAME_MAP.get(feat, feat)
            
            # Chuyển SHAP value (log-odds) sang % thay đổi xác suất
            # Sử dụng hàm sigmoid để chuyển đổi chính xác
            impact_percent = 100 * (1 / (1 + np.exp(-impact)) - 0.5)
            
            if is_reject:
                reasons.append(f"{vn_name} làm tăng rủi ro (+{impact_percent:.1f}%)")
            else:
                reasons.append(f"{vn_name} giúp hồ sơ an toàn ({impact_percent:.1f}%)")
                
    return reasons if reasons else ["Hồ sơ cân bằng, không có yếu tố nổi bật."]

@app.post("/predict")
def predict_credit_score(data: CreditApplication):
    # HARD RULES 
    if data.AMT_ANNUITY <= 0:
        return {"status": "REJECT", "probability": 1.0, "credit_score": 300, "message": "Số tiền trả hàng tháng không hợp lệ."}
    
    term_months = data.AMT_CREDIT / data.AMT_ANNUITY
    if term_months > MAX_LOAN_TERM_MONTHS:
        return {"status": "REJECT", "probability": 1.0, "threshold": FINAL_THRESHOLD, "credit_score": 300, "message": f"Thời gian vay quá dài ({term_months/12:.1f} năm).", "reasons": ["Vi phạm chính sách thời hạn vay (Nhiều nhất 30 năm)"]}
        
    if data.AMT_INCOME_TOTAL < MIN_INCOME * 12:
        return {"status": "REJECT", "probability": 1.0, "credit_score": 300, "message": "Thu nhập không đủ điều kiện.", "reasons": ["Thu nhập dưới chuẩn tối thiểu"]}

    monthly_income = data.AMT_INCOME_TOTAL / 12
    dti_ratio = data.AMT_ANNUITY / monthly_income
    if dti_ratio > MAX_DTI:
        return {"status": "REJECT", "probability": 0.9, "credit_score": 350, "message": f"Gánh nặng nợ quá lớn ({dti_ratio:.1%}).", "reasons": ["Tỷ lệ Trả nợ/Thu nhập vượt quá 60%"]}

    # AI PREDICTION 
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
            'EXT_SOURCE_3': [data.EXT_SOURCE_2] 
        }
        df = pd.DataFrame(input_dict)
        
        for col in CAT_FEATURES:
            if col in df.columns: df[col] = df[col].astype('category')

        # Feature Engineering
        df['CREDIT_INCOME_PERCENT'] = df['AMT_CREDIT'] / df['AMT_INCOME_TOTAL']
        df['ANNUITY_INCOME_PERCENT'] = df['AMT_ANNUITY'] / (df['AMT_INCOME_TOTAL'] / 12)
        df['CREDIT_TERM'] = df['AMT_CREDIT'] / df['AMT_ANNUITY']
        df['DAYS_EMPLOYED_PERCENT'] = df['DAYS_EMPLOYED'] / df['DAYS_BIRTH']
        
        for col in EXPECTED_FEATURES:
            if col not in df.columns: df[col] = 0
        df = df[EXPECTED_FEATURES]
        
        # 1. Predict Probability
        prob_default = model.predict_proba(df)[0][1]
        
        # 2. Calculate SHAP Values 
        # shap_values trả về list các array cho từng class, ta quan tâm class 1 (Vỡ nợ)
        shap_vals = explainer.shap_values(df)
        
        # LightGBM binary classification thường trả về list [array_class0, array_class1]
        # Hoặc chỉ 1 array nếu objective khác. 
        if isinstance(shap_vals, list) and len(shap_vals) == 2:
            target_shap = shap_vals[1][0] # Lấy SHAP của class 1, dòng đầu tiên
        else:
            target_shap = shap_vals[0] # Fallback
            
        # Logic Status
        status = "REJECT" if prob_default >= FINAL_THRESHOLD else "APPROVE"
        
        # 3. Lấy lý do từ SHAP
        reasons = get_top_reasons(target_shap, EXPECTED_FEATURES, is_reject=(status=="REJECT"))

        # Score Calculation
        if prob_default <= FINAL_THRESHOLD:
            score = int(850 - (prob_default / FINAL_THRESHOLD) * 150)
        else:
            score = int(700 - ((prob_default - FINAL_THRESHOLD) / (1 - FINAL_THRESHOLD)) * 400)
        if score < 300: score = 300

        msg = f"Hồ sơ Rất Tốt. Rủi ro: ({prob_default:.1%})" if status == "APPROVE" else f"Rủi ro cao ({prob_default:.1%})."

        return {
            "status": status,
            "probability": float(prob_default),
            "threshold": float(FINAL_THRESHOLD),
            "credit_score": score,
            "message": msg,
            "reasons": reasons # Trả về mảng lý do
        }
        
    except Exception as e:
        print(f"SHAP Error: {e}")
        # Fallback nếu SHAP lỗi
        return {
            "status": "REJECT", "probability": 0.5, "credit_score": 500, 
            "message": "Lỗi hệ thống khi phân tích.", "reasons": ["Không thể xác định lý do"]
        }
    
# CẤU HÌNH SERVE FRONTEND (REACT)
# Lấy đường dẫn tuyệt đối đến thư mục chứa file tĩnh (React Build)
# Trong Docker, ta sẽ copy 'frontend/dist' vào thư mục '/code/static'
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../static")

# Kiểm tra nếu thư mục tồn tại (để tránh lỗi khi chạy local development)
if os.path.exists(STATIC_DIR):
    # Mount thư mục assets (css, js)
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")

    # Route mặc định trả về index.html
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        # Nếu gọi API thì không trả về HTML (đã xử lý ở trên)
        if full_path.startswith("predict") or full_path.startswith("docs"):
            return 
        
        # Trả về file index.html cho mọi route khác (để React Router xử lý)
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))