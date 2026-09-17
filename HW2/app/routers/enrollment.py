# ============================================================
# routers/enrollment.py — 選課 API 路由
# 這個檔案包含「學生選課」的核心業務邏輯。
# 包含三個檢查：學生存在、課程存在、重複選課、名額已滿。
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import SessionLocal
from ..models import Course, Enrollment, Student
from ..schemas import EnrollmentRequest, EnrollmentResponse

# 建立一個 Router 實例，prefix 代表這個路由群組的 URL 前綴
router = APIRouter(
    prefix="/enrollments",
    tags=["enrollments"],
)


# ----------------------------------------------------------
# 依賴注入（Dependency Injection）：取得資料庫 Session
# FastAPI 會在每次請求時自動建立一個 Session，請求結束後自動關閉。
# 這種寫法可以確保資源被正確釋放。
# ----------------------------------------------------------
def get_db():
    db = SessionLocal()  # 建立一個新的 Session
    try:
        yield db  # 把 Session 交給 API 使用
    finally:
        db.close()  # 無論成功或失敗，最後都會關閉 Session


# ----------------------------------------------------------
# POST /enrollments — 學生選課
# ----------------------------------------------------------
@router.post("/", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
def enroll_course(
    request: EnrollmentRequest,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """
    學生選課功能：
    0. 先驗證使用者有帶有效的 JWT Token（否則回傳 401）
    1. 檢查學生是否存在
    2. 檢查課程是否存在
    3. 檢查是否重複選課
    4. 檢查課程是否額滿
    5. 通過所有檢查後，寫入資料庫
    """

    # ---- 步驟 1：檢查學生是否存在 ----
    # 用 student_id（資料庫主鍵）去 students 表查詢
    student = db.query(Student).filter(Student.id == request.student_id).first()
    if student is None:
        # 如果查不到學生，回傳 404 Not Found 錯誤
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="找不到該學生",
        )

    # ---- 步驟 2：檢查課程是否存在 ----
    # 用 course_id（資料庫主鍵）去 courses 表查詢
    course = db.query(Course).filter(Course.id == request.course_id).first()
    if course is None:
        # 如果查不到課程，回傳 404 Not Found 錯誤
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="找不到該課程",
        )

    # ---- 步驟 3：檢查是否重複選課 ----
    # 在 enrollments 表中，查詢是否已經有這位學生選這門課的紀錄
    existing_enrollment = (
        db.query(Enrollment)
        .filter(
            Enrollment.student_id == request.student_id,
            Enrollment.course_id == request.course_id,
        )
        .first()
    )
    if existing_enrollment is not None:
        # 如果已經選過這門課，回傳 409 Conflict 錯誤
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="該學生已經選過這門課，不可重複選課",
        )

    # ---- 步驟 4：檢查課程是否額滿 ----
    # 先統計這門課目前有多少人選（status 為 enrolled 的才算）
    current_count = (
        db.query(Enrollment)
        .filter(
            Enrollment.course_id == request.course_id,
            Enrollment.status == "enrolled",
        )
        .count()
    )
    # 如果目前選課人數 >= 課程的最大容納人數，就表示額滿
    if current_count >= course.max_capacity:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="該課程名額已滿，無法選課",
        )

    # ---- 步驟 5：通過所有檢查，建立新的選課紀錄 ----
    new_enrollment = Enrollment(
        student_id=request.student_id,  # 設定學生 id
        course_id=request.course_id,  # 設定課程 id
        status="enrolled",  # 預設狀態為「已選課」
    )
    db.add(new_enrollment)  # 將新紀錄加入 Session（尚未寫入資料庫）
    db.commit()  # 送出交易，正式寫入資料庫
    db.refresh(new_enrollment)  # 重新從資料庫讀取，取得 auto-generated 的 id 等欄位

    # 回傳成功的選課紀錄
    return new_enrollment
