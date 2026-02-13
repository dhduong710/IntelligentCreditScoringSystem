# 1. Dùng Python 3.10 làm môi trường gốc
FROM python:3.10

# 2. Tạo thư mục làm việc trong container
WORKDIR /code

# 3. Copy các file yêu cầu cài đặt
COPY backend/requirements.txt /code/requirements.txt

# 4. Cài đặt thư viện (Thêm shap, lightgbm, fastapi...)
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 5. Copy toàn bộ code vào container
# Copy thư mục model
COPY model_core /code/model_core
# Copy thư mục backend
COPY backend /code/backend
# Copy thư mục frontend build
# Lưu ý: Copy nội dung trong frontend/dist vào thư mục /code/static
COPY frontend/dist /code/static

# 6. Cấp quyền truy cập 
RUN chmod -R 777 /code

# 7. Mở cổng 7860 (Cổng mặc định của Hugging Face Spaces)
EXPOSE 7860

# 8. Lệnh chạy server
# Host 0.0.0.0 để public ra ngoài
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]