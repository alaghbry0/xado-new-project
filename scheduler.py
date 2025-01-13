import aiosqlite
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database.db_utils import remove_user_from_channel, TELEGRAM_BOT_TOKEN

from telegram_bot import send_message_to_user  # وظيفة إرسال التذكيرات
from aiogram import Bot


# وظيفة لتنفيذ المهام المجدولة
async def execute_scheduled_tasks():
    """
    تنفيذ المهام المجدولة بناءً على جدول المهام.
    """
    print("Starting scheduled tasks execution")
    try:
        async with aiosqlite.connect("database/database.db") as conn:
            cursor = await conn.cursor()

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await cursor.execute("""
                SELECT id, task_type, user_id FROM scheduled_tasks
                WHERE execute_at <= ? AND status = 'pending'
            """, (now,))
            tasks = await cursor.fetchall()

            print(f"Found {len(tasks)} tasks to execute.")
            for task_id, task_type, user_id in tasks:
                print(f"Executing task {task_id}: {task_type} for user {user_id}")

                if task_type == "remove_user":
                    print(f"Calling remove_user_from_channel for user {user_id}")
                    success = await remove_user_from_channel(user_id)
                    if success:
                        print(f"تم تنفيذ إزالة المستخدم {user_id} بنجاح.")
                elif task_type == "first_reminder":
                    print(f"Calling send_reminder for user {user_id} with first reminder message")
                    await send_message_to_user(user_id, "اشتراكك سينتهي قريبًا! لا تنسَ التجديد.")
                elif task_type == "second_reminder":
                    print(f"Calling send_reminder for user {user_id} with second reminder message")
                    await send_message_to_user(user_id, "تنبيه أخير: اشتراكك سينتهي قريبًا جدًا!")

                # تحديث حالة المهمة إلى "completed"
                await cursor.execute("UPDATE scheduled_tasks SET status = 'completed' WHERE id = ?", (task_id,))

            await conn.commit()
    except Exception as e:
        print(f"خطأ أثناء تنفيذ المهام المجدولة: {e}")


# وظيفة إرسال رسالة تذكير للمستخدم
async def send_reminder(user_id, message):
    """
    إرسال رسالة تذكير للمستخدم.
    :param user_id: معرف المستخدم في تيليجرام.
    :param message: نص الرسالة التذكيرية.
    """
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    try:
        await bot.send_message(chat_id=user_id, text=message)
        print(f"تم إرسال التذكير إلى المستخدم {user_id}: {message}")
    except Exception as e:
        print(f"خطأ أثناء إرسال التذكير إلى المستخدم {user_id}: {e}")
    finally:
        await bot.close()


# إعداد الجدولة باستخدام APScheduler
def start_scheduler():
    """
    بدء تشغيل جدولة المهام باستخدام APScheduler.
    """
    scheduler = AsyncIOScheduler()
    scheduler.add_job(execute_scheduled_tasks, 'interval', minutes=1)  # تنفيذ المهام المجدولة كل دقيقة
    scheduler.start()
    print("تم تشغيل جدولة المهام بنجاح.")
