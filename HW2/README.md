# 校務選課系統（School Course Enrollment System）

這是一個「學生選課」的完整 Full-Stack 練習專案，涵蓋：

- **後端 API**：使用 FastAPI + SQLAlchemy 實作，提供學生選課功能
- **前端網頁**：使用原生 HTML + JavaScript（Fetch API），提供選課操作畫面
- **測試**：使用 pytest 撰寫單元測試，並用 Playwright 做系統整合測試（E2E）

---

## 1. 這個專案在解決什麼問題？

一個看似簡單的「選課」，背後其實有嚴謹的業務邏輯需要把關：

1. 學生是否存在？
2. 課程是否存在？
3. 同一個學生**不能重複選**同一門課？
4. 課程**名額是否已滿**？

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
| API 伺服器 | Uvicorn | 啟動 FastAPI 應用程式 |
| 測試 | pytest + pytest-playwright | 單元測試與系統整合測試 |

> 後續若要換成 PostgreSQL / MySQL 等正式資料庫，只需修改 `app/database.py` 的 `DATABASE_URL`，程式碼不用改。

---

## 3. 專案目錄結構

```
HW2/
├── app/                        # 後端主程式
│   ├── __init__.py             # 套件標記
│   ├── main.py                 # FastAPI 主入口（啟動 + 掛載路由 + 回傳前端頁面）
│   ├── database.py             # 資料庫引擎與 Session 設定
│   ├── models.py               # SQLAlchemy ORM 模型（資料表定義）
│   ├── schemas.py              # Pydantic 資料驗證模型
│   ├── routers/
│   │   ├── __init__.py
│   │   └── enrollment.py       # 選課 API（核心業務邏輯）
│   └── static/
│       └── index.html          # 前端選課操作畫面
├── tests/                      # 測試程式
│   ├── __init__.py
│   ├── conftest.py             # pytest 共用設定（測試資料庫 + Playwright 設定）
│   ├── test_enrollment.py      # 選課 API 單元測試
│   └── test_system.py          # 系統整合測試（瀏覽器 E2E）
├── requirements.txt            # Python 依賴套件清單
├── pyproject.toml              # pytest 設定
└── app.db                      # SQLite 資料庫（啟動程式後自動產生，已被 .gitignore 忽略）
```

---

## 4. 資料庫設計

採用三張資料表，`enrollments` 是連接「學生」與「課程」的中間表（多對多）。

```
students (1) ──────< (N) enrollments (N) >────── (1) courses
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

---

## 5. API 說明

### 選課：`POST /enrollments/`

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
| 學生不存在 | 404 | `找不到該學生` |
| 課程不存在 | 404 | `找不到該課程` |
| 重複選課 | 409 | `該學生已經選過這門課，不可重複選課` |
| 名額已滿 | 409 | `該課程名額已滿，無法選課` |

### 選課的完整檢查流程（`app/routers/enrollment.py`）

```
收到請求 → 檢查學生存在 → 檢查課程存在 → 檢查是否重複 → 檢查是否額滿 → 寫入資料庫
    │            │                 │                │              │              │
   POST     查 students 表     查 courses 表     查 enrollments  統計 enrolled      commit
                                            是否有同一位學生    人數是否 >=        （正式寫入）
                                            選同一門課         max_capacity
```

---

## 6. 前端說明（`app/static/index.html`）

頁面是純 HTML + JavaScript，送出選課時流程如下：

1. 攔截表單的 `submit` 事件（避免頁面重新整理）
2. 用 `parseInt()` 讀取「學生編號」與「課程編號」輸入框的值
3. 用 **Fetch API** 發出 `POST http://127.0.0.1:8000/enrollments/` 請求
4. 依照後端回應：
   - `response.ok` 為 true → 顯示綠色「選課成功」訊息
   - 否則 → 顯示紅色錯誤訊息（讀取 `data.detail`）
   - 連線失敗 → 提示「無法連線到後端伺服器」

> 注意：前端 JavaScript 寫死呼叫 `http://127.0.0.1:8000/enrollments/`，所以**後端必須跑在 8000 埠**。

---

## 7. 如何安裝與執行

### 7.1 建立虛擬環境並安裝依賴

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

### 7.2 啟動後端伺服器

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

> 首次啟動時，程式會在 `app/main.py` 執行 `Base.metadata.create_all()`，
> 自動建立 `app.db` 與三張資料表，不需要手動建表。

---

## 8. 怎麼「真正的選一次課」？

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
3. 點「選課」→ 畫面上會出現綠色「選課成功」訊息

或者直接用 curl 打 API：

```bash
curl -X POST http://127.0.0.1:8000/enrollments/ \
     -H "Content-Type: application/json" \
     -d '{"student_id": 1, "course_id": 1}'
```

---

## 9. 怎麼跑測試？

### 9.1 只跑單元測試（3 個）

```bash
source .venv/bin/activate
python -m pytest tests/test_enrollment.py -v
```

涵蓋 3 個情境：**選課成功**、**重複選課被擋（409）**、**名額額滿被擋（409）**。

> 說明：單元測試使用**記憶體資料庫**（`sqlite://` + StaticPool），
> 透過 FastAPI 的 `dependency_overrides` 把資料庫換成測試資料庫，
> 不會碰亂你的 `app.db`。

### 9.2 跑系統整合測試（需先裝 Playwright 瀏覽器）

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

### 9.3 一次跑全部測試

```bash
source .venv/bin/activate
python -m pytest -v
```

預期結果：**4 passed**（3 個單元測試 + 1 個系統測試）。

---

## 10. 整體架構與資料流

```
┌────────────────────────────┐
│         瀏覽器（前端）         │
│   app/static/index.html     │
│   （HTML + JS + Fetch API）  │
└────────────┬───────────────┘
             │ POST /enrollments/  (JSON)
             ▼
┌────────────────────────────┐
│      FastAPI（後端）          │
│   app/routers/enrollment.py │
│   └─ 4 個業務檢查            │
│   ① 學生存在  ② 課程存在      │
│   ③ 不重複    ④ 未額滿        │
└────────────┬───────────────┘
             │ SQLAlchemy ORM
             ▼
┌────────────────────────────┐
│        SQLite（app.db）      │
│   students / courses /      │
│   enrollments               │
└────────────────────────────┘
```

---

## 11. 常見問題（疑難排解）

| 問題 | 解法 |
|------|------|
| 前端顯示「無法連線到後端伺服器」 | 確認 uvicorn 有啟動、且埠號是 8000 |
| 選課一直回傳「找不到該學生／課程」 | 資料庫還是空的，請先餵入學生與課程資料（見第 8 節） |
| `app.db` 被搞亂了 | 直接刪掉 `app.db`，重新啟動 uvicorn 會自動重建空資料表 |
| 系統測試報 `no-sandbox` 相關錯誤 | 已內建 `--no-sandbox` 參數，通常不需要處理 |
| Chromium 沒下載 | 執行 `python -m playwright install chromium` |

---

## 12. 後續可擴充方向（Roadmap）

- 新增「新增學生／課程／查詢課程清單」的 CRUD API
- 使用 **Alembic** 做資料庫版本遷移（目前用 `create_all`，只適合開發）
- 實作 JWT 登入認證與角色權限（學生／教務）
- 增加「退選」「成績輸入」功能
- 部署時資料庫改用 PostgreSQL，並加上 `.env` 設定檔