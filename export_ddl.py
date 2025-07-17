import argparse
import json
import os
from datetime import datetime, timedelta

import oracledb


def load_oracle_config(config_path="oracle_config.json"):
    """
    讀取 Oracle 設定檔
    """

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    return config["username"], config["password"], config["dsn"]


def get_target_date(days_diff=None, from_date_str=None):
    """
    計算查詢起始時間
    """

    if from_date_str:
        try:
            from_date = datetime.strptime(from_date_str, "%Y%m%d")
        except ValueError:
            raise ValueError("指定日期格式錯誤，必須為 yyyyMMdd")
        return from_date
    if days_diff is None:
        days_diff = 1
    return datetime.now() - timedelta(days=days_diff)


def configure_metadata(cursor):
    """
    設定 DBMS_METADATA 輸出參數
    """

    cursor.execute("BEGIN DBMS_METADATA.set_transform_param(DBMS_METADATA.session_transform, 'STORAGE', false); END;")
    cursor.execute(
        "BEGIN DBMS_METADATA.set_transform_param(DBMS_METADATA.session_transform, 'TABLESPACE', false); END;"
    )
    cursor.execute(
        "BEGIN DBMS_METADATA.set_transform_param(DBMS_METADATA.session_transform, 'SEGMENT_ATTRIBUTES', false); END;"
    )
    cursor.execute(
        "BEGIN DBMS_METADATA.set_transform_param(DBMS_METADATA.session_transform, 'CONSTRAINTS', true); END;"
    )
    cursor.execute(
        "BEGIN DBMS_METADATA.set_transform_param(DBMS_METADATA.session_transform, 'REF_CONSTRAINTS', true); END;"
    )
    cursor.execute(
        "BEGIN DBMS_METADATA.set_transform_param(DBMS_METADATA.session_transform, 'EMIT_SCHEMA', false); END;"
    )


def load_program_code_mapping(cursor):
    """
    載入 PROGRAM_CODE_TABLE 全表，建立 { table_name.lower(): [program_codes] } 的對應字典
    """

    cursor.execute(
        """
        SELECT LOWER(table_name), UPPER(program_code)
        FROM PROGRAM_CODE_TABLE
    """
    )
    mapping = {}
    for table_name, program_code in cursor.fetchall():
        mapping.setdefault(table_name, []).append(program_code)
    return mapping


def get_object_program_codes(mapping, obj_name):
    """
    從記憶體 dict 快速查詢 program_code
    """

    return mapping.get(obj_name.lower(), [])


def export_ddl(conn, output_dir, target_date):
    """
    匯出 DDL
    """

    cursor = conn.cursor()
    configure_metadata(cursor)

    # 預先載入所有 program_code 對應
    program_code_mapping = load_program_code_mapping(cursor)

    cursor.execute(
        """
        SELECT object_name, object_type, last_ddl_time
        FROM user_objects
        WHERE object_type IN ('TABLE', 'PROCEDURE', 'FUNCTION')
          AND last_ddl_time >= :ddl_time
        ORDER BY last_ddl_time DESC
    """,
        [target_date],
    )

    objects = cursor.fetchall()
    print(f"🔍 找到 {len(objects)} 個物件（{target_date.date()} 起有異動）")

    for obj_name, obj_type, ddl_time in objects:
        ddl_cursor = conn.cursor()
        ddl_cursor.execute(f"SELECT DBMS_METADATA.GET_DDL('{obj_type}', '{obj_name}') FROM dual")
        ddl_result = ddl_cursor.fetchone()

        if ddl_result and ddl_result[0]:
            ddl_text = ddl_result[0].read() if hasattr(ddl_result[0], "read") else ddl_result[0]
            ext = {
                "TABLE": ".sql",
                "PROCEDURE": ".prc",
                "FUNCTION": ".fnc",
            }.get(obj_type, ".sql")

            program_codes = get_object_program_codes(program_code_mapping, obj_name)

            output_paths = (
                [os.path.join(output_dir, "None")]
                if not program_codes
                else [os.path.join(output_dir, code[:5]) for code in program_codes]
            )

            for path in output_paths:
                os.makedirs(path, exist_ok=True)
                file_path = os.path.join(path, f"{obj_name}{ext}")
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(ddl_text)

                print(f"✅ [{obj_type}] {obj_name} → {file_path}")
        else:
            print(f"⚠️ 無法取得 {obj_type} 的 DDL：{obj_name}")
        ddl_cursor.close()

    cursor.close()


def main():
    today_str = datetime.now().strftime("%Y%m%d")
    default_output_path = os.path.join("./output/ExportChange", today_str)

    parser = argparse.ArgumentParser(description="Oracle DDL 匯出工具")
    parser.add_argument(
        "--output", "-o", type=str, default=default_output_path, help=f"輸出資料夾（預設={default_output_path}）"
    )
    parser.add_argument("--days", "-d", type=int, help="從幾天前開始計算（預設 1 天）", default=None)
    parser.add_argument("--fromdate", "-f", type=str, help="指定起始日期（格式 yyyyMMdd）")
    parser.add_argument("--config", "-c", type=str, default="oracle_config.json", help="Oracle 設定檔路徑")

    args = parser.parse_args()
    os.makedirs(args.output, exist_ok=True)

    try:
        username, password, dsn = load_oracle_config(args.config)
    except Exception as e:
        print(f"❌ 無法讀取設定檔：{e}")
        return

    try:
        target_date = get_target_date(args.days, args.fromdate)
    except Exception as e:
        print(f"❌ 日期格式錯誤：{e}")
        return

    try:
        conn = oracledb.connect(user=username, password=password, dsn=dsn)
        export_ddl(conn, args.output, target_date)
        conn.close()
    except Exception as e:
        print(f"❌ 連線或匯出錯誤：{e}")


if __name__ == "__main__":
    main()
