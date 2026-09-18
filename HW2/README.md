# 校務選課系統（School Course Enrollment System）

這是一個「學生選課」的完整 Full-Stack 練習專案，涵蓋：

- **後端 API**：使用 FastAPI + SQLAlchemy 實作，提供學生選課功能
- **前端網頁**：使用原生 HTML + JavaScript（Fetch API），提供選課操作畫面
- **安全認證**：使用 JWT Token 登入、角色權限驗證（教務／學生），密碼以 bcrypt 雜湊儲存
- **資料庫遷移**：使用 Alembic 管理資料表結構版本
- **容器化**：提供 Dockerfile，不用安裝 Python 也能跑
- **測試**：使用 pytest 撰寫單元測試，並用 Playwright 做系統整合測試（E2E），搭配 GitHub Actions 自動執行

---

## 1. 這個專案在解決什麼問題？

一個看似簡單的「選課」，背後其實有嚴謹的業務邏輯需要把關：

1. 學生是否存在？
2. 課程是否存在？
3. 同一個學生**不能重複選**同一門課？
4. 課程**名額是否已滿**？
5. 呼叫的人**是否已登入**？（帶有效的 JWT Token）
6. 呼叫的人**角色權限是否足夠**？（例如：教務專屬功能只有 `admin` 能用）

全部通過檢查後，這筆選課紀錄才會被寫進資料庫。

---

## 2. 技術架構

| 層級 | 技術 | 用途 |
|------|------|------|
| 前端 | HTML + CSS + JavaScript（Fetch API） | 選課操作畫面 |
| Web 框架 | FastAPI | 提供 RESTful API |
| ORM | SQLAlchemy 2.x | 操作資料庫（不直接寫 SQL） |
| 資料庫 | SQLite | 輕量、免安裝，適合開發與測試 |
| 資料驗證 | Pydantic v2 | 檢查 API 請求／回應格式 |
| 認證 | JWT（pyjwt） | 登入與 Token 權限驗證 |
| 密碼加密 | passlib（bcrypt） | 使用者密碼以雜湊儲存，不存明文 |
| 環境設定 | python-dotenv | 從 `.env` 讀取設定，密碼不外洩 |
| 資料庫遷移 | Alembic | 版本化資料表結構，升級欄位不刪資料 |
| 容器化 | Docker | 打包應用程式，免安裝 Python 直接跑 |
| CI | GitHub Actions | 每次 push 自動跑測試 |
| API 伺服器 | Uvicorn | 啟動 FastAPI 應用程式 |
| 測試 | pytest + pytest-playwright | 單元測試與系統整合測試 |

> 後續若要換成 PostgreSQL / MySQL 等正式資料庫，只需修改 `app/database.py` 的 `DATABASE_URL`，程式碼不用改。

---

## 3. 專案目錄結構

```
HW2/
├── app/                        # 後端主程式
│   ├── __init__.py             # 套件標記
│   ├── main.py                 # FastAPI 主入口（啟動 + /login + 回傳前端頁面）
│   ├── database.py             # 資料庫引擎與 Session 設定
│   ├── models.py               # SQLAlchemy ORM 模型（資料表定義）
│   ├── schemas.py              # Pydantic 資料驗證模型
│   ├── auth.py                 # 密碼雜湊（bcrypt）+ JWT 產生、驗證與角色依賴函式
│   ├── seed.py                 # 建立預設教務帳號 admin/admin（密碼 bcrypt 雜湊）
│   ├── routers/
│   │   ├── __init__.py
│   │   └── enrollment.py       # 選課 API + 教務限定的 GET /enrollments/list
│   └── static/
│       ├── index.html          # 前端選課操作畫面
│       ├── css/style.css       # 前端樣式（已從 HTML 獨立出來）
│       └── js/main.js          # 前端邏輯（登入拿 Token + 呼叫選課 API）
├── alembic/                    # Alembic 遷移腳本
│   ├── env.py                  # 設定（引入 models.Base）
│   └── versions/               # 各版本的遷移腳本
├── alembic.ini                 # Alembic 設定檔（sqlalchemy.url）
├── tests/                      # 測試程式
│   ├── __init__.py
│   ├── conftest.py             # pytest 共用設定（測試資料庫 + Playwright 設定）
│   ├── test_auth.py            # 密碼雜湊（bcrypt）+ User 模型單元測試
│   ├── test_enrollment.py      # 選課 API 單元測試（含登入/401）
│   ├── test_roles.py           # 角色權限（學生/教務）單元測試
│   └── test_system.py          # 系統整合測試（瀏覽器 E2E）
├── requirements.txt            # Python 依賴套件清單
├── pyproject.toml              # pytest 設定
├── .env.example                # 環境變數範例（複製成 .env 使用）
├── Dockerfile                  # 容器化打包設定
├── .dockerignore               # 打包時忽略的檔案
├── .github/workflows/test.yml  # GitHub Actions 自動化測試
└── app.db                      # SQLite 資料庫（啟動程式後自動產生，已被 .gitignore 忽略）
```

