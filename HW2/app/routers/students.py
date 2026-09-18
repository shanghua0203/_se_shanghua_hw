# ============================================================
# routers/students.py — 學生管理 API 路由
# 這個檔案提供「新增學生」的功能（教務限定）。
# 包含兩個檢查：學號是否重複、email 是否重複。
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import CurrentUser, get_current_user
from ..models import Student
from ..schemas import StudentCreate, StudentResponse
from .enrollment import get_db

# 建立一個 Router 實例，prefix 代表這個路由群組的 URL 前綴
router = APIRouter(
    prefix="/students",
    tags=["students"],
)


# ----------------------------------------------------------
# POST /students/ — 新增學生（教務限定）
# 權限規則：
#   - 沒帶 Token（未登入）→ 401
#   - 學生角色 → 403（沒有權限）
#   - 教務角色（admin）→ 201，回傳建立好的學生資料
# ----------------------------------------------------------
@router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(
    request: StudentCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    新增學生功能：
    0. 先驗證使用者有帶有效的 JWT Token（否則回傳 401）
    1. 權限檢查：只有教務（admin）可以新增學生
    2. 檢查學號是否重複
    3. 檢查 email 是否重複
    4. 通過所有檢查後，寫入資料庫
    """

    # ---- 步驟 1：權限檢查，只有教務（admin）可以新增學生 ----
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有權限新增學生",
        )

    # ---- 步驟 2：檢查學號是否重複 ----
    # 在 students 表中查詢是否有相同學號的紀錄
    existing_student_id = (
        db.query(Student).filter(Student.student_id == request.student_id).first()
    )
    if existing_student_id is not None:
        # 學號已存在 → 回傳 409 Conflict 錯誤
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="該學號已存在，不可重複新增",
        )

    # ---- 步驟 3：檢查 email 是否重複 ----
    # 在 students 表中查詢是否有相同 email 的紀錄
    existing_email = (
        db.query(Student).filter(Student.email == request.email).first()
    )
    if existing_email is not None:
        # email 已被使用 → 回傳 409 Conflict 錯誤
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="該 email 已被使用，不可重複",
        )

    # ---- 步驟 4：通過所有檢查，建立新的學生 ----
    new_student = Student(
        student_id=request.student_id,  # 設定學號
        name=request.name,  # 設定姓名
        email=request.email,  # 設定 email
        department=request.department,  # 設定科系
        enrollment_year=request.enrollment_year,  # 設定入學年份
    )
    db.add(new_student)  # 將新紀錄加入 Session（尚未寫入資料庫）
    db.commit()  # 送出交易，正式寫入資料庫
    db.refresh(new_student)  # 重新從資料庫讀取，取得 auto-generated 的 id 等欄位

    # 回傳建立成功的學生資料
    return new_student