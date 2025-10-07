# 使用 Python 3.12 官方映像
FROM python:3.12-slim

# 設定工作目錄
WORKDIR /app

# 複製依賴檔案
COPY requirements.txt .

# 安裝依賴套件
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式程式碼
COPY main.py .

# 設定環境變數
ENV PORT=8080

# 暴露端口
EXPOSE 8080

# 使用 gunicorn 啟動 Flask 應用
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
