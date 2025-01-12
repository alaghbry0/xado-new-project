import sqlite3
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from database.db_utils import remove_user_from_channel  # استيراد الدالة من db_utils

# وظيفة لتنفيذ المهام المجدولة
def execute_scheduled_tasks():
    """
    تنفيذ المهام المجدولة بناءً على جدول المهام.
    """
    conn = sqlite3.connect("database/database.db")
    cursor = conn.cursor()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        SELECT id, task_type, user_id FROM scheduled_tasks
        WHERE execute_at <= ? AND status = 'pending'
    """, (now,))
    tasks = cursor.fetchall()

    for task_id, task_type, user_id in tasks:
        if task_type == "remove_user":
            success = remove_user_from_channel(user_id)
            if success:
                print(f"تم تنفيذ إزالة المستخدم {user_id} بنجاح.")
        elif task_type == "first_reminder":
            send_reminder(user_id, "اشتراكك سينتهي قريبًا! لا تنسَ التجديد.")
        elif task_type == "second_reminder":
            send_reminder(user_id, "تنبيه أخير: اشتراكك سينتهي قريبًا جدًا!")

        # تحديث حالة المهمة إلى "completed"
        cursor.execute("UPDATE scheduled_tasks SET status = 'completed' WHERE id = ?", (task_id,))

    conn.commit()
    conn.close()

# وظيفة لإرسال التذكيرات (يمكن تعديلها لتتصل بـ Telegram API)
def send_reminder(user_id, message):
    """
    إرسال تذكير للمستخدم. يمكن استبدال الطباعة باستخدام Telegram Bot API.
    """
    print(f"إرسال تذكير للمستخدم {user_id}: {message}")

# إعداد الجدولة باستخدام APScheduler
def start_scheduler():
    """
    بدء تشغيل جدولة المهام باستخدام APScheduler.
    """
    scheduler = BackgroundScheduler()
    scheduler.add_job(execute_scheduled_tasks, 'interval', minutes=1)  # تنفيذ المهام المجدولة كل دقيقة
    scheduler.start()
    print("تم تشغيل جدولة المهام بنجاح.")
