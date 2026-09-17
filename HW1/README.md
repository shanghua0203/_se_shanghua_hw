# mycurl — 以 Python 標準函式庫打造的迷你 curl

`mycurl` 是一個**不依賴任何第三方套件**（尤其是 `requests`）的 HTTP 指令列用戶端，完全使用
Python 內建的 `http.client` 與 `urllib.parse` 實作。它可以像真正的 `curl` 一樣送出
GET / POST / PUT / DELETE 請求、附加自訂標頭與資料內容、以詳細（Verbose）模式觀察原始標頭、
把回應內容存成檔案，並支援**轉址追蹤、逾時控制與串流下載**。

本專案以「階段式任務」逐步建構，共涵蓋五個階段：

| 階段 | 內容 | 對應檔案 |
| --- | --- | --- |
| 一 | 底層核心 HTTP 請求模組 | `mycurl/client.py`、`tests/unit/test_client.py` |
| 二 | 指令列介面 | `mycurl/cli.py`、`mycurl/__main__.py`、`tests/unit/test_cli.py` |
| 三 | 系統端到端測試（本機臨時伺服器） | `tests/system/test_system.py` |
| 四 | 真實網路相容性驗證腳本 | `verify_live.py` |
| 五 | 網路韌性強化：串流、逾時、轉址、退出碼 | `mycurl/client.py`、`mycurl/cli.py` 及對應測試 |

---

## 目錄結構

```
HW1/
├── mycurl/
│   ├── __init__.py      # 套件入口，匯出 HttpClient 與各類錯誤
│   ├── client.py        # 核心：HttpClient、分塊串流、轉址、逾時與例外層級
│   ├── cli.py           # argparse 指令列解析與 main() 流程
│   └── __main__.py      # 讓 `python -m mycurl` 可以直接執行
├── tests/
│   ├── unit/
│   │   ├── test_client.py   # 單元測試（全程 Mock，不打真實網路）
│   │   └── test_cli.py      # 指令參數解析測試（含退出碼）
│   └── system/
│       └── test_system.py   # E2E：本機 http.server + subprocess 真實收發
├── verify_live.py       # 真實網路（httpbin.org）相容性驗證腳本
├── pyproject.toml       # pytest 設定（testpaths / pythonpath）
└── task_*.md            # 各階段任務說明
```

---

## 環境需求與安裝

- Python 3.12+（無任何第三方執行期依賴，pytest 僅用於開發測試）
- 建議在虛擬環境中操作：

```bash
python -m venv .venv
source .venv/bin/activate

pip install pytest   # 只有測試需要
```

---

## 使用方法

### 指令列（CLI）

透過 `python -m mycurl` 執行：

```bash
python -m mycurl <url> [選項]
```

#### 常用選項一覽

| 選項 | 說明 | 預設 |
| --- | --- | --- |
| `url` | 目標網址（必要） | 無 |
| `-X, --request` | HTTP 方法：GET / POST / PUT / DELETE | `GET` |
| `-H, --header` | 自訂標頭，格式 `"Name: value"`，**可重複**使用 | 無 |
| `-d, --data` | 請求資料內容；未指定 `-X` 時自動改用 POST | 無 |
| `-o, --output` | 將回應內容以**串流**寫入指定檔案（否則印在終端機） | 無 |
| `-v, --verbose` | 印出詳細的 Request / Response 標頭（輸出至 stderr） | 關閉 |
| `-m, --max-time` | 整個傳輸允許的最大秒數（整數或浮點數） | `30` |
| `-L, --location` | 自動追蹤轉址（301 / 302 / 303 / 307 / 308） | 關閉 |

#### 範例

**基本 GET：**

```bash
python -m mycurl https://httpbin.org/get
```

**指定方法並帶自訂標頭：**

```bash
python -m mycurl -X PUT -H "Authorization: Bearer xyz" -H "Accept: application/json" \
    https://httpbin.org/anything
```

**送出 POST 資料（`-d` 會自動把方法改為 POST，與 curl 行為一致）：**

```bash
python -m mycurl -d "name=test" https://httpbin.org/post
```

**將回應存成檔案（以 8KB 分塊邊收邊寫，不會把整份檔案載入記憶體；`-o` 時終端機不印 Body）：**

```bash
python -m mycurl -o output.txt https://httpbin.org/get
```

**追蹤轉址（看 ``302 → /final`` 的最終頁面）：**

```bash
python -m mycurl -L https://httpbin.org/redirect-to?url=/anything
```

**限制整個請求的最長秒數，超時以代碼 28 結束：**

```bash
python -m mycurl -m 5 https://httpbin.org/delay/60
echo $?   # => 28
```

**詳細模式（觀察連線過程、轉址與原始標頭）：**

```bash
python -m mycurl -Lv https://httpbin.org/redirect-to?url=/anything
```

詳細模式輸出範例（送往 `stderr`，`>` 為請求標頭、`<` 為回應標頭、`*` 為流程說明）：

```
* Connecting to httpbin.org via HTTPS
> GET /redirect-to?url=/anything HTTP/1.1
> Host: httpbin.org
>
< HTTP/1.1 302 FOUND
< Location: /anything
<
* Redirect #1 -> https://httpbin.org/anything
> GET /anything HTTP/1.1
> Host: httpbin.org
>
< HTTP/1.1 200 OK
< Content-Type: application/json
<
{ ...JSON 回應... }
```

#### 退出碼（Exit Code）

