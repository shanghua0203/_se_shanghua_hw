# 任務 6：建立 GitHub Actions 自動化測試
## 目標
每次有人上傳程式碼到 GitHub 時，要自動幫忙跑 pytest 測試，確保系統沒被改壞。

## 涉及檔案
- `HW2/.github/workflows/test.yml` (新增)

## 執行步驟
1. 建立 `.github/workflows/test.yml`。
2. 設定觸發條件：當 push 或 pull request 到 `main` 分支時啟動。
3. 設定 Job 步驟：
   - 使用 ubuntu 最新版環境。
   - Checkout 程式碼。
   - 安裝 Python 環境 (例如 3.10 版)。
   - 執行 `pip install -r requirements.txt` 以及安裝 `pytest`。
   - 執行 `pytest HW2/tests/`。

## 驗證標準
- [ ] 產生出的 yaml 檔案語法正確。
- [ ] 步驟有涵蓋環境安裝與執行測試。
