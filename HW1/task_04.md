請為我撰寫並執行一段驗證腳本，測試當前專案與真實網路的相容性：
	1.	請在 .venv 環境中，使用 subprocess 實際呼叫我們的 mycurl 指令：
⚬	測試一：python -m mycurl [https://httpbin.org/get](https://httpbin.org/get)（確認能拿到 JSON 回應）。
⚬	測試二：python -m mycurl -X POST -d "status=success" [https://httpbin.org/post](https://httpbin.org/post)（確認伺服器有收到資料）。
⚬	測試三：輸入一個隨機不存在的網址（確認程式會優雅印出錯誤，而不是整隻崩潰噴 Traceback）。
	2.	自動執行上述測試，並將各項測試的執行結果、耗時與 Exit Code 排版回報給我。
	3.	若有任何異常，請直接針對 mycurl/client.py 進行修正。