---

## 4. 資料庫設計

採用四張資料表，`enrollments` 是連接「學生」與「課程」的中間表（多對多），`users` 記錄登入帳號與角色。

```
students (1) ──────< (N) enrollments (N) >────── (1) courses

users（登入帳號，與選課記錄沒有直接關聯）
```

### students（學生表）
| 欄位 | 型態 | 說明 |
|------|------|------|
| id | INTEGER | **PK**，自動遞增 |
| student_id | VARCHAR(20) | 學號，UNIQUE |
| name | VARCHAR(50) | 姓名 |
| email | VARCHAR(100) | 電子郵件，UNIQUE |
| department | VARCHAR(50) | 科系 |
| enrollment_year | INTEGER | 入學年份 |
| is_active | BOOLEAN | 是否在學（預設 True） |
| created_at / updated_at | DATETIME | 建立／更新時間 |

### courses（課程表）
| 欄位 | 型態 | 說明 |
|------|------|------|
| id | INTEGER | **PK**，自動遞增 |
| course_code | VARCHAR(20) | 課程代碼，UNIQUE |
| name | VARCHAR(100) | 課程名稱 |
| credit | INTEGER | 學分數 |
| max_capacity | INTEGER | 最大容納人數（預設 60） |
| teacher_name | VARCHAR(50) | 授課教師 |
| semester | VARCHAR(20) | 學期 |
| is_active | BOOLEAN | 是否開課（預設 True） |
| created_at / updated_at | DATETIME | 建立／更新時間 |

### enrollments（選課紀錄表）
| 欄位 | 型態 | 說明 |
|------|------|------|
| id | INTEGER | **PK**，自動遞增 |
| student_id | INTEGER | **FK** → students.id |
| course_id | INTEGER | **FK** → courses.id |
| grade | VARCHAR(2) | 成績（可空，尚未評分） |
| status | VARCHAR(20) | enrolled / dropped / completed |
| enrolled_at / updated_at | DATETIME | 選課／更新時間 |

**Unique 約束**：`(student_id, course_id)` — 同一位學生不能重複選同一門課（資料庫層級的最後防線）。

### users（登入使用者表）
| 欄位 | 型態 | 說明 |
|------|------|------|
| id | INTEGER | **PK**，自動遞增 |
| username | VARCHAR(50) | 帳號，UNIQUE |
| password_hash | VARCHAR(128) | 密碼的 bcrypt 雜湊（**不存明文**） |
| role | VARCHAR(10) | 角色：admin（教務）/ student（學生） |
| is_active | BOOLEAN | 帳號是否啟用（預設 True） |
| created_at / updated_at | DATETIME | 建立／更新時間 |

---

## 5. 資料庫遷移（Alembic）

資料表結構由 Alembic 版本管理，以後新增欄位不用刪掉舊資料。

### 常用指令

```bash
# 套用所有遷移（建立/更新資料表到最新版本）
alembic upgrade head

# 修改過 models.py 之後，自動產生新的遷移腳本
alembic revision --autogenerate -m "描述這次的變更"

# 查看目前資料庫在哪個版本
alembic current
```

> 目前有兩個遷移腳本：`alembic/versions/409275526ff3_initial_schema.py`（students / courses / enrollments 三張表）與 `alembic/versions/793f7c001c10_add_users_table.py`（新增 users 表）。

---

## 6. API 說明

### 登入：`POST /login`

**Request Body（JSON）**
```json
{
    "username": "admin",
    "password": "admin"
}
```

