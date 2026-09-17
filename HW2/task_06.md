# 任務 1：引入環境變數機制 (dotenv)
## 目標
不要把資料庫密碼或重要設定直接寫在程式碼裡，請幫我改成用 `.env` 檔案來讀取。請用最簡單的方式實作。

## 涉及檔案
- `HW2/app/database.py`
- `HW2/requirements.txt`
- `HW2/.gitignore`

## 執行步驟
1. 在 `requirements.txt` 裡面新增 `python-dotenv`。
2. 建立一個範例檔案 `HW2/.env.example`，裡面寫上 `DATABASE_URL=sqlite:///./test.db`。
3. 修改 `HW2/.gitignore`，確保 `.env` 不會被上傳到 GitHub。
4. 修改 `HW2/app/database.py`，使用 `os.getenv` 或 `dotenv` 來讀取 `DATABASE_URL`，如果讀不到才使用預設的 `sqlite:///./test.db`。

## 驗證標準
- [ ] 執行程式碼時，系統能正常連線到資料庫。
- [ ] `.env` 檔案被 Git 忽略。
