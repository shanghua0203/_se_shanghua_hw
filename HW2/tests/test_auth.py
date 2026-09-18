# ============================================================
# test_auth.py — 密碼雜湊（bcrypt）功能的單元測試
# 驗證重點：
#   1. 密碼不會以明文形式存在
#   2. 正確密碼可以驗證成功、錯誤密碼驗證失敗
#   3. 使用者帳號以「密碼雜湊」寫入資料庫
# ============================================================

import pytest

from app.auth import get_password_hash, verify_password
from app.models import Base, User
from tests.conftest import TestSessionLocal, test_engine


# ----------------------------------------------------------
# Fixture：準備一個乾淨的測試資料庫
# 建立所有資料表（含 users 表），測試結束後刪除還原。
# ----------------------------------------------------------
@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=test_engine)  # 建立所有資料表
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()
    Base.metadata.drop_all(bind=test_engine)  # 清空，還原乾淨狀態


# ----------------------------------------------------------
# 測試 1：雜湊結果不是明文，且每次都不同
# ----------------------------------------------------------
def test_password_hash_is_not_plaintext():
    plain = "my-secret-password"
    hashed = get_password_hash(plain)

    # 雜湊字串不應該包含明文，也不能等於明文本身
    assert plain not in hashed
    assert hashed != plain

    # bcrypt 會自動加鹽，因此同一組密碼每次 hash 結果都不同
    assert hashed != get_password_hash(plain)


# ----------------------------------------------------------
# 測試 2：正確密碼可以驗證成功
# ----------------------------------------------------------
def test_verify_password_correct():
    plain = "my-secret-password"
    hashed = get_password_hash(plain)
    assert verify_password(plain, hashed) is True


# ----------------------------------------------------------
# 測試 3：錯誤密碼驗證失敗
# ----------------------------------------------------------
def test_verify_password_wrong():
    plain = "my-secret-password"
    hashed = get_password_hash(plain)
    assert verify_password("wrong-password", hashed) is False


# ----------------------------------------------------------
# 測試 4：不合法的雜湊字串驗證失敗，不會拋例外
# ----------------------------------------------------------
def test_verify_password_invalid_hash():
    assert verify_password("any", "not-a-bcrypt-hash") is False


# ----------------------------------------------------------
# 測試 5：User 模型把密碼以「雜湊」存入資料庫（不存明文）
# ----------------------------------------------------------
def test_user_model_stores_hashed_password(db_session):
    plain = "admin-password"
    user = User(
        username="admin",
        password_hash=get_password_hash(plain),
        role="admin",
    )
    db_session.add(user)
    db_session.commit()

    # 重新從資料庫讀取剛剛存進去的那位使用者
    saved = db_session.query(User).filter(User.username == "admin").first()
    assert saved is not None  # 有成功寫入

    # 資料庫裡存的是雜湊，不是明文
    assert saved.password_hash != plain
    assert plain not in saved.password_hash

    # 用 bcrypt 驗證：正確密碼通過、錯誤密碼不過
    assert verify_password(plain, saved.password_hash) is True
    assert verify_password("wrong-password", saved.password_hash) is False