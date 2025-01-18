import logging
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from aiogram.exceptions import TelegramAPIError
from aiogram import Bot
from telegram_bot import send_message_to_user
from database.db_utils import remove_user_from_channel, update_all_subscriptions
from config import TELEGRAM_BOT_TOKEN, DEFAULT_CHANNEL_ID
from db_queries import (
    get_pending_tasks,
    update_task_status,
    get_subscription,
    deactivate_subscription
)

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
    logging.info("execute_scheduled_tasks was triggered")
    logging.info("Starting execution of scheduled tasks")
    try:
        # الحصول على المهام المجدولة الجاهزة للتنفيذ
        tasks = await get_pending_tasks(connection)
        logging.info(f"Retrieved {len(tasks)} pending tasks: {tasks}")

        for task in tasks:
            logging.info(f"Processing task ID: {task['id']}, type: {task['task_type']}, user_id: {task['user_id']}")

            if task['task_type'] == "remove_user":
                logging.info("Attempting to remove user from channel")
                # قم بإزالة المستخدم عند انتهاء الاشتراك
                try:
                    subscription = await get_subscription(connection, task['user_id'])
                    if subscription:
                        logging.info(f"Found subscription for user {task['user_id']}: {subscription}")

                        # تحديث حالة الاشتراك إلى غير نشط
                        await deactivate_subscription(connection, task['user_id'])
                        logging.info(f"Subscription {subscription['id']} set to inactive.")

                        # إزالة المستخدم فعلياً من القناة
                        logging.info("Calling remove_user_from_channel...")
                        removal_success = await remove_user_from_channel(task['user_id'], DEFAULT_CHANNEL_ID)
                        if removal_success:
                            logging.info(f"User {task['user_id']} was successfully removed from the channel.")
                        else:
                            logging.warning(f"Failed to remove user {task['user_id']} from the channel.")

                        # تحديث حالة المهمة
                        await update_task_status(connection, task['id'], "completed")
                except Exception as e:
                    logging.error(f"Error while processing remove_user task {task['id']}: {e}")

            elif task['task_type'] in ["first_reminder", "second_reminder"]:
                logging.info("Attempting to send reminder")
                try:
                    # إرسال التذكيرات
                    message = (
                        "اشتراكك سينتهي قريبًا! لا تنسَ التجديد."
                        if task['task_type'] == "first_reminder"
                        else "اشتراكك سينتهي قريبًا جدًا! لا تنسَ التجديد."
                    )
                    logging.info(f"Calling send_reminder with message: {message}")
                    await send_reminder(task['user_id'], message)
                    logging.info(f"Reminder sent successfully to user {task['user_id']}.")
                    # تحديث حالة المهمة
                    await update_task_status(connection, task['id'], "completed")
                except Exception as e:
                    logging.error(f"Error while sending reminder for task {task['id']}: {e}")

        logging.info("All scheduled tasks have been processed successfully.")
    except Exception as e:
        logging.error(f"Error while executing scheduled tasks: {e}")


def start_scheduler(connection):
    """
    يبدأ إعداد جدولة المهام باستخدام APScheduler.

    تضيف هذه الدالة وظيفتين مجدولتين:
    - واحدة تتحقق من المهام المجدولة كل 5 ثوانٍ.
    - أخرى تحدث الاشتراكات كل ساعة.

    يتم تسجيل أي أخطاء أثناء الإعداد.
    """
    logging.info("Starting scheduler setup.")
    try:
        # إنشاء الجدولة
        scheduler = AsyncIOScheduler()

        # تعريف الوظائف المجدولة بشكل واضح
        async def scheduled_task_executor():
            await execute_scheduled_tasks(connection)

        async def scheduled_subscription_updater():
            await update_all_subscriptions(connection)

        # إضافة الوظائف المجدولة إلى الجدولة
        scheduler.add_job(scheduled_task_executor, 'interval', minutes=1)
        logging.info("Added execute_scheduled_tasks to the scheduler")

        scheduler.add_job(scheduled_subscription_updater, 'interval', minutes=1)
        logging.info("Added update_all_subscriptions to the scheduler")

        # بدء الجدولة
        scheduler.start()
        logging.info("Scheduler has been started")

    except Exception as e:
        # تسجيل الخطأ مع إمكانية اتخاذ إجراء إضافي إذا لزم الأمر
        logging.error(f"Error starting scheduler: {e}")
        # إذا كنت تستخدم خدمة مراقبة، يمكن إرسال الإشعارات هنا:
        # monitor_service.notify("Scheduler initialization failed", e)
