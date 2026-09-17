# ============================================================
# Dockerfile — 把 FastAPI 選課系統打包成可以獨立執行的容器
#
# 使用方式：
#   docker build -t course-enrollment .
#   docker run -p 8000:8000 course-enrollment
# 打開瀏覽器連 http://127.0.0.1:8000 即可看到選課畫面
# ============================================================

# ---- 1. 使用輕量級的 Python 基礎映像檔 ----
FROM python:3.10-slim

# ---- 2. 設定工作目錄（容器內的路徑）----
WORKDIR /app

# ---- 3. 先複製 requirements.txt 並安裝依賴 ----
# 先複製 requirements.txt 而不是整份程式碼，
# 這樣 requirements.txt 沒變的話，pip install 這層可以快取，build 會更快
COPY requirements.txt .

# 安裝所有 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# ---- 4. 複製剩下的專案程式碼 ----
COPY app/ ./app/
COPY alembic.ini .
COPY alembic/ ./alembic/

# ---- 5. 設定容器啟動時要執行的指令 ----
# 用 uvicorn 啟動 FastAPI 應用程式
# --host 0.0.0.0 讓容器內的服務可以被外部存取
# --port 8000 對應前端 JS 寫死的 API 網址
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]