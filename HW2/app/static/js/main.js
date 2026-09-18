// ============================================================
// main.js — 負責與後端 API 溝通
//
// 【白話文說明】
// 當使用者填完表單並點擊「選課」按鈕時，
// 1. JavaScript 會攔截表單的預設送出行為（避免頁面重新整理）
// 2. 取得使用者輸入的 student_id 和 course_id
// 3. 用 Fetch API 發出一個 POST 請求到後端的 /enrollments/ 端點
// 4. 後端回傳結果後，根據回應內容在畫面上顯示成功或失敗的訊息
//
// 【API 端點說明】
// POST http://127.0.0.1:8000/enrollments/
// Request Body（JSON 格式）：
//   {
//       "student_id": 1,   // 學生的資料庫 id（整數）
//       "course_id": 1     // 課程的資料庫 id（整數）
//   }
// Response（成功 201）：
//   {
//       "id": 1,
//       "student_id": 1,
//       "course_id": 1,
//       "status": "enrolled",
//       "enrolled_at": "2024-01-01T00:00:00"
//   }
// Response（失敗 409）：
//   {
//       "detail": "該學生已經選過這門課，不可重複選課"
//   }
// ============================================================

// 後端 API 的網址
// 如果後端不是跑在預設的 8000 埠號，請改成對應的網址
const API_URL = "http://127.0.0.1:8000/enrollments/";
const LOGIN_URL = "http://127.0.0.1:8000/login";
const STUDENT_API_URL = "http://127.0.0.1:8000/students/";
const COURSE_API_URL = "http://127.0.0.1:8000/courses/";

// 儲存登入後取得的 JWT Token，選課時需要帶上
let authToken = null;

// 取得頁面上的元素，方便後續操作
const form = document.getElementById("enrollForm");       // 表單
const messageBox = document.getElementById("messageBox"); // 提示訊息區域
const submitBtn = document.getElementById("submitBtn");   // 送出按鈕

// 管理功能頁面的元素
const studentForm = document.getElementById("studentForm");           // 新增學生表單
const studentMessage = document.getElementById("studentMessage");     // 新增學生的提示訊息
const courseForm = document.getElementById("courseForm");             // 新增課程表單
const courseMessage = document.getElementById("courseMessage");       // 新增課程的提示訊息
const courseListEl = document.getElementById("courseList");           // 課程清單顯示區

// ----------------------------------------------------------
// 頁面載入時自動登入（admin / admin），取得 JWT Token
// 選課 API 需要帶 Token 才能使用
// ----------------------------------------------------------
async function initAuth() {
    try {
        const response = await fetch(LOGIN_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: "admin", password: "admin" }),
        });
        if (response.ok) {
            const data = await response.json();
            authToken = data.access_token;
            // 登入成功後，順便載入課程清單
            await loadCourseList();
        }
    } catch (error) {
        // 登入失敗時，選課按鈕照常可用，送出時會顯示錯誤訊息
        showMessageTo(courseListEl, "登入失敗，無法載入課程清單", "error");
    }
}
initAuth();

