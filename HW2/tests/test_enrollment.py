# ============================================================
# test_enrollment.py — 選課功能的單元測試
# 測試四種情境：
#   1. 選課成功
#   2. 重複選課被擋
#   3. 名額額滿被擋
#   4. 不帶 Token 呼叫選課 API 會被拒絕（401）
# ============================================================

from app.auth import create_access_token
from app.models import Course, Student
from tests.conftest import TestSessionLocal


# 取得一個有效的測試用 Token
TEST_TOKEN = create_access_token("admin")

# 所有選課 API 請求都需要帶上的 Authorization header
AUTH_HEADER = {"Authorization": f"Bearer {TEST_TOKEN}"}


# ----------------------------------------------------------
# 輔助函數：在測試資料庫中預先建立「學生」和「課程」資料
# 由於每次測試的資料庫都是全新的（由 conftest.py 處理），
# 所以需要在每個測試前手動建立測試用的資料。
# ----------------------------------------------------------
def create_test_data(db_session):
    """
    在資料庫中建立一筆測試用的學生和一門測試用的課程。
    回傳 (student, course) 供後續測試使用。
    """
    # 建立一個測試用的學生
    student = Student(
        student_id="S111210505",  # 學號
        name="王小明",  # 姓名
        email="test@example.com",  # 電子郵件
        department="資訊工程學系",  # 科系
        enrollment_year=2024,  # 入學年份
    )
    db_session.add(student)  # 加入 Session

    # 建立一個測試用的課程（最大人數設定為 1，方便測試額滿的情境）
    course = Course(
        course_code="CS101",  # 課程代碼
        name="程式設計導論",  # 課程名稱
        credit=3,  # 學分數
        max_capacity=1,  # 最大容納人數設為 1（方便測試額滿）
        teacher_name="李教授",  # 授課教師
        semester="112-2",  # 學期
    )
    db_session.add(course)  # 加入 Session

    db_session.commit()  # 寫入資料庫，取得 auto-generated 的 id

    # 用 refresh 從資料庫重新讀取，確保 id 等欄位是最新的
    db_session.refresh(student)
    db_session.refresh(course)

    return student, course


# ----------------------------------------------------------
# 輔助函數：取得測試用的 Session（供 create_test_data 使用）
# ----------------------------------------------------------
def get_test_db():
    """
    產生一個測試用的 Session。
    這跟 conftest.py 中的 override_get_db 功能相同，
    但在測試函數中需要直接操作資料庫時（例如建立初始資料），
    會用到這個函數。
    """
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==================================================
# 測試 1：選課成功
# ==================================================
def test_enroll_success(client):
    """
    測試正常選課流程。
    前提條件：資料庫中有學生和課程，且學生尚未選過該課程。
    預期結果：HTTP 201（Created），回傳選課紀錄。
    """
    # 取得測試用的資料庫 Session
    db = next(get_test_db())

    # 在資料庫中建立測試用的學生和課程
    student, course = create_test_data(db)

    # 發出 POST 請求，模擬學生選課
    response = client.post(
        "/enrollments/",  # API 端點路徑
        json={
            "student_id": student.id,  # 傳入學生的資料庫 id
            "course_id": course.id,  # 傳入課程的資料庫 id
        },
        headers=AUTH_HEADER,  # 帶上 JWT Token
    )

    # 驗證回應狀態碼為 201（成功建立）
    assert response.status_code == 201, f"預期狀態碼 201，但得到 {response.status_code}"

    # 驗證回應 body 中的資料正確
    data = response.json()
    assert data["student_id"] == student.id  # 確認 student_id 正確
    assert data["course_id"] == course.id  # 確認 course_id 正確
    assert data["status"] == "enrolled"  # 確認狀態為 enrolled


