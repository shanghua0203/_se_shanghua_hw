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
