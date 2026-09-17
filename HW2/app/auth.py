# ============================================================
# auth.py — JWT Token 的產生與驗證
# 這個檔案負責兩件事：
#   1. create_access_token()：登入成功後，產生一個 JWT Token 給使用者
#   2. get_current_user()：FastAPI 的依賴函式，
#      檢查請求有沒有帶有效的 Token，沒有就拒絕（回傳 401）
# ============================================================

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

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
# 產生 JWT Token
# username: 登入的使用者名稱
# 回傳：一個 JWT 字串
# ----------------------------------------------------------
def create_access_token(username: str) -> str:
    """
    把使用者名稱寫進 Token 的 payload，
    並設定過期時間（exp），過期後 Token 就失效。
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": username,  # subject：這顆 Token 屬於誰
        "exp": expire,  # 過期時間
    }
    # 用金鑰把 payload 簽署成 JWT 字串
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ----------------------------------------------------------
# 驗證 Token 的依賴函式（Dependency）
# 任何需要保護的 API，只要加上 current_user: str = Depends(get_current_user)
# FastAPI 就會先執行這個函式：
#   - 沒有帶 Token → 回傳 401
#   - Token 無效或過期 → 回傳 401
#   - Token 有效 → 回傳使用者名稱，繼續執行 API
# ----------------------------------------------------------
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    從 Authorization： Bearer <token> 取出 Token 並驗證。
    驗證失敗一律回傳 401 Unauthorized。
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
        return payload["sub"]  # 回傳 Token 中的使用者名稱
    except jwt.PyJWTError:
        # Token 無效或已過期，回傳 401
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 無效或已過期",
            headers={"WWW-Authenticate": "Bearer"},
        )