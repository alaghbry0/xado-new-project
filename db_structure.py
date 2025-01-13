import sqlite3


def get_database_structure(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # الحصول على أسماء الجداول
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    print("Tables in the database:")
    for table in tables:
        table_name = table[0]
        print(f"\nTable: {table_name}")

        # الحصول على هيكل الجدول
        cursor.execute(f"PRAGMA table_info('{table_name}');")
        columns = cursor.fetchall()

        print("Columns:")
        for column in columns:
            col_id, col_name, col_type, not_null, default_val, pk = column
            print(f"  - {col_name} ({col_type}) {'NOT NULL' if not_null else ''} {'PRIMARY KEY' if pk else ''}")

        # عرض العلاقات (إذا وجدت)
        cursor.execute(f"PRAGMA foreign_key_list('{table_name}');")
        foreign_keys = cursor.fetchall()
        if foreign_keys:
            print("Foreign Keys:")
            for fk in foreign_keys:
                id_, seq, table, from_col, to_col, on_update, on_delete, match = fk
                print(f"  - {from_col} -> {table}.{to_col}")

    conn.close()


# استدعاء الوظيفة
get_database_structure("database/database.db")