# ==================================================
# 測試 2：重複選課被擋
# ==================================================
def test_enroll_duplicate(client):
    """
    測試重複選課的情境。
    前提條件：學生已經選過該課程。
    預期結果：HTTP 409（Conflict），錯誤訊息提示「不可重複選課」。
    """
    db = next(get_test_db())

    # 建立測試用的學生和課程
    student, course = create_test_data(db)

    # 第一次選課（應該成功）
    response1 = client.post(
        "/enrollments/",
        json={"student_id": student.id, "course_id": course.id},
        headers=AUTH_HEADER,
    )
    assert response1.status_code == 201, "第一次選課應該成功（201）"

    # 第二次選課（應該失敗，因為重複選課）
    response2 = client.post(
        "/enrollments/",
        json={"student_id": student.id, "course_id": course.id},
        headers=AUTH_HEADER,
    )

    # 驗證第二次選課被擋，回傳 409 Conflict
    assert response2.status_code == 409, f"預期狀態碼 409，但得到 {response2.status_code}"

    # 驗證錯誤訊息包含「不可重複選課」
    assert "不可重複選課" in response2.json()["detail"]


# ==================================================
# 測試 3：名額額滿被擋
# ==================================================
def test_enroll_full(client):
    """
    測試課程額滿的情境。
    前提條件：課程的 max_capacity=1，且已經有一個學生選了這門課。
    預期結果：HTTP 409（Conflict），錯誤訊息提示「名額已滿」。
    """
    db = next(get_test_db())

    # 建立測試用的學生和課程（max_capacity=1）
    student1, course = create_test_data(db)

    # 建立第二個學生（用來測試額滿時的選課）
    student2 = Student(
        student_id="S99999999",
        name="陳小華",
        email="test2@example.com",
        department="資訊工程學系",
        enrollment_year=2024,
    )
    db.add(student2)
    db.commit()
    db.refresh(student2)

    # 第一個學生選課（會佔滿唯一的名額）
    response1 = client.post(
        "/enrollments/",
        json={"student_id": student1.id, "course_id": course.id},
        headers=AUTH_HEADER,
    )
    assert response1.status_code == 201, "第一個學生選課應該成功（201）"

    # 第二個學生選課（應該失敗，因為名額已滿）
    response2 = client.post(
        "/enrollments/",
        json={"student_id": student2.id, "course_id": course.id},
        headers=AUTH_HEADER,
    )

    # 驗證第二個學生選課被擋，回傳 409 Conflict
    assert response2.status_code == 409, f"預期狀態碼 409，但得到 {response2.status_code}"

    # 驗證錯誤訊息包含「名額已滿」
    assert "名額已滿" in response2.json()["detail"]


# ==================================================
# 測試 4：不帶 Token 呼叫選課 API 會被拒絕
# ==================================================
def test_enroll_without_token(client):
    """
    測試 JWT 權限驗證。
    前提條件：資料庫中有學生和課程。
    預期結果：不帶 Authorization 標頭呼叫選課 API → HTTP 401（Unauthorized）。
    """
    db = next(get_test_db())

    # 建立測試用的學生和課程
    student, course = create_test_data(db)

    # 沒有帶 Token，直接呼叫選課 API
    response = client.post(
        "/enrollments/",
        json={"student_id": student.id, "course_id": course.id},
    )

    # 驗證被拒絕，回傳 401
    assert response.status_code == 401, f"預期狀態碼 401，但得到 {response.status_code}"


# ==================================================
# 測試 5：登入 /login 可以拿到 Token
# ==================================================
def test_login_get_token(client):
    """
    測試登入 API。
    預期結果：輸入 admin / admin → 回傳 200，且帶有 access_token。
    """
    response = client.post(
        "/login",
        json={"username": "admin", "password": "admin"},
    )

    # 驗證登入成功
    assert response.status_code == 200, f"預期狀態碼 200，但得到 {response.status_code}"

    # 驗證回應中帶有 access_token
    data = response.json()
    assert data["token_type"] == "bearer"
    assert "access_token" in data and data["access_token"]
