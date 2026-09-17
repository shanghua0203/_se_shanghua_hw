# 任務 4：新增簡易的 JWT 登入與權限驗證
## 目標
選課系統不能讓路人隨便呼叫 API，需要加入 JWT Token 驗證機制。只要實作最基礎的登入和保護路由即可。

## 涉及檔案
- `HW2/app/main.py`
- `HW2/app/routers/enrollment.py`
- `HW2/requirements.txt`

## 執行步驟
1. 在 `requirements.txt` 新增 `pyjwt` 和 `passlib`。
2. 在 `app` 裡面新增一個 `auth.py`，實作產生 JWT Token 的功能以及驗證 Token 的依賴函式 (Dependency)。
3. 在 `main.py` 新增一個 `/login` 的 API，只要隨便輸入一組帳號密碼(例如 admin/admin) 就發給他一個 Token。
4. 修改 `routers/enrollment.py` 裡面的選課 API，加上 Depends 確保只有帶著 Token 的人可以呼叫。

## 驗證標準
- [ ] 不帶 Token 呼叫選課 API 會被拒絕 (回傳 401)。
- [ ] 成功登入拿到 Token 後，可以正常選課。
