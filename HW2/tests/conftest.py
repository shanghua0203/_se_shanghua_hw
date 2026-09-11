# ============================================================
# conftest.py — pytest 的共用設定檔
# 這裡定義的 fixture（固定裝置）可以被同目錄下的所有測試檔案使用。
# 主要用途：為每個測試建立一個乾淨的、獨立的測試用資料庫。
# ============================================================

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


# ---- Fixture：讓 Playwright 啟動瀏覽器時加上 --no-sandbox ----
# 在某些伺服器/容器環境，Chromium 需要這個參數才能啟動。
# 這個 fixture 會「覆寫」pytest-playwright 提供的 browser_type_launch_args，
# 讓測試用的瀏覽器在啟動時自動帶上 --no-sandbox。
@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    """
    在原本的瀏覽器啟動參數中，加上 --no-sandbox。
    """
    launch_args = dict(browser_type_launch_args)  # 複製原本的參數
    launch_args["args"] = ["--no-sandbox"]  # 加上 --no-sandbox
    return launch_args

from app.models import Base
from app.main import app
from app.routers.enrollment import get_db

# ---- 建立測試用的資料庫引擎 ----
# 使用記憶體中的 SQLite（"sqlite://" 後面沒有路徑），
# 好處是速度超快、每次測試都是全新的、測試結束後自動消失。
#
# 重要：使用 StaticPool 確保所有 Session 共用同一個連線。
# 因為記憶體 SQLite 每個連線會產生獨立的資料庫，
# 如果不共用連線，A Session 寫入的資料 B Session 看不到。
TEST_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite 需要這個參數
    poolclass=StaticPool,  # 確保所有連線共用同一個連線，測試才不會出錯
)

# 建立測試用的 Session 工廠
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


# ---- Fixture：覆寫資料庫 Session ----
# 這個函數會「覆寫」app 中原本的 get_db 依賴，
# 讓測試用的 API 使用測試資料庫，而非正式資料庫。
def override_get_db():
    db = TestSessionLocal()  # 建立測試用的 Session
    try:
        yield db  # 把 Session 交給 API 使用
    finally:
        db.close()  # 最後關閉 Session


# 把覆寫的 Session 注入到 FastAPI app 中
# 這行讓所有 API 端點在測試時都使用測試資料庫
app.dependency_overrides[get_db] = override_get_db


# ---- Fixture：建立測試用的 HTTP Client ----
@pytest.fixture
def client():
    """
    每次執行測試前：
    1. 在測試資料庫中建立所有表格（根據 ORM Model）
    2. 建立一個 TestClient 供測試使用
    3. 測試結束後，移除所有表格（確保下次測試是乾淨的）
    """
    # 在測試開始前，建立所有資料表
    Base.metadata.create_all(bind=test_engine)

    # 建立 FastAPI 的測試客戶端
    with TestClient(app) as c:
        yield c  # 把 client 交給測試函數使用

    # 測試結束後，移除所有資料表（還原乾淨狀態）
    Base.metadata.drop_all(bind=test_engine)
