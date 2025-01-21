import sqlite3

def create_database():
    conn = sqlite3.connect("database/database.db")
    cursor = conn.cursor()

    # إنشاء جدول المستخدمين
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            full_name TEXT
        )
    """)

    # إنشاء جدول الاشتراكات
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subscription_type TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            is_app.pyBOOLEAN DEFAULT TRUE,
            reminders_sent INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)

    # إنشاء جدول المهام المجدولة
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_type TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            execute_at DATETIME NOT NULL,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()
    print("تم إنشاء جميع الجداول بنجاح.")

if __name__ == "__main__":
    create_database()
