import aiosqlite

# وظيفة لجلب هيكل قاعدة البيانات
async def get_database_structure(db_path):
    async with aiosqlite.connect(db_path) as conn:
        cursor = await conn.cursor()

        # الحصول على أسماء الجداول
        await cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = await cursor.fetchall()

        print("Tables in the database:")
        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")

            # الحصول على هيكل الجدول
            await cursor.execute(f"PRAGMA table_info('{table_name}');")
            columns = await cursor.fetchall()

            print("Columns:")
            for column in columns:
                col_id, col_name, col_type, not_null, default_val, pk = column
                print(f"  - {col_name} ({col_type}) {'NOT NULL' if not_null else ''} {'PRIMARY KEY' if pk else ''}")

            # عرض العلاقات (إذا وجدت)
            await cursor.execute(f"PRAGMA foreign_key_list('{table_name}');")
            foreign_keys = await cursor.fetchall()
            if foreign_keys:
                print("Foreign Keys:")
                for fk in foreign_keys:
                    id_, seq, table, from_col, to_col, on_update, on_delete, match = fk
                    print(f"  - {from_col} -> {table}.{to_col}")
