# Oracle DDL 匯出工具

此 Python 腳本用於匯出 Oracle 資料庫中自指定日期以來修改過的物件（ 表和儲存過程 ）的 DDL（ 資料定義語言 ）語句。它使用 `oracledb` 庫連接到 Oracle 資料庫，並利用 `DBMS_METADATA` 來生成 DDL 語句。

## 功能

- 匯出指定日期後修改的表和儲存過程的 DDL 語句。
- 支援通過 JSON 設定檔配置 Oracle 連線設定。
- 可選擇按天數或特定起始日期篩選物件。
- 為表生成 `.sql` 檔案，為儲存過程生成 `.prc` 檔案。
- 支援通過命令列參數進行配置。

## 環境需求

- Python 3.11
- `oracledb` 庫（ 可通過 `pip install oracledb` 安裝 ）
- Oracle 資料庫訪問權限
- 一個 JSON 設定檔（ 預設為 `oracle_config.json` ），格式如下：

```json
{
    "username": "你的用戶名",
    "password": "你的密碼",
    "dsn": "你的資料庫連線字串"
}
```

## 安裝

1. 安裝 Python 3.11。
2. 安裝 `oracledb` 庫：

   ```bash
   pip install oracledb
   ```

3. 準備 `oracle_config.json` 檔案，填入正確的 Oracle 資料庫連線資訊。

## 使用方法

運行腳本時，可通過命令列參數指定選項：

```bash
python script.py [--output OUTPUT_DIR] [--days DAYS] [--fromdate YYYYMMDD] [--config CONFIG_PATH]
```

### 參數說明

- `--output`, `-o`：輸出 DDL 檔案的資料夾（ 預設：`./output/ddl/YYYYMMDD` ）。
- `--days`, `-d`：從幾天前開始匯出修改的物件（ 預設：1 天 ）。
- `--fromdate`, `-f`：指定起始日期，格式為 `YYYYMMDD`（ 例如：20250101 ）。
- `--config`, `-c`：Oracle 設定檔路徑（ 預設：`oracle_config.json` ）。

### 示例

匯出過去 3 天內修改的物件：

```bash
python script.py --days 3
```

匯出 2025 年 1 月 1 日起修改的物件：

```bash
python script.py --fromdate 20250101
```

指定輸出資料夾和設定檔：

```bash
python script.py --output ./my_output --config my_config.json
```


### 輸出

- 腳本將在指定的輸出資料夾中生成 DDL 檔案：
  - 表：以 `.sql` 為副檔名。
  - 儲存過程：以 `.prc` 為副檔名。
- 控制台會顯示查找到的物件數量及每個物件的匯出狀態。

## 注意事項

- 確保 `oracle_config.json` 中的連線資訊正確，且具有足夠的資料庫權限。
- 日期格式必須為 `YYYYMMDD`，否則會報錯。
- 若無法取得某物件的 DDL，腳本會在控制台顯示警告訊息。
- 輸出的 DDL 檔案使用 UTF-8 編碼。

## 錯誤處理

- 若無法讀取設定檔，腳本會顯示錯誤訊息並退出。
- 若連線到資料庫失敗或查詢過程中發生錯誤，腳本會顯示錯誤訊息並退出。
