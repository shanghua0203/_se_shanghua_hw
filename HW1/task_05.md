任務目標：全面提升 mycurl 專案的網路韌性、記憶體效能與終端機體驗。
執行環境規範：
	1.	所有測試與執行必須嚴格在專案根目錄的 .venv 虛擬環境中進行（使用 .venv/bin/python 與 .venv/bin/pytest）。
	2.	嚴禁引入外部 HTTP 請求三方套件（如 requests、httpx），維持使用 Python 內建標準庫（http.client, urllib, ssl, socket）。
	3.	保持既有測試全部相容，不得破壞既有功能。
具體優化需求：
1. 串流下載與記憶體優化（Chunked Streaming）
⚬	修改 mycurl/client.py，下載資料或儲存檔案（-o）時，改採分塊讀取機制（例如每次讀取 8KB），邊收邊寫入檔案或輸出。
⚬	嚴禁將大檔案一次性 read() 載入記憶體，確保處理 500MB 以上檔案時記憶體佔用仍低於 30MB。
2. 逾時控制機制（Timeout Handling）
⚬	在 mycurl/cli.py 新增參數 -m, --max-time（浮點數或整數，單位為秒，預設 30 秒）。
⚬	在底層 Socket 連線與讀取時套用逾時設定，時間一到立即中斷並優雅退出，避免連線永久掛起。
3. 自動轉址追蹤（Follow Redirects）
⚬	新增參數 -L, --location。
⚬	當收到 HTTP 狀態碼 301, 302, 303, 307, 308 且使用者有帶 -L 時：
⚬	自動解析 Response Header 的 Location 欄位。
⚬	支援相對路徑與絕對網址跳轉。
⚬	內建防死循環機制，最多追蹤 10 次轉址，超過次數需中斷並報錯。
⚬	303 狀態碼跳轉需強制改為 GET 請求。
4. 異常處理與標準退出碼（Exit Codes）
⚬	封裝所有底層網路例外（如 socket.gaierror, TimeoutError, ssl.SSLError），在 CLI 最外層統一捕捉。
⚬	發生錯誤時僅在 stderr 印出簡潔的人類可讀訊息（例如：mycurl: (6) Could not resolve host: xyz），嚴禁向使用者噴出 Python Traceback 堆疊訊息。
⚬	規範 System Exit Code：
⚬	0：請求成功
⚬	6：DNS 解析失敗（無法找到主機）
⚬	7：連線伺服器失敗（Connection Refused）
⚬	28：連線或傳輸逾時（Timeout）
⚬	47：超過最大轉址上限（Too many redirects）
測試擴充與自我驗證要求：
	1.	單元測試 (tests/unit/)：
⚬	為逾時設定、轉址次數上限計算、錯誤代碼轉換撰寫 Mock 測試。
	2.	系統端到端測試 (tests/system/)：
⚬	在測試伺服器中新增回傳 302 Redirect 的路由，驗證 -L 參數能順利取得最終頁面內容。
⚬	新增模擬逾時的測試路由，驗證 -m 能如期中斷並回傳 exit code 28。
	3.	自動執行與修復迴圈：
⚬	完成後自動執行 .venv/bin/pytest tests/ -v。
⚬	若有測試未通過，自動定位問題並自我修復，直到測試全數綠燈。
⚬	不准為求通過而修改測試斷言。
