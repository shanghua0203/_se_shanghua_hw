階段三：系統整合與端到端測試（真實情境測試）
複製給 OpenCode 的指令：
現在我們要進行系統端到端測試（System E2E Tests），以確認程式像真正的 curl 一樣運作：
	1.	在 tests/system/test_system.py 中，使用 Python 內建的 http.server 與 threading 在本機啟動一個臨時的測試 HTTP 伺服器。
	2.	透過 subprocess.run 執行虛擬環境中的指令（例如 .venv/bin/python -m mycurl [http://127.0.0.1](http://127.0.0.1):port/...）。
	3.	系統測試案例必須涵蓋：
⚬	Case 1 (基本 GET)：發送請求並驗證終端機輸出內容符合預期。
⚬	Case 2 (POST 傳值)：帶入 -d "name=test"，驗證本地伺服器正確收到 Payload。
⚬	Case 3 (檔案儲存)：帶入 -o output.txt，驗證本機確實產生檔案且內容無誤。
⚬	Case 4 (Verbose 模式)：帶入 -v，驗證 stderr 有印出 > 與 < 開頭的標頭資訊。
	4.	請執行完整測試套件 pytest tests/，確認所有單元測試與系統測試皆順利通過。
測試驗證對照重點
⚬	單元測試（Unit Test）：只測邏輯，不連網、不開伺服器。所有網路 Socket 通通給假資料（Mock），確保程式在沒有網路的環境下也能瞬間跑完。
⚬	系統測試（System Test）：由程式在背景自動拉起一個微型伺服器，模擬真實使用者敲指令敲進去，檢查「輸出的文字」與「儲存的檔案」是否百分之百正確。
