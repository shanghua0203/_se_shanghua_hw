# ============================================================
# test_students.py — 學生管理 API 的單元測試
# 測試五種情境：
#   1. 教務（admin）新增學生成功
#   2. 學號重複被擋
#   3. email 重複被擋
#   4. 不帶 Token 呼叫被拒（401）
#   5. 學生角色呼叫被拒（403）
# ============================================================

from app.auth import create_access_token


# 教務使用者的 Token
ADMIN_TOKEN = create_access_token("admin", "admin")
# 學生的 Token
STUDENT_TOKEN = create_access_token("s111210505", "student")

# 兩種角色各自要帶的 Authorization 標頭
ADMIN_HEADER = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
STUDENT_HEADER = {"Authorization": f"Bearer {STUDENT_TOKEN}"}


# 一組合法的學生資料（每個測試都用全新的記憶體資料庫，不會互相干擾）
VALID_STUDENT = {
    "student_id": "S111210505",  # 學號
    "name": "王小明",  # 姓名
    "email": "s111210505@example.com",  # 電子郵件
    "department": "資訊工程學系",  # 科系
    "enrollment_year": 2024,  # 入學年份
}


# ==================================================
# 測試 1：教務新增學生成功
# ==================================================
def test_create_student_admin_success(client):
    """教務（admin）呼叫 POST /students/ → 201，回傳建立好的學生資料。"""
    response = client.post("/students/", json=VALID_STUDENT, headers=ADMIN_HEADER)

    # 驗證回應狀態碼為 201（成功建立）
    assert response.status_code == 201, f"預期狀態碼 201，但得到 {response.status_code}"

    # 驗證回應 body 中的資料正確
    data = response.json()
    assert data["student_id"] == VALID_STUDENT["student_id"]  # 學號正確
    assert data["name"] == VALID_STUDENT["name"]  # 姓名正確
    assert data["email"] == VALID_STUDENT["email"]  # email 正確
    assert data["department"] == VALID_STUDENT["department"]  # 科系正確
    assert data["enrollment_year"] == VALID_STUDENT["enrollment_year"]  # 入學年正確


# ==================================================
# 測試 2：學號重複被擋
# ==================================================
def test_create_student_duplicate_student_id(client):
    """重複的學號 → 409 Conflict，錯誤訊息提示「學號」。"""
    # 先建立一筆，佔住這個學號
    response1 = client.post("/students/", json=VALID_STUDENT, headers=ADMIN_HEADER)
    assert response1.status_code == 201, "第一次新增應該成功（201）"

    # 同一學號、不同 email 再新增一次（應該失敗，因為學號重複）
    duplicate = {
        "student_id": VALID_STUDENT["student_id"],  # 相同的學號
        "name": "李四",
        "email": "another@example.com",  # 不同 email
        "department": "資訊工程學系",
        "enrollment_year": 2024,
    }
    response2 = client.post("/students/", json=duplicate, headers=ADMIN_HEADER)

    # 驗證被擋，回傳 409 Conflict
    assert response2.status_code == 409, f"預期狀態碼 409，但得到 {response2.status_code}"
    assert "學號" in response2.json()["detail"]


# ==================================================
# 測試 3：email 重複被擋
# ==================================================
def test_create_student_duplicate_email(client):
    """重複的 email → 409 Conflict，錯誤訊息提示「email」。"""
    # 先建立一筆，佔住這個 email
    response1 = client.post("/students/", json=VALID_STUDENT, headers=ADMIN_HEADER)
    assert response1.status_code == 201, "第一次新增應該成功（201）"

    # 不同學號、相同 email 再新增一次（應該失敗，因為 email 重複）
    duplicate = {
        "student_id": "S99999999",  # 不同學號
        "name": "李四",
        "email": VALID_STUDENT["email"],  # 相同的 email
        "department": "資訊工程學系",
        "enrollment_year": 2024,
    }
    response2 = client.post("/students/", json=duplicate, headers=ADMIN_HEADER)

    # 驗證被擋，回傳 409 Conflict
    assert response2.status_code == 409, f"預期狀態碼 409，但得到 {response2.status_code}"
    assert "email" in response2.json()["detail"]


# ==================================================
# 測試 4：不帶 Token 呼叫被拒
# ==================================================
def test_create_student_without_token(client):
    """不帶 Authorization 標頭呼叫 POST /students/ → 401。"""
    response = client.post("/students/", json=VALID_STUDENT)

    # 驗證被拒絕，回傳 401
    assert response.status_code == 401, f"預期狀態碼 401，但得到 {response.status_code}"


# ==================================================
# 測試 5：學生角色呼叫被拒
# ==================================================
def test_create_student_student_forbidden(client):
    """學生（student）角色呼叫 POST /students/ → 403 沒有權限。"""
    response = client.post("/students/", json=VALID_STUDENT, headers=STUDENT_HEADER)

    # 驗證被拒絕，回傳 403
    assert response.status_code == 403, f"預期狀態碼 403，但得到 {response.status_code}"
    assert "權限" in response.json()["detail"]