**成功（HTTP 200）**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer"
}
```

**失敗（HTTP 401）**：帳號或密碼錯誤

登入邏輯（`app/main.py`）：
1. 先去 `users` 表查這個帳號
2. 帳號**存在** → 用 bcrypt 驗證密碼 → 正確就發 Token，並把使用者的角色寫進 JWT
3. 帳號**不存在** → 保留預設的 `admin / admin` 相容登入（方便未 seed 的環境也能用）

JWT payload 範例（`role` 就是權限判斷的依據）：
```json
{
    "sub": "admin",
    "role": "admin",
    "exp": 1789701439
}
```

預設教務帳號由 `python -m app.seed` 建立（密碼以 bcrypt 雜湊存入，不存明文）：
- **admin / admin**（角色：教務）

### 選課：`POST /enrollments/`（需登入）

呼叫時必須在 `Authorization` 標頭帶上登入拿到的 Token：

```
Authorization: Bearer <access_token>
```

**Request Body（JSON）**
```json
{
    "student_id": 1,
    "course_id": 1
}
```

**成功（HTTP 201）**
```json
{
    "id": 1,
    "student_id": 1,
    "course_id": 1,
    "status": "enrolled",
    "enrolled_at": "2026-09-11T03:35:30"
}
```

**失敗的情境與狀態碼**
| 情境 | HTTP 狀態碼 | 錯誤訊息 |
|------|------------|----------|
| 未帶 Token | 401 | `未提供認證 Token` |
| Token 無效或過期 | 401 | `Token 無效或已過期` |
| 學生不存在 | 404 | `找不到該學生` |
| 課程不存在 | 404 | `找不到該課程` |
| 重複選課 | 409 | `該學生已經選過這門課，不可重複選課` |
| 名額已滿 | 409 | `該課程名額已滿，無法選課` |

### 選課的完整檢查流程（`app/routers/enrollment.py`）

```
收到請求 → 驗證 JWT Token → 檢查學生存在 → 檢查課程存在 → 檢查是否重複 → 檢查是否額滿 → 寫入資料庫
    │            │                │                 │                │              │              │
   POST      驗證 Authorization  查 students 表  查 courses 表  查 enrollments  統計 enrolled    commit
             Bearer Token                      是否有同一位學生    人數是否 >=    （正式寫入）
                                               選同一門課         max_capacity
```

### 查看選課紀錄：`GET /enrollments/list`（教務限定）

只有 **教務（admin）** 角色可以呼叫，回傳所有選課紀錄清單（前端尚未使用，供 API 測試）。

**成功（HTTP 200）**
```json
[
    {
        "id": 1,
        "student_id": 1,
        "course_id": 1,
        "status": "enrolled",
        "enrolled_at": "2026-09-11T03:35:30"
    }
]
```

**失敗的情境與狀態碼**
| 情境 | HTTP 狀態碼 | 錯誤訊息 |
|------|------------|----------|
| 未帶 Token | 401 | `未提供認證 Token` |
| 學生角色 | 403 | `您沒有權限查看選課紀錄` |

> 選課 `POST /enrollments/` 則維持「任何已登入者」皆可用（學生與教務都可以選課）。

---

## 7. 前端說明（`app/static/index.html`）

頁面是純 HTML + JavaScript，CSS 與 JS 已拆到 `css/style.css` 與 `js/main.js`。送出選課時流程如下：

1. 頁面載入時，JS 會自動呼叫 `POST /login`（`admin/admin`）取得 JWT Token
2. 攔截表單的 `submit` 事件（避免頁面重新整理）
3. 用 `parseInt()` 讀取「學生編號」與「課程編號」輸入框的值
4. 用 **Fetch API** 發出 `POST http://127.0.0.1:8000/enrollments/` 請求，並帶上 `Authorization: Bearer <token>` 標頭
5. 依照後端回應：
   - `response.ok` 為 true → 顯示綠色「選課成功」訊息
   - 否則 → 顯示紅色錯誤訊息（讀取 `data.detail`）
   - 連線失敗 → 提示「無法連線到後端伺服器」

> 注意：前端 JavaScript 寫死呼叫 `http://127.0.0.1:8000/enrollments/`，所以**後端必須跑在 8000 埠**。

---

## 8. 環境變數設定（.env）

不要把資料庫連線資訊寫死在程式碼裡。`app/database.py` 會用 `python-dotenv` 讀取 `.env`，讀不到才用預設值。

```bash
# 第一次使用：把範例檔複製成 .env 再依需求修改
cp .env.example .env
```

