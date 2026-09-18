# ============================================================
# seed.py — 建立預設教務帳號
# 這是開發用的簡易資料填充腳本：
#   執行 `python -m app.seed` 會建立一個預設「教務」帳號
#   username: admin
#   password: admin
# 密碼一律以 bcrypt 雜湊存入資料庫，不存明文。
# 若帳號已存在則略過（不覆寫），可重複執行。
# ============================================================

from .auth import get_password_hash
from .database import SessionLocal
from .models import User

# 預設教務帳號與密碼（與原本示範的登入資訊一致）
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin"


def seed_admin_user() -> None:
    """
    建立一個預設的教務（admin）使用者。
    若同名帳號已存在就不重複建立，直接略過。
    """
    db = SessionLocal()
    try:
        existing = (
            db.query(User).filter(User.username == DEFAULT_ADMIN_USERNAME).first()
        )
        if existing is not None:
            print(
                f"預設帳號「{DEFAULT_ADMIN_USERNAME}」已存在，跳過建立（登入密碼不變，避免覆寫）。"
            )
            return

        # 建立教務帳號：密碼經過 bcrypt 雜湊後再存資料庫
        admin_user = User(
            username=DEFAULT_ADMIN_USERNAME,
            password_hash=get_password_hash(DEFAULT_ADMIN_PASSWORD),
            role="admin",
        )
        db.add(admin_user)
        db.commit()
        print(
            f"已建立預設教務帳號：{DEFAULT_ADMIN_USERNAME} / {DEFAULT_ADMIN_PASSWORD}"
        )
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin_user()