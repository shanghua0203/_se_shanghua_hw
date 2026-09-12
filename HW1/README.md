# mycurl — 以 Python 標準函式庫打造的迷你 curl

`mycurl` 是一個**不依賴任何第三方套件**（尤其是 `requests`）的 HTTP 指令列用戶端，完全使用
Python 內建的 `http.client` 與 `urllib.parse` 實作。它可以像真正的 `curl` 一樣送出
GET / POST / PUT / DELETE 請求、附加自訂標頭與資料內容、以詳細（Verbose）模式觀察原始標頭、
把回應內容存成檔案，並在無網路的環境下透過模擬（Mock）進行完整測試。

本專案以「階段式任務」逐步建構，共涵蓋四個階段：

| 階段 | 內容 | 對應檔案 |
| --- | --- | --- |
| 一 | 底層核心 HTTP 請求模組 | `mycurl/client.py`、`tests/unit/test_client.py` |
| 二 | CI/CD 風格指令列介面 | `mycurl/cli.py`、`mycurl/__main__.py`、`tests/unit/test_cli.py` |
| 三 | 系統端到端測試（本機臨時伺服器） | `tests/system/test_system.py` |
| 四 | 真實網路相容性驗證腳本 | `verify_live.py` |

---

## 目錄結構

```
HW1/
├── mycurl/
│   ├── __init__.py      # 套件入口，匯出 HttpClient / HttpClientError
│   ├── client.py        # 核心：HttpClient、HttpResponse、HttpClientError
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
# 建立並啟動虛擬環境
python -m venv .venv
source .venv/bin/activate

# 安裝測試所需套件（只有 pytest）
pip install pytest
```

> 所有指令都請在 `.venv` 虛擬環境中執行，確保與本專案的測試環境一致。

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
| `-o, --output` | 將回應內容寫入指定檔案（否則印在終端機） | 無 |
| `-v, --verbose` | 印出詳細的 Request / Response 標頭（輸出至 stderr） | 關閉 |

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

**將回應存成檔案（此模式下終端機不會印出 Body）：**

```bash
python -m mycurl -o output.txt https://httpbin.org/get
cat output.txt
```

**詳細模式（觀察連線過程與原始標頭）：**

```bash
python -m mycurl -v https://httpbin.org/get
```

詳細模式輸出範例（送往 `stderr`，`>` 為請求標頭、`<` 為回應標頭）：

```
* Connecting to httpbin.org via HTTPS
> GET /get HTTP/1.1
> Host: httpbin.org
>
< HTTP/1.1 200 OK
< Date: Sat, 12 Sep 2026 ...
< Content-Type: application/json
<
{ ...JSON 回應... }
```

#### 退出碼（Exit Code）

| 退出碼 | 意義 |
| --- | --- |
| `0` | 成功 |
| `1` | 網路/連線失敗（例如 DNS 解析失敗、連線被拒） |
| `2` | 參數錯誤（例如缺失網址、標頭格式缺少 `:`） |

錯誤一律以 `mycurl: error: ...` 印到 `stderr`，**不會**噴出 Traceback。

### 作為 Python 函式庫使用

除了指令列，也可以直接 import 使用：

```python
from mycurl import HttpClient, HttpClientError

client = HttpClient(verbose=True, timeout=10.0)

try:
    text = client.request(
        "POST",
        "https://httpbin.org/post",
        headers={"X-Custom": "abc"},
        body={"status": "success"},      # dict 會自動序列化成 JSON
        output="result.json",            # 指定後也會寫入檔案
    )
    print(text)
except HttpClientError as exc:
    print("請求失敗:", exc)
```

`HttpClient.request()` 的參數：

- `method`：`GET` / `POST` / `PUT` / `DELETE`（大小寫不拘，會自動轉大寫）
- `url`：支援 `http://` 與 `https://`
- `headers`：dict 形式的自訂標頭
- `body`：字串、bytes、或 dict/list（後兩者會自動 `json.dumps`；未指定 Content-Type 時會自動填入）：
  - 字串 body → `application/x-www-form-urlencoded`
  - dict/list/bytes body → `application/json`
- `output`：指定路徑時，回應內容會一併寫入檔案
- 回傳值：回應 Body 字串

---

## 測試

### 單元測試（Unit Tests）— 不打真實網路

所有網路 Socket 皆以 `unittest.mock` 模擬 `http.client.HTTPConnection` /
`HTTPSConnection`，即使完全離線也能瞬間跑完：

```bash
.venv/bin/python -m pytest tests/unit -v
```

涵蓋項目：

- 正常 GET 請求（方法、路徑、Port、Timeout 皆被正確呼叫）
- 帶 Header / Body 的 POST（含 `-d` 自動推斷 POST、`-X` 優先覆寫）
- PUT / DELETE 等其它方法
- dict Body 自動轉 JSON
- 連線失敗時拋出 `HttpClientError`
- 回應寫檔、Verbose 標頭輸出
- CLI 參數解析型態、無效參數退出碼

### 系統測試（System Tests）— 本機真實收發

以 Python 內建的 `http.server.ThreadingHTTPServer` + `threading` 在隨機埠啟動臨時伺服器，
再用 `subprocess.run` 呼叫 `.venv/bin/python -m mycurl`，驗證「終端機輸出」與「寫出的檔案」：

```bash
.venv/bin/python -m pytest tests/system -v
```

涵蓋案例：

1. 基本 GET：終端機輸出符合伺服器回應
2. POST `-d "name=test"`：伺服器確實收到 Payload（含 Content-Type）
3. `-o output.txt`：檔案確實產生且內容無誤、stdout 不輸出
4. `-v`：stderr 含 `>` 與 `<` 開頭的標頭

### 完整測試套件

```bash
.venv/bin/python -m pytest tests/
```

### 真實網路驗證（Task 04）

`verify_live.py` 以 subprocess 實際連接 httpbin.org 驗證與真實網路的相容性：

```bash
.venv/bin/python verify_live.py
```

三項測試皆為 PASS 時，會輸出各項的 Exit Code 與耗時：

| 測試 | 預期結果 |
| --- | --- |
| `GET https://httpbin.org/get` | Exit 0，stdout 為合法 JSON |
| `-X POST -d "status=success" .../post` | Exit 0，伺服器回應 `form.status == success` |
| 隨機不存在的網址（`.invalid`） | Exit 1，stderr 優雅報錯、無 Traceback |

---

## 設計要點與限制

- **零依賴**：執行期只用標準函式庫的 `http.client`、`urllib.parse`、`argparse`、`json`。
- **錯誤處理**：`OSError`（連線被拒、DNS 失敗等）一律包裝成 `HttpClientError`，
  由 CLI 統一轉成 exit code 1；參數錯誤為 exit code 2。
- **Verbose 不走 stdout**：詳細標頭送 `stderr`，確保 stdout 永遠只有回應 Body，
  方便管線處理（例如 `python -m mycurl ... | jq`）。
- **限制**：尚不支援分塊上傳、大型串流回應、Cookie 管理、代理伺服器與
  自訂 TLS 憑證驗證等進階功能，設計目標是「簡潔、可測試、模仿 curl 的基本行為」。