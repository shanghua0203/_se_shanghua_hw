# 任務 2：重構前端靜態檔案
## 目標
目前前端所有的東西都塞在 `index.html` 裡面，太亂了。請幫我把 HTML、CSS、JavaScript 拆開來。

## 涉及檔案
- `HW2/app/static/index.html`
- (新增) `HW2/app/static/css/style.css`
- (新增) `HW2/app/static/js/main.js`

## 執行步驟
1. 建立 `css` 與 `js` 資料夾。
2. 把 `index.html` 裡面的 `<style>` 內容剪下，貼到 `style.css` 裡。
3. 把 `index.html` 裡面的 `<script>` 內容剪下，貼到 `main.js` 裡。
4. 在 `index.html` 裡面用 `<link>` 和 `<script src="...">` 把剛才的檔案重新連線進來。

## 驗證標準
- [ ] 打開網頁時，畫面長得跟原本一模一樣，沒有跑版。
- [ ] 網頁按鈕的功能依然正常。
