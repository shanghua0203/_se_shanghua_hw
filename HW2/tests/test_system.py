# ============================================================
# test_system.py — 系統整合測試（System Test / E2E）
#
# 【這份測試在做什麼？】
# 用「真的瀏覽器」（Playwright + Chromium）模擬一個真實的學生：
#   1. 打開前端網頁
#   2. 輸入學號與課程編號
#   3. 點擊送出按鈕
#   4. 確認畫面上顯示「選課成功」
#   5. 打開資料庫，確認這筆選課紀錄真的有寫進去
#
# 【為什麼用 Playwright？】
# - 安裝簡單：pip install 之後，再一行指令下載瀏覽器即可，不用像 Selenium
#   還要去抓 WebDriver 中介程式
# - 會「自動等待」畫面元素出現，測試更穩定、不容易出錯
# - 有官方的 pytest 外掛（pytest-playwright），跟 pytest 整合很順
#
# 【測試怎麼運作的？】
# 測試會先在背景啟動一個「真的後端伺服器」（跑在 127.0.0.1:8000），
# 再用瀏覽器去開 http://127.0.0.1:8000/ 這個頁面操作。
# 跟前面單元測試最大的不同是：單元測試在測試資料庫內測 API 邏輯，
# 而這支測試是「前後端都裝起來」，從使用者角度完整走一遍流程。
# ============================================================

import threading
import time
import urllib.request

import pytest
import uvicorn

from app.database import engine, SessionLocal
from app.main import app
from app.models import Base, Course, Enrollment, Student

# ---- 測試用的伺服器設定 ----
# 注意：前端 index.html 的 JavaScript 是寫死呼叫 127.0.0.1:8000，
# 所以測試伺服器也必須跑在 8000 埠，兩邊才對得上。
TEST_HOST = "127.0.0.1"
TEST_PORT = 8000
BASE_URL = f"http://{TEST_HOST}:{TEST_PORT}"


# ----------------------------------------------------------
# 輔助函數：等待後端伺服器啟動完成
# 因為伺服器是在「背景執行緒」啟動的，需要確認它真的可以連線，
# 測試才不會一忙就往下跑、結果頁面打不開。
# ----------------------------------------------------------
def _wait_for_server(timeout=15):
    """
    不斷嘗試連到測試伺服器，直到連上才回傳 True；
    超過 timeout 秒還沒連上就回傳 False。
    """
    deadline = time.time() + timeout  # 設定截止時間
    while time.time() < deadline:  # 只要還沒超過時間就繼續試
        try:
            # 嘗試連到伺服器的根路徑（會回傳前端 HTML）
            urllib.request.urlopen(BASE_URL + "/", timeout=1)
            return True  # 連上了！
        except Exception:
            time.sleep(0.2)  # 還沒準備好，休息一下再試
    return False  # 時間到了還是連不上


# ----------------------------------------------------------
# Fixture：啟動一個「真的」後端伺服器 + 準備測試資料
# scope="module" 表示整個測試檔只啟動一次伺服器，省時間。
# ----------------------------------------------------------
@pytest.fixture(scope="module")
def live_server():
    """
    這個 fixture 負責：
    1. 清空資料庫，並重新建立資料表
    2. 插入一筆「測試學生」和一門「測試課程」
    3. 在背景執行緒啟動 uvicorn 伺服器
    4. 測試結束後，關閉伺服器、清理資料庫
    """
    # ---- 步驟 1：清空資料庫，再重新建立所有資料表 ----
    # 特別注意：不能用「刪掉 app.db 檔案」的方式清空，
    # 因為 SQLAlchemy 的 engine 會保留連線，若檔案被刪掉，
    # 之後 create_all 會誤以為表格還在（跑在舊的連線上）而不重新建立。
    # 所以改用 drop_all + create_all 來重置資料庫。
    Base.metadata.drop_all(bind=engine)  # 先刪掉所有資料表
    Base.metadata.create_all(bind=engine)  # 再重新建立資料表

    db = SessionLocal()  # 建立一個連到 app.db 的 Session
    try:
        # ---- 步驟 2：插入測試資料 ----
        # 建立一筆測試用的學生
        student = Student(
            student_id="S111210505",  # 學號
            name="王小明",  # 姓名
            email="s111210505@example.com",  # 電子郵件
            department="資訊工程學系",  # 科系
            enrollment_year=2024,  # 入學年份
        )
        db.add(student)

        # 建立一門測試用的課程（max_capacity=60，一定選得進去）
        course = Course(
            course_code="CS101",  # 課程代碼
            name="程式設計導論",  # 課程名稱
            credit=3,  # 學分數
            max_capacity=60,  # 最大容納人數
            teacher_name="李教授",  # 授課教師
            semester="112-2",  # 學期
        )
        db.add(course)

        db.commit()  # 寫入資料庫，取得 auto-generated 的 id

        # 重新從資料庫讀取，確保拿到的 id 是最新的
        db.refresh(student)
        db.refresh(course)

        # 記下學生與課程的 id，之後給瀏覽器輸入用
        student_id = student.id
        course_id = course.id
    finally:
        db.close()

    # ---- 步驟 3：啟動後端伺服器 ----
    # 重要：conftest.py 為了單元測試，有把 app 的資料庫依賴「換成」測試資料庫。
    # 但系統測試要用「真的資料庫（app.db）」，所以先把覆寫清掉，
    # 這樣伺服器才會真的打 app.db，而不是打到記憶體資料庫。
    saved_overrides = dict(app.dependency_overrides)  # 先保存原本的覆寫
    app.dependency_overrides.clear()  # 清除覆寫，讓伺服器使用真實 app.db

    # 設定 uvicorn 伺服器（log_level="warning" 讓測試輸出乾淨一點）
    config = uvicorn.Config(
        app,  # 直接使用已經 import 好的 FastAPI app
        host=TEST_HOST,
        port=TEST_PORT,
        log_level="warning",
    )
    server = uvicorn.Server(config)

    # 把伺服器放到背景執行緒跑（daemon=True 表示主程式結束它就跟著結束）
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # 等待伺服器真正可以連線
    if not _wait_for_server():
        raise RuntimeError("測試伺服器沒有在時間內啟動，無法執行系統測試")

    # 把測試資料交給測試函數使用
    yield {"student_id": student_id, "course_id": course_id}

    # ---- 步驟 4：測試結束後的清理 ----
    server.should_exit = True  # 通知 uvicorn 停止
    thread.join(timeout=10)  # 等背景執行緒結束

    # 把原本的 dependency_overrides 還原（不影響其他測試）
    app.dependency_overrides.clear()
    app.dependency_overrides.update(saved_overrides)

    # 清空資料表，讓 app.db 回到空狀態（下次測試會重新建立）
    Base.metadata.drop_all(bind=engine)
    # 關閉所有資料庫連線，避免殘留連線造成後續問題
    engine.dispose()


