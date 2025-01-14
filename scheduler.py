from models import db, Subscription, ScheduledTask
import logging
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database.db_utils import remove_user_from_channel

from aiogram import Bot


# وظيفة لتنفيذ المهام المجدولة
def execute_scheduled_tasks():
    """
    تنفيذ المهام المجدولة بناءً على جدول المهام.
    """
    logging.info("Starting scheduled tasks execution")
    try:
        # الحصول على المهام المجدولة الجاهزة للتنفيذ
        now = datetime.now()
        tasks = ScheduledTask.query.filter(ScheduledTask.execute_at <= now, ScheduledTask.status == "pending").all()

        logging.info(f"Found {len(tasks)} tasks to execute.")
        for task in tasks:
            logging.info(f"Executing task {task.id}: {task.task_type} for user {task.user_id}")

            if task.task_type == "remove_user":
                subscription = Subscription.query.filter_by(user_id=task.user_id, is_active=True).first()
                if subscription:
                    success = remove_user_from_channel(task.user_id, subscription.subscription_type)
                    if success:
                        subscription.is_active = False
                        db.session.commit()
                        logging.info(f"تم تنفيذ إزالة المستخدم {task.user_id} بنجاح.")
            elif task.task_type == "first_reminder":
                send_reminder(task.user_id, "اشتراكك سينتهي قريبًا! لا تنسَ التجديد.")
            elif task.task_type == "second_reminder":
                send_reminder(task.user_id, "تنبيه أخير: اشتراكك سينتهي قريبًا جدًا!")

            # تحديث حالة المهمة إلى "completed"
            task.status = "completed"
            db.session.commit()

        logging.info("تم تنفيذ جميع المهام المجدولة بنجاح.")
    except Exception as e:
        logging.error(f"خطأ أثناء تنفيذ المهام المجدولة: {e}")


# وظيفة إرسال رسالة تذكير للمستخدم
def send_reminder(user_id, message):
    """
    إرسال رسالة تذكير للمستخدم.
    :param user_id: معرف المستخدم في تيليجرام.
    :param message: نص الرسالة التذكيرية.
    """
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    try:
        bot.send_message(chat_id=user_id, text=message)
        logging.info(f"تم إرسال التذكير إلى المستخدم {user_id}: {message}")
    except Exception as e:
        logging.error(f"خطأ أثناء إرسال التذكير إلى المستخدم {user_id}: {e}")


# إعداد الجدولة باستخدام APScheduler
def start_scheduler():
    """
    بدء تشغيل جدولة المهام باستخدام APScheduler.
    """
    scheduler = AsyncIOScheduler()
    scheduler.add_job(execute_scheduled_tasks, 'interval', minutes=1)  # جدولة كل دقيقة
    scheduler.start()
    logging.info("تم تشغيل جدولة المهام بنجاح.")
