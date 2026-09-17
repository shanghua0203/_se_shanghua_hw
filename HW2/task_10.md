# 任務 5：將應用程式容器化 (Dockerfile)
## 目標
請幫我寫一個 Dockerfile，把這個 FastAPI 專案打包起來，讓別人不用裝 Python 也能跑。

## 涉及檔案
- `HW2/Dockerfile` (新增)
- `HW2/.dockerignore` (新增)

## 執行步驟
1. 建立 `.dockerignore`，忽略 `.git`, `__pycache__`, `.env`, `venv` 等不需要打包進去的東西。
2. 撰寫 `Dockerfile`：
   - 使用輕量級的 Python 基礎映像檔 (如 `python:3.10-slim`)。
   - 設定工作目錄。
   - 複製 `requirements.txt` 並執行 `pip install`。
   - 複製剩下的程式碼。
   - 設定啟動指令 (CMD) 來執行 uvicorn。

## 驗證標準
- [ ] 能夠成功 build 出 image。
- [ ] 執行 container 後，能在瀏覽器連上系統畫面。
