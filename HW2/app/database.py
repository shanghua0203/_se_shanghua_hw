# ============================================================
# database.py — 資料庫連線與 Session 設定
# 這個檔案負責建立資料庫引擎（engine）以及 Session 工廠。
# Session 是 SQLAlchemy 操作資料庫的主要介面。
# ============================================================

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()

# 使用 SQLite 作為資料庫（輕量、免安裝、適合開發與測試）
# 「check_same_thread=False」是 SQLite + FastAPI 的必要參數，
# 因為 FastAPI 使用非同步，SQLite 預設不允許跨執行緒共用連線。
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# SessionLocal 是一個「Session 工廠」
# 每次呼叫 SessionLocal() 就會產生一個新的資料庫 Session
# 用來執行查詢、新增、修改、刪除等操作
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
