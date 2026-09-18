# ============================================================
# auth.py — 密碼雜湊與 JWT Token 的產生、驗證
# 這個檔案負責三件事：
#   1. get_password_hash() / verify_password()：
#      用 bcrypt 把密碼雜湊後存進資料庫，登入時再比對
#   2. create_access_token()：登入成功後，產生一個 JWT Token 給使用者
#   3. get_current_user()：FastAPI 的依賴函式，
#      檢查請求有沒有帶有效的 Token，沒有就拒絕（回傳 401）
# ============================================================

from datetime import datetime, timedelta, timezone
from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext

# ---- 密碼雜湊設定 ----
# CryptContext 是 passlib 提供的統一介面，這裡指定用 bcrypt 演算法
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---- JWT 設定 ----
# SECRET_KEY 是簽署 Token 的金鑰，正式環境一定要改成環境變數，不能寫死在程式碼
SECRET_KEY = "your-secret-key-change-me-in-production"
# 簽署 Token 使用的演算法
ALGORITHM = "HS256"
# Token 的有效期限（分鐘）
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# HTTPBearer 負責從請求的 Authorization 標頭取出 Token
# auto_error=False 表示找不到 Authorization 時不要自動報錯，
# 讓我們自己決定要回傳什麼錯誤訊息（統一回傳 401）
security = HTTPBearer(auto_error=False)


# ----------------------------------------------------------
# 密碼雜湊工具
# 資料庫永遠不存明文密碼，而是存 bcrypt 雜湊。
# ----------------------------------------------------------
def get_password_hash(password: str) -> str:
    """
    把明文密碼轉成 bcrypt 雜湊字串。
    bcrypt 會自動加鹽（salt），所以同一組密碼每次產生的雜湊都不一樣。
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    拿使用者輸入的明文密碼，去比對資料庫裡的雜湊是否吻合。
    吻合回傳 True，不吻合回傳 False。
    如果雜湊格式不合法（例如並不是 bcrypt 雜湊），
    一律回傳 False，不讓錯誤向外拋出。
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # 任何驗證失敗（格式錯誤、演算法不對等）都視為「密碼錯誤」
        return False


# ----------------------------------------------------------
# 產生 JWT Token
# username: 登入的使用者名稱
# role: 使用者角色（admin＝教務／student＝學生）
#       「預設值給 student」：如果呼叫端沒指定角色，
#       一律當成最沒權限的學生，避免誤發教務權限。
# 回傳：一個 JWT 字串
# ----------------------------------------------------------
def create_access_token(username: str, role: str = "student") -> str:
    """
    把使用者名稱寫進 Token 的 payload，
    並設定過期時間（exp），過期後 Token 就失效。
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": username,  # subject：這顆 Token 屬於誰
        "role": role,  # role：這顆 Token 的使用者是教務還是學生
        "exp": expire,  # 過期時間
    }
    # 用金鑰把 payload 簽署成 JWT 字串
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ----------------------------------------------------------
# 目前登入使用者的資訊
# 由 get_current_user() 從 Token 解出來，再交給 API 使用。
# 這樣 API 才知道呼叫的人是誰、是什麼角色。
# ----------------------------------------------------------
@dataclass
class CurrentUser:
    username: str  # 使用者名稱（Token 的 sub）
    role: str  # 角色：admin（教務）/ student（學生）


# ----------------------------------------------------------
# 驗證 Token 的依賴函式（Dependency）
# 任何需要保護的 API，只要加上 current_user: CurrentUser = Depends(get_current_user)
# FastAPI 就會先執行這個函式：
#   - 沒有帶 Token → 回傳 401
#   - Token 無效或過期 → 回傳 401
#   - Token 有效 → 回傳目前登入的使用者資訊（含角色），繼續執行 API
# ----------------------------------------------------------
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> CurrentUser:
    """
    從 Authorization： Bearer <token> 取出 Token 並驗證。
    驗證失敗一律回傳 401 Unauthorized。
    驗證成功回傳一個 CurrentUser 物件（帳號＋角色）。
    """
    # 檢查有沒有帶 Authorization 標頭
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供認證 Token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # 解碼並驗證 Token（金鑰不對、過期、格式錯誤都會拋例外）
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        # 這裡一定要回傳「包含角色」的使用者資訊，
        # 讓後續的 API 能判斷「學生」還是「教務」。
        # get 表示：萬一 Token 沒有 role（舊 Token），預設當成學生（最沒權限）。
        return CurrentUser(
            username=payload["sub"],  # 使用者名稱
            role=payload.get("role", "student"),  # 角色，沒有的話預設學生
        )
    except jwt.PyJWTError:
        # Token 無效或已過期，回傳 401
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 無效或已過期",
            headers={"WWW-Authenticate": "Bearer"},
        )