# ============================================================
# models.py — SQLAlchemy ORM 模型定義
# 這個檔案負責定義資料庫的「表格結構」，
# 用 Python 類別來描述 students、courses、enrollments、users 四張表。
# ============================================================

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, relationship


# 所有 ORM 模型的基礎類別，所有 Model 都要繼承它
class Base(DeclarativeBase):
    pass


# ----------------------------------------------------------
# User 模型 — 對應資料庫中的 users 表
# 用來存放登入帳號：教務（admin）與學生（student）都記在這裡。
# 密碼一律只存「bcrypt 雜湊」，絕對不存明文。
# ----------------------------------------------------------
class User(Base):
    __tablename__ = "users"  # 資料庫中實際的表名

    id = Column(Integer, primary_key=True, autoincrement=True)  # 主鍵，自動遞增
    username = Column(String(50), unique=True, nullable=False)  # 帳號，不可重複
    password_hash = Column(String(128), nullable=False)  # 密碼雜湊（bcrypt）
    role = Column(String(10), nullable=False)  # 角色：admin（教務）/ student（學生）
    is_active = Column(Boolean, default=True, nullable=False)  # 帳號是否啟用
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)  # 建立時間
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False,
    )  # 更新時間


# ----------------------------------------------------------
# Student 模型 — 對應資料庫中的 students 表
# ----------------------------------------------------------
class Student(Base):
    __tablename__ = "students"  # 資料庫中實際的表名

    id = Column(Integer, primary_key=True, autoincrement=True)  # 主鍵，自動遞增
    student_id = Column(String(20), unique=True, nullable=False)  # 學號，不可重複
    name = Column(String(50), nullable=False)  # 學生姓名
    email = Column(String(100), unique=True, nullable=False)  # 電子郵件
    department = Column(String(50), nullable=False)  # 科系
    enrollment_year = Column(Integer, nullable=False)  # 入學年份
    is_active = Column(Boolean, default=True, nullable=False)  # 是否在學
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)  # 建立時間
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False,
    )  # 更新時間

    # 設定與 enrollments 的「一對多」關係
    # 一個學生可以有多筆選課紀錄
    enrollments = relationship("Enrollment", back_populates="student")


# ----------------------------------------------------------
# Course 模型 — 對應資料庫中的 courses 表
# ----------------------------------------------------------
class Course(Base):
    __tablename__ = "courses"  # 資料庫中實際的表名

    id = Column(Integer, primary_key=True, autoincrement=True)  # 主鍵，自動遞增
    course_code = Column(String(20), unique=True, nullable=False)  # 課程代碼，不可重複
    name = Column(String(100), nullable=False)  # 課程名稱
    credit = Column(Integer, nullable=False)  # 學分數
    max_capacity = Column(Integer, default=60, nullable=False)  # 最大選課人數
    teacher_name = Column(String(50), nullable=False)  # 授課教師
    semester = Column(String(20), nullable=False)  # 學期
    is_active = Column(Boolean, default=True, nullable=False)  # 是否開課
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False,
    )  # 更新時間

    # 設定與 enrollments 的「一對多」關係
    # 一門課程可以被多個學生選
    enrollments = relationship("Enrollment", back_populates="course")


# ----------------------------------------------------------
# Enrollment 模型 — 對應資料庫中的 enrollments 表
# 這是一張「中間表」，用來連接學生與課程（多對多）
# ----------------------------------------------------------
class Enrollment(Base):
    __tablename__ = "enrollments"  # 資料庫中實際的表名

    id = Column(Integer, primary_key=True, autoincrement=True)  # 主鍵，自動遞增
    student_id = Column(
        Integer, ForeignKey("students.id"), nullable=False
    )  # 外鍵，指向 students 表的 id
    course_id = Column(
        Integer, ForeignKey("courses.id"), nullable=False
    )  # 外鍵，指向 courses 表的 id
    grade = Column(String(2), nullable=True)  # 成績，可以為空（尚未評分）
    status = Column(
        String(20), default="enrolled", nullable=False
    )  # 狀態：enrolled / dropped / completed
    enrolled_at = Column(DateTime, default=datetime.utcnow, nullable=False)  # 選課時間
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False,
    )

    # 設定與 student 的「多對一」關係（反向）
    student = relationship("Student", back_populates="enrollments")
    # 設定與 course 的「多對一」關係（反向）
    course = relationship("Course", back_populates="enrollments")

    # 唯一約束：同一個學生不能重複選同一門課
    # 用 Table-level constraint 實作
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_student_course"),
    )
