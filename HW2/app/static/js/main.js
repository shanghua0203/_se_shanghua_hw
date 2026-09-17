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

// 取得頁面上的元素，方便後續操作
const form = document.getElementById("enrollForm");       // 表單
const messageBox = document.getElementById("messageBox"); // 提示訊息區域
const submitBtn = document.getElementById("submitBtn");   // 送出按鈕

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
        const response = await fetch(API_URL, {
            method: "POST",                    // 使用 POST 方法
            headers: {
                "Content-Type": "application/json",  // 告訴後端我們送的是 JSON
            },
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
// ----------------------------------------------------------
function showMessage(message, type) {
    messageBox.textContent = message;   // 設定訊息文字
    messageBox.className = "message " + type;  // 設定樣式（成功=綠色，失敗=紅色）
    messageBox.style.display = "block"; // 顯示訊息區域
}