# ----------------------------------------------------------
# 輔助函數：檢查資料庫裡有沒有這筆選課紀錄
# ----------------------------------------------------------
def _check_enrollment_exists(student_id, course_id):
    """
    用 SQLAlchemy 去查 app.db：
    如果有找到「該學生 + 該課程」的選課紀錄，回傳 True，否則 False。
    """
    db = SessionLocal()
    try:
        record = (
            db.query(Enrollment)  # 查選課紀錄表
            .filter(
                Enrollment.student_id == student_id,  # 條件 1：學生相符
                Enrollment.course_id == course_id,  # 條件 2：課程相符
            )
            .first()  # 只取第一筆
        )
        return record is not None  # 有找到就回傳 True
    finally:
        db.close()  # 用完記得關 Session


# ==================================================
# 主測試：模擬真實學生操作完整選課流程
# ==================================================
def test_system_enrollment_flow(live_server, page):
    """
    【測試情境】模擬真實學生操作的完整流程：
      1. 用瀏覽器打開前端網頁
      2. 輸入學號與課程編號
      3. 點擊「選課」送出按鈕
      4. 驗證畫面上出現「選課成功」的訊息
      5. 去資料庫檢查這筆選課紀錄確實存在
    """
    # 取出 fixture 準備好的學生與課程 id
    student_id = live_server["student_id"]
    course_id = live_server["course_id"]

    # ---- 情境 1：打開前端網頁 ----
    # 用 Playwright 開一個無頭瀏覽器，前往後端首頁
    page.goto(f"{BASE_URL}/")

    # 確認網頁有成功載入（標題是我們設定的「校務選課系統」）
    assert "校務選課系統" in page.title(), "網頁標題不對，可能頁面沒載入成功"

    # 確認選課表單有出現在畫面上
    assert page.locator("#enrollForm").is_visible(), "找不到選課表單"

    # ---- 情境 2：輸入學號與課程編號 ----
    page.fill("#studentId", str(student_id))  # 在「學生編號」欄位輸入學號
    page.fill("#courseId", str(course_id))  # 在「課程編號」欄位輸入課程編號

    # ---- 情境 3：點擊送出按鈕 ----
    page.click("#submitBtn")  # 點擊「選課」按鈕

    # ---- 情境 4：驗證畫面出現「選課成功」的訊息 ----
    # 因為是呼叫 API，需要等一下後端回傳。
    # Playwright 的 expect(...).to_be_visible() 會自動等到元素出現
    message_box = page.locator("#messageBox")
    message_box.wait_for(state="visible", timeout=10000)  # 最多等 10 秒

    # 讀取畫面上的訊息文字
    message_text = message_box.inner_text()
    print(f"\n[系統測試] 畫面上的訊息：{message_text}")

    # 驗證訊息有包含「選課成功」
    assert "選課成功" in message_text, f"畫面沒有顯示成功訊息，實際內容：{message_text}"

    # ---- 情境 5：去資料庫確認資料真的有寫進去 ----
    exists = _check_enrollment_exists(student_id, course_id)
    assert exists, "資料庫中找不到這筆選課紀錄，代表選課沒有真正寫入資料庫"