| 退出碼 | 意義 |
| --- | --- |
| `0` | 請求成功 |
| `2` | 參數錯誤（例如缺失網址、標頭格式缺少 `:`） |
| `3` | 網址格式無效或不支援的 scheme |
| `6` | DNS 解析失敗（無法找到主機） |
| `7` | 連線伺服器失敗（例如 Connection Refused） |
| `28` | 連線或傳輸逾時（超過 `-m`） |
| `47` | 超過最大轉址上限（10 次） |
| `60` | TLS/SSL 錯誤 |

錯誤一律以 `mycurl: (代碼) 訊息` 印到 `stderr`，**不會**噴出 Python Traceback。例如：

```
mycurl: (6) could not resolve host: no-such-host.example
mycurl: (28) operation timed out after 5.0 seconds
mycurl: (47) maximum (10) redirects followed
```

### 作為 Python 函式庫使用

```python
from mycurl import HttpClient, HttpClientError

client = HttpClient(verbose=False, timeout=10.0)

try:
    text = client.request(
        "POST",
        "https://httpbin.org/post",
        headers={"X-Custom": "abc"},
        body={"status": "success"},       # dict 會自動序列化成 JSON
        follow_redirects=True,
    )
    print(text)
except HttpClientError as exc:
    print("請求失敗 (exit", exc.exit_code, "):", exc)
```

`HttpClient.request()` 的參數：

- `method`：`GET` / `POST` / `PUT` / `DELETE`（會自動轉大寫）
- `url`：支援 `http://` 與 `https://`（也作為轉址時的基準網址）
- `headers`：dict 形式的自訂標頭
- `body`：字串、bytes、或 dict/list（後兩者自動 `json.dumps`；未指定 Content-Type 會自動填入）
- `output`：指定路徑時以 8KB 分塊串流寫入檔案，此時回傳 `None`
- `follow_redirects`：開啟後追蹤 301/302/303/307/308（303 強制改為 GET），上限 10 次
- 回傳值：回應 Body 字串（`output` 未指定時）

---

## 網路韌性設計重點

- **串流下載（Chunked Streaming）**：回應一律以 `CHUNK_SIZE = 8KB` 分塊讀取；
  `-o` 時邊收邊寫入檔案，不呼叫一次性 `resp.read()`。實測下載 600MB 檔案峰值記憶體約 **20MB**。
- **逾時控制（`-m`）**：Socket 連線與讀取皆套用逾時；同時以 monotonic deadline 控制整體預算
  （含多次轉址的累計時間），時間到立即以代碼 28 優雅退出。
- **自動轉址（`-L`）**：支援相對路徑與絕對網址（`urljoin`），`303` 強制改用 GET；
  上限 10 次，超出回傳代碼 47。
- **例外分層**：`socket.gaierror → DnsError(6)`、`ConnectionRefusedError/OSError → ConnectionFailedError(7)`、
  `TimeoutError → RequestTimeoutError(28)`、`ssl.SSLError → SslError(60)`、超過轉址 → `TooManyRedirectsError(47)`。
  全部繼承 `HttpClientError`，由 CLI 最外層統一轉成 `mycurl: (N) message` 並對應退出碼。

---

## 測試

### 單元測試（Unit Tests）— 不打真實網路

所有網路 Socket 皆以 `unittest.mock` 模擬 `http.client.HTTPConnection` /
`HTTPSConnection`，即使完全離線也能瞬間跑完：

```bash
.venv/bin/python -m pytest tests/unit -v
```

涵蓋項目（含 Task 05 新增）：

- 正常 GET / POST（Header / Body）/ PUT / DELETE
- `-d` 自動推斷 POST、`-X` 優先覆寫
- dict Body 自動轉 JSON
- 回應以 8KB 分塊讀取、回應寫檔（回傳 `None`）
- 連線失敗拋出 `HttpClientError`
- 逾時設定傳入連線、逾時錯誤 → exit code 28
- DNS 失敗 → 6、Connection Refused → 7、SSL 錯誤 → 60
- 轉址追蹤（含 `303` → GET）、超過 10 次 → 47、未帶 `-L` 不追蹤
- CLI 參數解析型態、無效參數退出碼、`-m` / `-L` 傳遞

### 系統測試（System Tests）— 本機真實收發

以 `http.server.ThreadingHTTPServer` + `threading` 在隨機埠啟動臨時伺服器，再用
`subprocess.run` 呼叫 `.venv/bin/python -m mycurl`：

```bash
.venv/bin/python -m pytest tests/system -v
```

涵蓋案例：

1. 基本 GET：終端機輸出符合伺服器回應
2. POST `-d "name=test"`：伺服器確實收到 Payload（含 Content-Type）
3. `-o output.txt`：串流寫檔、內容無誤、stdout 不輸出
4. `-v`：stderr 含 `>` 與 `<` 開頭的標頭
5. `-L` 追蹤 `302 → /final` 取得最終頁面
6. 未帶 `-L` 只送出一次請求
7. `/slow` 路由（伺服器延遲回應）：`-m 1` 如期中斷，退出碼 28
8. `/loop` 轉址迴圈：`-L` 後退出碼 47

### 完整測試套件

```bash
.venv/bin/python -m pytest tests/
```

### 真實網路驗證

`verify_live.py` 以 subprocess 實際連接 httpbin.org：

```bash
.venv/bin/python verify_live.py
```

驗證 GET 拿 JSON、POST 送 `status=success`、以及不存在網址的優雅報錯與退出碼。

---

## 設計限制

- 尚不支援分塊上傳、大型串流上傳、Cookie 管理、代理伺服器與自訂 TLS 憑證驗證。
- 追蹤轉址與 TLS 錯誤使用與 curl 相容的退出碼（47、60），但訊息文字為自有格式。