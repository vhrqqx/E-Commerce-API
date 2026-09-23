# Sử dụng Python runtime bản slim để tối ưu kích thước
FROM python:3.14-slim

# Ngăn Python ghi file .pyc và ép in log ra terminal ngay lập tức
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Cài đặt các gói phụ thuộc hệ thống cần thiết để biên dịch psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt dependencies trước để tận dụng Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn vào container
COPY . .

# Thiết lập PYTHONPATH trỏ vào thư mục gốc và thư mục src
ENV PYTHONPATH=/app:/app/src

# Mở cổng 8000
EXPOSE 8000

# Khởi chạy FastAPI thông qua uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]