`.env.example` 內容：

```ini
DATABASE_URL=sqlite:///./test.db
```

> `.env` 已被 `.gitignore` 忽略，不會被上傳到 GitHub，機密資料不會外洩。

---

## 9. 如何安裝與執行

### 9.1 建立虛擬環境並安裝依賴

```bash
# 在專案資料夾（HW2）內建立虛擬環境
python -m venv .venv

# 啟動虛擬環境
source .venv/bin/activate

# 安裝所有依賴（requirements.txt 含後端、測試用套件）
pip install -r requirements.txt

# 下載 Playwright 用的無頭瀏覽器（系統測試才需要，約 110MB）
python -m playwright install chromium
```

### 9.2 建立資料表與預設帳號

```bash
# 套用 Alembic 遷移，建立全部資料表（含 users）
alembic upgrade head

# 建立預設教務帳號 admin / admin（密碼會先用 bcrypt 雜湊再存入）
python -m app.seed

# 若直接跑 seed 卻報「no such table: users」，
# 表示還沒有 users 表，請先執行上面的 alembic upgrade head。
```

> 方式二：直接啟動伺服器，程式會自動 `create_all` 建全部資料表（含 users）。但 seed 前若用 Alembic 管理版本，兩者並不會互相衝突（create_all 只會補建缺少的表）。

### 9.3 啟動後端伺服器

```bash
# 確認已在虛擬環境中
source .venv/bin/activate

# 啟動 API 伺服器（--reload 表示程式碼有改會自動重啟）
uvicorn app.main:app --reload
```

啟動後：

- **前端選課畫面**：瀏覽器開啟 http://127.0.0.1:8000/
- **API 互動文件（Swagger UI）**：開啟 http://127.0.0.1:8000/docs
- **API 健康檢查**：開啟 http://127.0.0.1:8000 （會回傳前端頁面）

---

## 10. 怎麼「真正的選一次課」？

因為目前沒有寫「新增學生／課程」的 API，資料庫的學生與課程需要用 Python 手動塞入。
下面示範如何塞入一筆學生與一門課程（在專案資料夾執行）：

```bash
source .venv/bin/activate
python -c "
from app.database import SessionLocal
from app.models import Student, Course

db = SessionLocal()
db.add(Student(student_id='S111210505', name='王小明',
               email='s111210505@example.com', department='資訊工程學系',
               enrollment_year=2024))
db.add(Course(course_code='CS101', name='程式設計導論',
              credit=3, max_capacity=60, teacher_name='李教授',
              semester='112-2'))
db.commit()
db.close()
print('資料已寫入，學生的 id=1、課程的 id=1')
"
```

接著：

1. 瀏覽器打開 http://127.0.0.1:8000/
2. 學生編號輸入 `1`、課程編號輸入 `1`
3. 點「選課」→ 畫面上會出現綠色「選課成功」訊息（頁面會自動登入並帶 Token）

或者直接用 curl 打 API：

```bash
# 步驟 1：登入拿 Token
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# 步驟 2：帶上 Token 選課
curl -X POST http://127.0.0.1:8000/enrollments/ \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"student_id": 1, "course_id": 1}'
```

---

## 11. 用 Docker 跑（不用裝 Python）

```bash
# 在 HW2 資料夾內 build image
docker build -t course-enrollment .

# 啟動容器，把 8000 埠對應到外面
docker run -p 8000:8000 course-enrollment
```

然後瀏覽器打開 http://127.0.0.1:8000/ 即可。

> `.dockerignore` 會排除 `.env`、`*.db`、虛擬環境等不需要的東西，避免把機密與測試檔案打包進去。

---

## 12. 怎麼跑測試？

### 12.1 只跑單元測試

```bash
source .venv/bin/activate
python -m pytest tests/test_auth.py -v         # 密碼雜湊（bcrypt）+ User 模型
python -m pytest tests/test_enrollment.py -v   # 選課 API（含登入 / 401）
python -m pytest tests/test_roles.py -v        # 角色權限（學生 / 教務）
python -m pytest tests/test_auth.py tests/test_enrollment.py tests/test_roles.py -v   # 全部單元測試
```

涵蓋情境（共 15 個）：

