# ============================================================
# test_courses.py — 課程管理 API 的單元測試
# 測試六種情境：
#   1. 教務（admin）新增課程成功
#   2. 課程代碼重複被擋
#   3. 不帶 Token 呼叫新增課程被拒（401）
#   4. 學生角色呼叫新增課程被拒（403）
#   5. 登入（學生）可以查詢課程清單
#   6. 不帶 Token 查詢課程清單被拒（401）
# ============================================================

from app.auth import create_access_token


# 教務使用者的 Token
ADMIN_TOKEN = create_access_token("admin", "admin")
# 學生的 Token
STUDENT_TOKEN = create_access_token("s111210505", "student")

# 兩種角色各自要帶的 Authorization 標頭
ADMIN_HEADER = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
STUDENT_HEADER = {"Authorization": f"Bearer {STUDENT_TOKEN}"}


# 一門合法的課程資料（每個測試都用全新的記憶體資料庫，不會互相干擾）
VALID_COURSE = {
    "course_code": "CS101",  # 課程代碼
    "name": "程式設計導論",  # 課程名稱
    "credit": 3,  # 學分數
    "max_capacity": 60,  # 最大選課人數
    "teacher_name": "李教授",  # 授課教師
    "semester": "112-2",  # 學期
}


# ==================================================
# 測試 1：教務新增課程成功
# ==================================================
def test_create_course_admin_success(client):
    """教務（admin）呼叫 POST /courses/ → 201，回傳建立好的課程資料。"""
    response = client.post("/courses/", json=VALID_COURSE, headers=ADMIN_HEADER)

    # 驗證回應狀態碼為 201（成功建立）
    assert response.status_code == 201, f"預期狀態碼 201，但得到 {response.status_code}"

    # 驗證回應 body 中的資料正確
    data = response.json()
    assert data["course_code"] == VALID_COURSE["course_code"]  # 課程代碼正確
    assert data["name"] == VALID_COURSE["name"]  # 課程名稱正確
    assert data["credit"] == VALID_COURSE["credit"]  # 學分數正確
    assert data["max_capacity"] == VALID_COURSE["max_capacity"]  # 容量正確
    assert data["teacher_name"] == VALID_COURSE["teacher_name"]  # 教師正確
    assert data["semester"] == VALID_COURSE["semester"]  # 學期正確


# ==================================================
# 測試 2：課程代碼重複被擋
# ==================================================
def test_create_course_duplicate_code(client):
    """重複的課程代碼 → 409 Conflict，錯誤訊息提示「課程代碼」。"""
    # 先建立一門課，佔住這個課程代碼
    response1 = client.post("/courses/", json=VALID_COURSE, headers=ADMIN_HEADER)
    assert response1.status_code == 201, "第一次新增應該成功（201）"

    # 相同課程代碼、不同課程名稱再新增一次（應該失敗，因為代碼重複）
    duplicate = {
        "course_code": VALID_COURSE["course_code"],  # 相同的課程代碼
        "name": "程式設計進階",  # 不同課程名稱
        "credit": 3,
        "max_capacity": 60,
        "teacher_name": "李教授",
        "semester": "112-2",
    }
    response2 = client.post("/courses/", json=duplicate, headers=ADMIN_HEADER)

    # 驗證被擋，回傳 409 Conflict
    assert response2.status_code == 409, f"預期狀態碼 409，但得到 {response2.status_code}"
    assert "課程代碼" in response2.json()["detail"]


# ==================================================
# 測試 3：不帶 Token 呼叫新增課程被拒
# ==================================================
def test_create_course_without_token(client):
    """不帶 Authorization 標頭呼叫 POST /courses/ → 401。"""
    response = client.post("/courses/", json=VALID_COURSE)

    # 驗證被拒絕，回傳 401
    assert response.status_code == 401, f"預期狀態碼 401，但得到 {response.status_code}"


# ==================================================
# 測試 4：學生角色呼叫新增課程被拒
# ==================================================
def test_create_course_student_forbidden(client):
    """學生（student）角色呼叫 POST /courses/ → 403 沒有權限。"""
    response = client.post("/courses/", json=VALID_COURSE, headers=STUDENT_HEADER)

    # 驗證被拒絕，回傳 403
    assert response.status_code == 403, f"預期狀態碼 403，但得到 {response.status_code}"
    assert "權限" in response.json()["detail"]


# ==================================================
# 測試 5：登入（學生）可以查詢課程清單
# ==================================================
def test_list_courses_student_success(client):
    """學生（student）呼叫 GET /courses/ → 200，能看到課程清單。"""
    # 先由教務建立一門課，再把學生叫來查清單
    response1 = client.post("/courses/", json=VALID_COURSE, headers=ADMIN_HEADER)
    assert response1.status_code == 201, "教務新增課程應該成功（201）"

    response = client.get("/courses/", headers=STUDENT_HEADER)

    # 學生登入就能查，預期 200
    assert response.status_code == 200, f"預期狀態碼 200，但得到 {response.status_code}"

    # 驗證回傳的就是「剛剛那門」課程
    data = response.json()
    assert isinstance(data, list) and len(data) == 1
    assert data[0]["course_code"] == VALID_COURSE["course_code"]
    assert data[0]["name"] == VALID_COURSE["name"]


# ==================================================
# 測試 6：不帶 Token 查詢課程清單被拒
# ==================================================
def test_list_courses_without_token(client):
    """不帶 Authorization 標頭呼叫 GET /courses/ → 401。"""
    response = client.get("/courses/")

    # 驗證被拒絕，回傳 401
    assert response.status_code == 401, f"預期狀態碼 401，但得到 {response.status_code}"