# ============================================================
# schemas.py — Pydantic 資料驗證模型
# 用來驗證 API 請求（Request）與回應（Response）的資料格式。
# 與 ORM Model 分開，是 FastAPI 的最佳實踐。
# ============================================================

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ----------------------------------------------------------
# 新增學生 Schema — 客戶端打 API 時要帶的資料
# ----------------------------------------------------------
class StudentCreate(BaseModel):
    """
    新增學生的請求資料格式。
    客戶端需要提供學號、姓名、email、科系、入學年份。
    """
    student_id: str = Field(..., description="學號，不可重複")  # ... 表示必填
    name: str = Field(..., description="學生姓名")  # ... 表示必填
    email: str = Field(..., description="電子郵件，不可重複")  # ... 表示必填
    department: str = Field(..., description="科系")  # ... 表示必填
    enrollment_year: int = Field(..., description="入學年份")  # ... 表示必填


# ----------------------------------------------------------
# 新增學生回應 Schema — API 回傳給客戶端的資料格式
# ----------------------------------------------------------
class StudentResponse(BaseModel):
    """
    新增學生成功後回傳的資料格式。
    包含學生的完整資訊與資料庫自動產生的 id。
    """
    id: int  # 學生的主鍵
    student_id: str  # 學號
    name: str  # 姓名
    email: str  # 電子郵件
    department: str  # 科系
    enrollment_year: int  # 入學年份

    # 告訴 Pydantic 這個 schema 可以從 ORM 對象直接轉換
    # 這是 FastAPI + SQLAlchemy 搭配時的常見寫法
    model_config = {"from_attributes": True}


# ----------------------------------------------------------
# 新增課程 Schema — 客戶端打 API 時要帶的資料
# ----------------------------------------------------------
class CourseCreate(BaseModel):
    """
    新增課程的請求資料格式。
    客戶端需要提供課程代碼、名稱、學分、最大容量、授課教師、學期。
    """
    course_code: str = Field(..., description="課程代碼，不可重複")  # ... 表示必填
    name: str = Field(..., description="課程名稱")  # ... 表示必填
    credit: int = Field(..., description="學分數")  # ... 表示必填
    max_capacity: int = Field(60, description="最大選課人數（預設 60）")
    teacher_name: str = Field(..., description="授課教師")  # ... 表示必填
    semester: str = Field(..., description="學期")  # ... 表示必填


# ----------------------------------------------------------
# 新增課程回應 Schema — API 回傳給客戶端的資料格式
# ----------------------------------------------------------
class CourseResponse(BaseModel):
    """
    新增課程成功後回傳的資料格式。
    包含課程的完整資訊與資料庫自動產生的 id。
    """
    id: int  # 課程的主鍵
    course_code: str  # 課程代碼
    name: str  # 課程名稱
    credit: int  # 學分數
    max_capacity: int  # 最大選課人數
    teacher_name: str  # 授課教師
    semester: str  # 學期

    # 告訴 Pydantic 這個 schema 可以從 ORM 對象直接轉換
    # 這是 FastAPI + SQLAlchemy 搭配時的常見寫法
    model_config = {"from_attributes": True}


# ----------------------------------------------------------
# 選課請求 Schema — 客戶端打 API 時要帶的資料
# ----------------------------------------------------------
class EnrollmentRequest(BaseModel):
    """
    選課請求的資料格式。
    客戶端需要提供 student_id 和 course_id。
    """
    student_id: int = Field(..., description="學生的資料庫 id")  # ... 表示必填
    course_id: int = Field(..., description="課程的資料庫 id")  # ... 表示必填


# ----------------------------------------------------------
# 選課回應 Schema — API 回傳給客戶端的資料格式
# ----------------------------------------------------------
class EnrollmentResponse(BaseModel):
    """
    選課成功後回傳的資料格式。
    包含選課紀錄的完整資訊。
    """
    id: int  # 選課紀錄的主鍵
    student_id: int  # 學生 id
    course_id: int  # 課程 id
    status: str  # 狀態（enrolled / dropped / completed）
    enrolled_at: datetime  # 選課時間

    # 告訴 Pydantic 這個 schema 可以從 ORM 對象直接轉換
    # 這是 FastAPI + SQLAlchemy 搭配時的常見寫法
    model_config = {"from_attributes": True}


# ----------------------------------------------------------
# 錯誤回應 Schema — API 回傳錯誤時的格式
# ----------------------------------------------------------
class ErrorResponse(BaseModel):
    """
    當選課失敗時（重複選課或名額已滿），
    API 回傳的錯誤訊息格式。
    """
    detail: str  # 錯誤訊息內容