// ----------------------------------------------------------
// 監聽表單的 submit 事件
// 當使用者點擊「選課」按鈕時，會觸發這個函數
// ----------------------------------------------------------
form.addEventListener("submit", async function(event) {
    // 阻止表單的預設行為（預設行為是重新整理頁面）
    event.preventDefault();

    // 取得使用者輸入的值
    const studentId = parseInt(document.getElementById("studentId").value);
    const courseId = parseInt(document.getElementById("courseId").value);

    // 簡單驗證：確認輸入的值是有效的數字
    if (isNaN(studentId) || isNaN(courseId)) {
        showMessage("請輸入有效的學生編號和課程編號", "error");
        return;
    }

    // 按下按鈕後，先把按鈕設為 disabled（避免重複點擊）
    submitBtn.disabled = true;
    submitBtn.textContent = "選課中...";

    // 先隱藏之前的提示訊息
    messageBox.style.display = "none";

        try {
            // ----------------------------------------------------------
            // 使用 Fetch API 發出 POST 請求到後端
            // ----------------------------------------------------------
            const headers = {
                "Content-Type": "application/json",  // 告訴後端我們送的是 JSON
            };
            // 如果有 token，帶上 Authorization 標頭
            if (authToken) {
                headers["Authorization"] = "Bearer " + authToken;
            }

            const response = await fetch(API_URL, {
                method: "POST",                    // 使用 POST 方法
                headers: headers,
                body: JSON.stringify({              // 把 JavaScript 物件轉成 JSON 字串
                    student_id: studentId,          // 學生的資料庫 id
                    course_id: courseId,            // 課程的資料庫 id
                }),
            });

        // 把後端回傳的 JSON 資料解析成 JavaScript 物件
        const data = await response.json();

        if (response.ok) {
            // ---- 選課成功（HTTP 狀態碼 201） ----
            showMessage(
                "選課成功！已將學生 " + data.student_id +
                " 加入課程 " + data.course_id +
                "（狀態：" + data.status + "）",
                "success"
            );
        } else {
            // ---- 選課失敗（HTTP 狀態碼 404 或 409） ----
            // 後端回傳的錯誤訊息會在 data.detail 中
            showMessage("選課失敗：" + data.detail, "error");
        }
    } catch (error) {
        // ---- 連線錯誤（例如後端沒有啟動） ----
        showMessage(
            "無法連線到後端伺服器，請確認後端是否已啟動（" + API_URL + "）",
            "error"
        );
    } finally {
        // 無論成功或失敗，都把按鈕恢復成可點擊的狀態
        submitBtn.disabled = false;
        submitBtn.textContent = "選課";
    }
});

// ----------------------------------------------------------
// 輔助函數：在畫面上顯示提示訊息
// message: 要顯示的文字
// type: "success"（綠色）或 "error"（紅色）
// target: 要顯示訊息的元素（預設是選課的 #messageBox）
// ----------------------------------------------------------
function showMessage(message, type, target = messageBox) {
    target.textContent = message;   // 設定訊息文字
    target.className = "message " + type;  // 設定樣式（成功=綠色，失敗=紅色）
    target.style.display = "block"; // 顯示訊息區域
}

// ----------------------------------------------------------
// 輔助函數：指定元素名稱的顯示訊息
// 就是 showMessage 的別名，語意上更清楚
// ----------------------------------------------------------
function showMessageTo(target, message, type) {
    showMessage(message, type, target);
}

// ----------------------------------------------------------
// 新增學生 —— 監聽 studentForm 的 submit 事件
// 把表單欄位轉換成後端要的 JSON，再送去 POST /students/
// ----------------------------------------------------------
studentForm.addEventListener("submit", async function(event) {
    event.preventDefault();  // 阻止頁面重新整理

    // 收集使用者輸入的資料，並轉成後端 API 要的欄位名稱
    const payload = {
        student_id: document.getElementById("newStudentId").value.trim(),
        name: document.getElementById("studentName").value.trim(),
        email: document.getElementById("studentEmail").value.trim(),
        department: document.getElementById("studentDept").value.trim(),
        enrollment_year: parseInt(document.getElementById("studentYear").value),
    };

    // 確認沒有空欄位
    if (!payload.student_id || !payload.name || !payload.email ||
        !payload.department || isNaN(payload.enrollment_year)) {
        showMessageTo(studentMessage, "請填寫完整的學生資料", "error");
        return;
    }

    const btn = document.getElementById("studentSubmitBtn");
    btn.disabled = true;
    btn.textContent = "新增中...";
    studentMessage.style.display = "none";

    try {
        const response = await fetch(STUDENT_API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + authToken,
            },
            body: JSON.stringify(payload),
        });
        const data = await response.json();

        if (response.ok) {
            // 新增成功（201）
            showMessageTo(
                studentMessage,
                "新增學生成功！學號：" + data.student_id + "，姓名：" + data.name,
                "success"
            );
            studentForm.reset();  // 清空表單，方便連續輸入
        } else {
            // 失敗（例如學號/email 重複、權限不足）
            showMessageTo(studentMessage, "新增學生失敗：" + data.detail, "error");
        }
    } catch (error) {
        showMessageTo(studentMessage, "無法連線到後端伺服器（" + STUDENT_API_URL + "）", "error");
    } finally {
        btn.disabled = false;
        btn.textContent = "新增學生";
    }
});

