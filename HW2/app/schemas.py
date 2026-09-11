# ============================================================
# schemas.py — Pydantic 資料驗證模型
# 用來驗證 API 請求（Request）與回應（Response）的資料格式。
# 與 ORM Model 分開，是 FastAPI 的最佳實踐。
# ============================================================

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


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
