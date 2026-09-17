# ============================================================
# main.py — FastAPI 應用程式主入口
# 這個檔案負責建立 FastAPI 實例、註冊路由、設定資料庫。
# 執行這個檔案就能啟動整個 API 伺服器。
# ============================================================

from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel

from .auth import create_access_token
from .database import engine
from .models import Base
from .routers import enrollment

# 建立 FastAPI 實例，設定專案的基本資訊
app = FastAPI(
    title="校務選課系統 API",
    description="提供學生選課功能的後端 API",
    version="0.1.0",
)

# 啟動時自動建立資料庫表格
# 如果表格已存在，則不會做任何事情（不會刪除舊資料）
Base.metadata.create_all(bind=engine)

# 註冊路由（Router）
# 把 enrollment 模組中定義的 API 路由掛載到主 app 上
app.include_router(enrollment.router)


# ----------------------------------------------------------
# 登入用的 Pydantic Schema
# ----------------------------------------------------------
class LoginRequest(BaseModel):
    """登入請求：只需要帳號與密碼。"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """登入成功後回傳 Token。"""
    access_token: str  # JWT Token
    token_type: str  # 固定為 "bearer"


# ----------------------------------------------------------
# POST /login — 登入並取得 Token
# 為了簡單示範，目前只接受一組固定帳號密碼：admin / admin。
# ----------------------------------------------------------
@app.post("/login", response_model=TokenResponse)
def login(request: LoginRequest):
    """
    驗證帳號密碼，正確就發給一顆 JWT Token。
    之後呼叫需要認證的 API（例如選課），
    在 Authorization 標頭帶上「Bearer <token>」即可。
    """
    # 帳號密碼都正確 → 發 Token
    if request.username == "admin" and request.password == "admin":
        return TokenResponse(
            access_token=create_access_token(request.username),
            token_type="bearer",
        )

    # 帳號或密碼錯誤 → 拒絕登入
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="帳號或密碼錯誤",
    )


# ---- 讀取前端 HTML 檔案的內容 ----
# 取得 static/index.html 的完整路徑
STATIC_DIR = Path(__file__).parent / "static"
HTML_FILE = STATIC_DIR / "index.html"

# 掛載靜態資料夾，讓瀏覽器能載入 css/style.css 與 js/main.js
app.mount("/css", StaticFiles(directory=STATIC_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=STATIC_DIR / "js"), name="js")

# 讀取 HTML 檔案的內容（啟動時讀取一次即可）
html_content = HTML_FILE.read_text(encoding="utf-8")


# 根路由 — 直接回傳前端選課頁面
@app.get("/", response_class=HTMLResponse)
def read_root():
    """
    根路由，回傳前端選課操作畫面。
    在瀏覽器中打開 http://127.0.0.1:8000/ 就能看到選課頁面。
    """
    return html_content
