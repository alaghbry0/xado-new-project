import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from db_queries import get_pending_tasks, update_task_status
from config import TELEGRAM_BOT_TOKEN, DEFAULT_CHANNEL_ID
telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN)

async def send_reminder(user_id: int, message: str):

    """
    إرسال رسالة تذكير للمستخدم.
    """
    try:
        await telegram_bot.send_message(chat_id=user_id, text=message)

        logging.info(f"تم إرسال التذكير إلى المستخدم {user_id}: {message}")
    except Exception as e:
        logging.error(f"خطأ أثناء إرسال التذكير إلى المستخدم {user_id}: {e}")


async def execute_scheduled_tasks(connection):
    """
    تنفيذ المهام المجدولة بناءً على جدول المهام.
    """
    logging.info("Starting scheduled tasks execution")
    try:
        # الحصول على المهام المجدولة الجاهزة للتنفيذ
        now = datetime.now()
        tasks = await get_pending_tasks(connection)

        logging.info(f"Found {len(tasks)} tasks to execute.")
        for task in tasks:
            logging.info(f"Executing task {task['id']}: {task['task_type']} for user {task['user_id']}")

            if task['task_type'] == "remove_user":
                # المنطق لإزالة المستخدم من القناة
                success = await remove_user_from_channel(telegram_bot, task['user_id'], DEFAULT_CHANNEL_ID)

                if success:
                    await update_task_status(connection, task['id'], "completed")
                    logging.info(f"تم تنفيذ إزالة المستخدم {task['user_id']} بنجاح.")
            elif task['task_type'] == "first_reminder":
                await telegram_bot.send_message(chat_id=user_id, text="اشتراكك سينتهي قريبًا! لا تنسَ التجديد.")
                await update_task_status(connection, task['id'], "completed")
            elif task['task_type'] == "second_reminder":
                await telegram_bot.send_message(chat_id=user_id, text="اشتراكك سينتهي قريبًا! لا تنسَ التجديد.")
                await update_task_status(connection, task['id'], "completed")

        logging.info("تم تنفيذ جميع المهام المجدولة بنجاح.")
    except Exception as e:
        logging.error(f"خطأ أثناء تنفيذ المهام المجدولة: {e}")


def start_scheduler(connection):
    """
    بدء تشغيل جدولة المهام باستخدام APScheduler.
    """
    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: execute_scheduled_tasks(connection), 'interval', minutes=1)
    scheduler.start()
    logging.info("تم تشغيل جدولة المهام بنجاح.")
