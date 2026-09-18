# ============================================================
# routers/courses.py — 課程管理 API 路由
# 這個檔案提供兩種功能：
#   1. POST /courses/  — 新增課程（教務限定）
#   2. GET  /courses/  — 查詢課程清單（登入即可）
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import CurrentUser, get_current_user
from ..models import Course
from ..schemas import CourseCreate, CourseResponse
from .enrollment import get_db

# 建立一個 Router 實例，prefix 代表這個路由群組的 URL 前綴
router = APIRouter(
    prefix="/courses",
    tags=["courses"],
)


# ----------------------------------------------------------
# POST /courses/ — 新增課程（教務限定）
# 權限規則：
#   - 沒帶 Token（未登入）→ 401
#   - 學生角色 → 403（沒有權限）
#   - 教務角色（admin）→ 201，回傳建立好的課程資料
# ----------------------------------------------------------
@router.post("/", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(
    request: CourseCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    新增課程功能：
    0. 先驗證使用者有帶有效的 JWT Token（否則回傳 401）
    1. 權限檢查：只有教務（admin）可以新增課程
    2. 檢查課程代碼是否重複
    3. 通過所有檢查後，寫入資料庫
    """

    # ---- 步驟 1：權限檢查，只有教務（admin）可以新增課程 ----
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有權限新增課程",
        )

    # ---- 步驟 2：檢查課程代碼是否重複 ----
    # 在 courses 表中查詢是否有相同課程代碼的紀錄
    existing_course = (
        db.query(Course).filter(Course.course_code == request.course_code).first()
    )
    if existing_course is not None:
        # 課程代碼已存在 → 回傳 409 Conflict 錯誤
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="該課程代碼已存在，不可重複新增",
        )

    # ---- 步驟 3：通過所有檢查，建立新的課程 ----
    new_course = Course(
        course_code=request.course_code,  # 設定課程代碼
        name=request.name,  # 設定課程名稱
        credit=request.credit,  # 設定學分數
        max_capacity=request.max_capacity,  # 設定最大選課人數
        teacher_name=request.teacher_name,  # 設定授課教師
        semester=request.semester,  # 設定學期
    )
    db.add(new_course)  # 將新紀錄加入 Session（尚未寫入資料庫）
    db.commit()  # 送出交易，正式寫入資料庫
    db.refresh(new_course)  # 重新從資料庫讀取，取得 auto-generated 的 id 等欄位

    # 回傳建立成功的課程資料
    return new_course


# ----------------------------------------------------------
# GET /courses/ — 查詢課程清單
# 權限規則：
#   - 沒帶 Token（未登入）→ 401
#   - 學生角色 → 200（可以看）
#   - 教務角色 → 200（可以看）
# ----------------------------------------------------------
@router.get("/", response_model=list[CourseResponse])
def list_courses(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    查詢所有課程的清單。
    只要登入就能看（學生、教務都可以），方便前端選課前先看有哪些課。
    """
    # 回傳資料庫中所有的課程
    return db.query(Course).all()