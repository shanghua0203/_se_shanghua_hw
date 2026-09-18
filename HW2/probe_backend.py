#!/usr/bin/env python3
# 用「真的 HTTP」探測後端：登入拿到的 Token 內容、以及 /enrollments/list 的回應。
import base64
import json
import threading
import time
import urllib.request

import uvicorn

# 清空資料庫 + 建立資料表 + seed（複製 live_server fixture 的做法）
from app.database import SessionLocal, engine
from app.models import Base, Course, Enrollment, Student, User
from app.auth import get_password_hash


def _seed():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        student = Student(
            student_id="S111210505", name="王小明",
            email="s111210505@example.com", department="資訊工程學系",
            enrollment_year=2024,
        )
        db.add(student)
        course = Course(
            course_code="CS101", name="程式設計導論", credit=3,
            max_capacity=60, teacher_name="李教授", semester="112-2",
        )
        db.add(course)
        admin_user = User(
            username="admin", password_hash=get_password_hash("admin"), role="admin",
        )
        db.add(admin_user)
        db.commit()
        db.refresh(student)
        db.refresh(course)
        return student.id, course.id
    finally:
        db.close()


def _http(method, url, body=None, token=None):
    req = urllib.request.Request(url, method=method)
    if token:
        req.add_header("Authorization", "Bearer " + token)
    if body is not None:
        data = json.dumps(body).encode()
        req.add_header("Content-Type", "application/json")
        req.add_header("Content-Length", str(len(data)))
        return urllib.request.urlopen(req, data=data)
    return urllib.request.urlopen(req)


def _decode_payload(token):
    part = token.split(".")[1]
    b64 = part.replace("-", "+").replace("_", "/")
    b64 += "=" * ((4 - len(b64) % 4) % 4)
    return json.loads(base64.b64decode(b64))


def _wait(timeout=15):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen("http://127.0.0.1:8000/", timeout=1)
            return True
        except Exception:
            time.sleep(0.2)
    return False


def main():
    student_id, course_id = _seed()
    config = uvicorn.Config("app.main:app", host="127.0.0.1", port=8000, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    if not _wait():
        print("SERVER_FAILED")
        return
    print(f"SEED student_id={student_id} course_id={course_id}")

    base = "http://127.0.0.1:8000"

    # ---- 1. admin 登入 ----
    try:
        r = _http("POST", base + "/login", {"username": "admin", "password": "admin"})
        admin_data = json.load(r)
        admin_token = admin_data["access_token"]
        print("ADMIN_LOGIN", r.status)
        print("ADMIN_KEYS", sorted(admin_data.keys()))
        print("ADMIN_CLAIMS", _decode_payload(admin_token))
    except Exception as e:
        print("ADMIN_LOGIN_FAIL", repr(e), getattr(e, "code", ""))
        return

    # ---- 2. 學生登入（測試裡用的是 s111210505）----
    try:
        r = _http("POST", base + "/login", {"username": "s111210505", "password": "s111210505"})
        stu_data = json.load(r)
        print("STU_LOGIN", r.status, sorted(stu_data.keys()))
    except urllib.error.HTTPError as e:
        print("STU_LOGIN", e.code, "BODY", e.read().decode())

    # ---- 3. 用 admin token 打 /enrollments/list ----
    try:
        r = _http("GET", base + "/enrollments/list", token=admin_token)
        print("ADMIN_LIST", r.status, "BODY", r.read().decode()[:300])
    except urllib.error.HTTPError as e:
        print("ADMIN_LIST", e.code, "BODY", e.read().decode())

    server.should_exit = True
    thread.join(timeout=10)


if __name__ == "__main__":
    main()
