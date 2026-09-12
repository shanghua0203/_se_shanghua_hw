階段一：初始化與核心請求模組（底層連線）
複製給 OpenCode 的指令：
請在當前專案建立核心 HTTP 請求模組 mycurl/client.py，要求如下：
	1.	請確認所有操作都在專案根目錄的 .venv 虛擬環境中進行。
	2.	使用 Python 內建的 http.client 與 urllib.parse 實作一個 HttpClient 類別，不依賴外部三方 requests 套件。
	3.	支援功能：
⚬	指定 HTTP 方法（GET, POST, PUT, DELETE）。
⚬	傳送自訂標頭（Headers）與資料內容（Body）。
⚬	詳細輸出模式（Verbose 模式，印出連線過程與原始標頭）。
⚬	將回應內容存為檔案或回傳字串。
	4.	請同時在 tests/unit/test_client.py 撰寫單元測試：
⚬	使用 unittest.mock 模擬 http.client.HTTPConnection，不要發出真實網路請求。
⚬	測試項目需包含：正常 GET 請求、帶 Header/Body 的 POST 請求、連線失敗時的錯誤拋出。
	5.	實作完成後，請自動在 .venv 環境執行 pytest tests/unit 驗證全數通過。