// ----------------------------------------------------------
// 新增課程 —— 監聽 courseForm 的 submit 事件
// 把表單欄位轉換成後端要的 JSON，再送去 POST /courses/
// ----------------------------------------------------------
courseForm.addEventListener("submit", async function(event) {
    event.preventDefault();  // 阻止頁面重新整理

    // 收集使用者輸入的資料，並轉成後端 API 要的欄位名稱
    const payload = {
        course_code: document.getElementById("courseCode").value.trim(),
        name: document.getElementById("courseName").value.trim(),
        credit: parseInt(document.getElementById("courseCredit").value),
        max_capacity: parseInt(document.getElementById("courseCapacity").value),
        teacher_name: document.getElementById("courseTeacher").value.trim(),
        semester: document.getElementById("courseSemester").value.trim(),
    };

    // 確認沒有空欄位
    if (!payload.course_code || !payload.name || isNaN(payload.credit) ||
        isNaN(payload.max_capacity) || !payload.teacher_name || !payload.semester) {
        showMessageTo(courseMessage, "請填寫完整的課程資料", "error");
        return;
    }

    const btn = document.getElementById("courseSubmitBtn");
    btn.disabled = true;
    btn.textContent = "新增中...";
    courseMessage.style.display = "none";

    try {
        const response = await fetch(COURSE_API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + authToken,
            },
            body: JSON.stringify(payload),
        });
        const data = await response.json();

        if (response.ok) {
            // 新增成功（201）
            showMessageTo(
                courseMessage,
                "新增課程成功！代碼：" + data.course_code + "，名稱：" + data.name,
                "success"
            );
            courseForm.reset();
            // 課程變多了，順便更新課程清單
            await loadCourseList();
        } else {
            // 失敗（例如課程代碼重複、權限不足）
            showMessageTo(courseMessage, "新增課程失敗：" + data.detail, "error");
        }
    } catch (error) {
        showMessageTo(courseMessage, "無法連線到後端伺服器（" + COURSE_API_URL + "）", "error");
    } finally {
        btn.disabled = false;
        btn.textContent = "新增課程";
    }
});

// ----------------------------------------------------------
// 載入課程清單 —— 呼叫 GET /courses/ 並渲染到頁面上
// 登入的使用者（學生、教務）都可以看
// ----------------------------------------------------------
async function loadCourseList() {
    // 還沒登入成功就拿不到 token，skip（等 initAuth 完成後會再呼叫一次）
    if (!authToken) {
        return;
    }

    courseListEl.textContent = "載入中...";

    try {
        const response = await fetch(COURSE_API_URL, {
            method: "GET",
            headers: { "Authorization": "Bearer " + authToken },
        });

        if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            showMessageTo(courseListEl, "載入課程清單失敗：" + (data.detail || response.status), "error");
            return;
        }

        const courses = await response.json();

        // 沒有課程時的提示
        if (!courses.length) {
            courseListEl.textContent = "目前沒有課程";
            courseListEl.className = "course-list";
            return;
        }

        // 把每一門課渲染成一格
        courseListEl.innerHTML = courses.map(function(c) {
            return (
                '<div class="course-item">' +
                '<div class="course-item-title">[' + c.course_code + '] ' + c.name + '</div>' +
                '<div class="course-item-meta">' +
                c.credit + ' 學分 ｜ 授課教師：' + c.teacher_name +
                ' ｜ 學期：' + c.semester + ' ｜ 名額：' + c.max_capacity + '</div>' +
                '</div>'
            );
        }).join("");
        courseListEl.className = "course-list";
    } catch (error) {
        showMessageTo(courseListEl, "無法連線到後端伺服器（" + COURSE_API_URL + "）", "error");
    }
}