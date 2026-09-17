# 任務 3：導入 Alembic 進行資料庫遷移管理
## 目標
為了以後新增資料庫欄位時不用刪除舊資料，請幫我在專案中加入 Alembic。

## 涉及檔案
- `HW2/requirements.txt`
- `HW2/alembic.ini` (新增)
- `HW2/alembic/` (新增)

## 執行步驟
1. 在 `requirements.txt` 新增 `alembic`。
2. 在 `HW2` 目錄下執行 `alembic init alembic` 來建立基礎設定檔。
3. 修改 `alembic/env.py`，把 `HW2/app/models.py` 裡面的 `Base` 引入，讓 Alembic 知道我們的資料表長怎樣。
4. 修改 `alembic.ini`，把 `sqlalchemy.url` 指向正確的資料庫路徑。
5. 幫我生成第一個 migration script (初始版本)。

## 驗證標準
- [ ] 執行 `alembic upgrade head` 不會報錯。
- [ ] 資料表結構與原本 `models.py` 定義的一致。
