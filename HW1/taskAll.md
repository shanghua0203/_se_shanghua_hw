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
階段二：CLI 指令列介面實作（包裝參數）
複製給 OpenCode 的指令：
請實作指令列入口 mycurl/cli.py 與 mycurl/__main__.py，串接剛才完成的 client.py：
	1.	使用 argparse 實作仿 curl 的指令參數：
⚬	url：目標網址（必填）。
⚬	-X, --request：HTTP 方法（預設 GET）。
⚬	-H, --header：自訂標頭，支援重複帶入多個（例如 -H "A: 1" -H "B: 2"）。
⚬	-d, --data：HTTP POST 送出的資料內容。
⚬	-o, --output：將回傳內容寫入指定檔案路徑，未指定時預設印在終端機。
⚬	-v, --verbose：印出詳細的 Request / Response Headers。
	2.	請在 tests/unit/test_cli.py 撰寫參數解析的單元測試：
⚬	驗證各項參數是否能正確被解析為字典與正確型態。
⚬	測試無效參數時的離開代碼（Exit Code）。
	3.	請在 .venv 下執行 pytest tests/unit，確保單元測試全部綠燈。
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
