# ============================================================
# test_roles.py — 角色權限（學生 / 教務）的單元測試
# 測的重點：
#   1. 教務限定端點 GET /enrollments/list
#      - 沒帶 Token → 401
#      - 學生角色 → 403（沒權限）
#      - 教務角色 → 200（可以看到選課紀錄）
#   2. 選課 POST /enrollments/ 維持「任何已登入者」皆可呼叫
#      - 學生角色可以選課
#      - 教務角色也可以選課
# ============================================================

from app.auth import create_access_token
from app.models import Course, Enrollment, Student
from tests.conftest import TestSessionLocal


# 教務使用者的 Token
ADMIN_TOKEN = create_access_token("admin", "admin")
# 學生的 Token
STUDENT_TOKEN = create_access_token("s111210505", "student")

# 兩種角色各自要帶的 Authorization 標頭
ADMIN_HEADER = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
STUDENT_HEADER = {"Authorization": f"Bearer {STUDENT_TOKEN}"}


# ----------------------------------------------------------
# 輔助函數：取得測試用 Session
# ----------------------------------------------------------
def get_test_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ----------------------------------------------------------
# 輔助函數：建立一筆測試用的「學生」與「課程」
# ----------------------------------------------------------
def create_student_course(db_session):
    student = Student(
        student_id="S111210505",
        name="王小明",
        email="test@example.com",
        department="資訊工程學系",
        enrollment_year=2024,
    )
    course = Course(
        course_code="CS101",
        name="程式設計導論",
        credit=3,
        max_capacity=60,
        teacher_name="李教授",
        semester="112-2",
    )
    db_session.add_all([student, course])
    db_session.commit()
    db_session.refresh(student)
    db_session.refresh(course)
    return student, course


# ==================================================
# 測試 1：教務限定端點，沒帶 Token → 401
# ==================================================
def test_list_enrollments_without_token(client):
    """不帶 Authorization 標頭呼叫 GET /enrollments/list → 401。"""
    response = client.get("/enrollments/list")
    assert response.status_code == 401, f"預期狀態碼 401，但得到 {response.status_code}"


# ==================================================
# 測試 2：教務限定端點，學生角色 → 403
# ==================================================
def test_list_enrollments_student_forbidden(client):
    """學生（student）呼叫教務限定端點 → 403 沒有權限。"""
    response = client.get("/enrollments/list", headers=STUDENT_HEADER)
    assert response.status_code == 403, f"預期狀態碼 403，但得到 {response.status_code}"
    assert "權限" in response.json()["detail"]


# ==================================================
# 測試 3：教務限定端點，教務角色 → 200 可查看
# ==================================================
def test_list_enrollments_admin_success(client):
    """教務（admin）呼叫 GET /enrollments/list → 200，能看到選課紀錄。"""
    db = next(get_test_db())

    # 建立學生、課程，並先選一門課
    student, course = create_student_course(db)
    enrollment = Enrollment(
        student_id=student.id,
        course_id=course.id,
        status="enrolled",
    )
    db.add(enrollment)
    db.commit()

    response = client.get("/enrollments/list", headers=ADMIN_HEADER)
    assert response.status_code == 200, f"預期狀態碼 200，但得到 {response.status_code}"

    # 驗證回傳的就是「剛剛那筆」選課紀錄
    data = response.json()
    assert isinstance(data, list) and len(data) == 1
    assert data[0]["student_id"] == student.id
    assert data[0]["course_id"] == course.id
    assert data[0]["status"] == "enrolled"


# ==================================================
# 測試 4：選課 POST 允許「學生」角色呼叫
# ==================================================
def test_enroll_post_allows_student_role(client):
    """學生（student）角色呼叫選課 API → 201 成功。"""
    db = next(get_test_db())
    student, course = create_student_course(db)

    response = client.post(
        "/enrollments/",
        json={"student_id": student.id, "course_id": course.id},
        headers=STUDENT_HEADER,
    )
    assert response.status_code == 201, f"預期狀態碼 201，但得到 {response.status_code}"


# ==================================================
# 測試 5：選課 POST 允許「教務」角色呼叫
# ==================================================
def test_enroll_post_allows_admin_role(client):
    """教務（admin）角色呼叫選課 API → 201 成功。"""
    db = next(get_test_db())
    student, course = create_student_course(db)

    response = client.post(
        "/enrollments/",
        json={"student_id": student.id, "course_id": course.id},
        headers=ADMIN_HEADER,
    )
    assert response.status_code == 201, f"預期狀態碼 201，但得到 {response.status_code}"