- `test_auth.py`（5 個）：密碼不存明文、正確／錯誤密碼驗證、不合法雜湊不回傳例外、User 模型存雜湊
- `test_enrollment.py`（5 個）：選課成功、重複選課被擋（409）、名額額滿被擋（409）、未登入被擋（401）、登入拿 Token
- `test_roles.py`（5 個）：`/enrollments/list` 未登入 401、學生 403、教務 200；選課 POST 學生／教務皆可用

> 說明：單元測試使用**記憶體資料庫**（`sqlite://` + StaticPool），
> 透過 FastAPI 的 `dependency_overrides` 把資料庫換成測試資料庫，
> 不會碰亂你的 `app.db`。

### 12.2 跑系統整合測試（需先裝 Playwright 瀏覽器）

```bash
source .venv/bin/activate
python -m pytest tests/test_system.py -v -s
```

模擬真實學生操作：

1. 清空並重建資料庫、塞入測試資料
2. 在背景啟動「真的」uvicorn 伺服器（綁定 127.0.0.1:8000）
3. 用無頭 Chromium 打開前端網頁
4. 輸入學生編號與課程編號 → 點「選課」
5. 驗證畫面上出現「選課成功」訊息
6. 再去查 `app.db`，確認 `enrollments` 表真的有這筆紀錄

### 12.3 一次跑全部測試

```bash
source .venv/bin/activate
python -m pytest -v
```

預期結果：**16 passed**（15 個單元測試 + 1 個系統整合測試）。

### 12.4 GitHub Actions 自動測試

`.github/workflows/test.yml` 會在每次 **push 或 pull request 到 `main`** 時自動：

1. 用最新 Ubuntu 環境
2. 安裝 Python 3.10
3. `pip install -r requirements.txt`
4. 安裝 Playwright 瀏覽器
5. 執行 `pytest HW2/tests/`

確保程式碼不會被改壞才合併進 `main`。

---

## 13. 整體架構與資料流

```
┌────────────────────────────┐
│         瀏覽器（前端）         │
│   app/static/index.html     │
│   （HTML + CSS + JS）        │
│   先登入拿「帶角色的 Token」→ 選課       │
└────────────┬───────────────┘
             │ ① POST /login
             │ ② POST /enrollments/  (JSON + Bearer Token)
             │ ③ GET  /enrollments/list（教務限定）
             ▼
┌────────────────────────────┐
│      FastAPI（後端）          │
│   app/auth.py（bcrypt+JWT）  │
│   驗證 Token → 取出角色        │
│   app/routers/enrollment.py │
│   └─ 5 個業務檢查            │
│   ① 已登入   ② 角色權限       │
│   ③ 學生存在 ④ 課程存在        │
│   ⑤ 不重複／未額滿            │
└────────────┬───────────────┘
             │ SQLAlchemy ORM
             ▼
┌────────────────────────────┐
│        SQLite（app.db）      │
│   students / courses /      │
│   enrollments / users       │
│   （由 Alembic 管理結構）     │
└────────────────────────────┘
```

---

## 14. 常見問題（疑難排解）

| 問題 | 解法 |
|------|------|
| 前端顯示「無法連線到後端伺服器」 | 確認 uvicorn 有啟動、且埠號是 8000 |
| 選課一直回傳 401 | 重新整理頁面（讓自動登入再跑一次）或確認 Token 沒過期 |
| 選課一直回傳「找不到該學生／課程」 | 資料庫還是空的，請先餵入學生與課程資料（見第 10 節） |
| `python -m app.seed` 報 `no such table: users` | 還未建表，先執行 `alembic upgrade head` 再 seed |
| `GET /enrollments/list` 回傳 403 | 換成教務（admin）角色的 Token；學生角色沒有權限 |
| `app.db` 被搞亂了 | 直接刪掉 `app.db`，重新執行 `alembic upgrade head` 重建資料表 |
| 系統測試報 `no-sandbox` 相關錯誤 | 已內建 `--no-sandbox` 參數，通常不需要處理 |
| Chromium 沒下載 | 執行 `python -m playwright install chromium` |

---

## 15. 後續可擴充方向（Roadmap）

- 新增「新增學生／課程／查詢課程清單」的 CRUD API
- ~~JWT 登入改用資料庫裡的真實使用者，並加上角色權限（學生／教務）~~ ✅ 已完成
- 增加「退選」「成績輸入」功能
- 部署時資料庫改用 PostgreSQL，連線資訊放入 `.env`