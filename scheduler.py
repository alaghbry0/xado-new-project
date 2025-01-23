import logging
import asyncio
import signal
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from aiogram.exceptions import TelegramAPIError
from aiogram import Bot
from telegram_bot import send_message_to_user
from database.db_utils import remove_user_from_channel, send_message
from config import TELEGRAM_BOT_TOKEN
from db_queries import (
    get_pending_tasks,
    update_task_status,
    get_subscription,
    deactivate_subscription
)

telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN)

async def execute_scheduled_tasks(connection):
    """
    تنفيذ المهام المجدولة بناءً على جدول المهام.
    """
    try:
        tasks = await get_pending_tasks(connection)
        task_count = len(tasks)
        logging.info(f"Retrieved {task_count} pending tasks.")

        for task in tasks:
            task_id = int(task['id'])
            task_type = task['task_type']
            telegram_id = task['telegram_id']
            channel_id = task['channel_id']

            logging.info(
                f"Processing task ID: {task_id}, type: {task_type}, telegram_id: {telegram_id}, channel_id: {channel_id}"
            )

            # التحقق من صحة البيانات
            if not telegram_id or not channel_id:
                logging.warning(f"Skipping task ID {task_id} due to missing telegram_id or channel_id.")
                continue

            try:
                if task_type == "remove_user":
                    await handle_remove_user_task(connection, telegram_id, channel_id, task_id)
                elif task_type in ["first_reminder", "second_reminder"]:
                    await handle_reminder_task(connection, telegram_id, task_type, task_id, channel_id)
                else:
                    logging.warning(f"Unknown task type {task_type} for task ID {task_id}. Skipping task.")
            except Exception as task_error:
                logging.error(f"Error while processing task ID {task_id} (type: {task_type}): {task_error}")
                # تحديث حالة المهمة إلى "failed" في حال الخطأ
                await update_task_status(connection, task_id, "failed")

        logging.info("All scheduled tasks have been processed successfully.")
    except Exception as e:
        logging.error(f"Error while executing scheduled tasks: {e}")

async def handle_remove_user_task(connection, telegram_id, channel_id, task_id):
    """
    معالجة مهمة إزالة المستخدم.
    """
    try:
        logging.info(f"محاولة إزالة المستخدم {telegram_id} من القناة {channel_id}.")

        # إلغاء تفعيل الاشتراك في قاعدة البيانات
        await deactivate_subscription(connection, telegram_id, channel_id)
        logging.info(f"تم إلغاء تفعيل الاشتراك للمستخدم {telegram_id} في القناة {channel_id}.")

        # إزالة المستخدم من القناة
        removal_success = await remove_user_from_channel(connection, telegram_id, channel_id)
        if removal_success:
            logging.info(f"تمت إزالة المستخدم {telegram_id} من القناة {channel_id} بنجاح.")
        else:
            logging.warning(f"فشل إزالة المستخدم {telegram_id} من القناة {channel_id}.")

        # تحديث حالة المهمة
        await update_task_status(connection, task_id, "completed")
    except Exception as e:
        logging.error(f"خطأ أثناء معالجة مهمة إزالة المستخدم {telegram_id} من القناة {channel_id}: {e}")


async def handle_reminder_task(connection, telegram_id: int, task_type: str, task_id: int, channel_id: int):
    """
    معالجة مهمة إرسال تذكير.
    """
    try:
        logging.info(
            f"بدء معالجة مهمة التذكير: task_id={task_id}, task_type={task_type}, telegram_id={telegram_id}, channel_id={channel_id}")

        # جلب بيانات الاشتراك
        subscription = await connection.fetchrow("""
            SELECT st.name AS channel_name, s.expiry_date, s.is_active
            FROM subscription_types st
            JOIN subscriptions s ON st.channel_id = s.channel_id
            WHERE s.telegram_id = $1 AND s.channel_id = $2
        """, telegram_id, channel_id)

        if not subscription:
            logging.error(f"لم يتم العثور على بيانات القناة {channel_id} أو الاشتراك للمستخدم {telegram_id}.")
            return

        channel_name = subscription['channel_name']
        expiry_date = subscription['expiry_date']
        is_active = subscription['is_active']
        current_time = datetime.now()

        # إذا انتهى الاشتراك، قم بتحديث جميع المهام إلى "not completed"
        if not is_active or expiry_date <= current_time:
            await connection.execute("""
                UPDATE scheduled_tasks
                SET status = 'not completed'
                WHERE telegram_id = $1 AND channel_id = $2 AND status = 'pending'
            """, telegram_id, channel_id)
            logging.warning(
                f"الاشتراك للمستخدم {telegram_id} في القناة {channel_id} انتهى. تم تحديث المهام إلى 'not completed'.")
            return

        # إعداد رسالة التذكير
        if task_type == "first_reminder":
            message = f"مرحبا/nاشتراكك سينتهي في {expiry_date.strftime('%Y/%m/%d %H:%M:%S')}. يرجى تجديد الاشتراك رجاءً."
        elif task_type == "second_reminder":
            remaining_time = expiry_date - current_time
            remaining_hours = int(remaining_time.total_seconds() // 3600)
            message = f" متبقي على اشتراكك اقل من{remaining_hours} ساعة. يرجى تجديد الاشتراك رجاءً."
        else:
            logging.warning(f"نوع تذكير غير معروف: {task_type} للمهمة {task_id}.")
            return

        # إرسال الرسالة باستخدام الوظيفة الموحدة
        success = await send_message(telegram_id, message)
        if success:
            logging.info(f"تم إرسال الرسالة إلى المستخدم {telegram_id}: {message}")

            # تحديث حالة التذكير الحالي
            await update_task_status(connection, task_id, "completed")
            logging.info(f"تم تحديث حالة المهمة {task_id} إلى 'completed'.")

            # إذا كان التذكير الثاني يتم تنفيذه، قم بتحديث حالة التذكير الأول إلى 'completed'
            if task_type == "second_reminder":
                await connection.execute("""
                    UPDATE scheduled_tasks
                    SET status = 'completed'
                    WHERE telegram_id = $1 AND channel_id = $2 AND task_type = 'first_reminder' AND status = 'pending'
                """, telegram_id, channel_id)
                logging.info(f"تم تحديث حالة التذكير الأول إلى 'completed'.")
        else:
            logging.warning(f"فشل إرسال التذكير إلى المستخدم {telegram_id}.")
    except Exception as e:
        logging.error(f"خطأ أثناء معالجة مهمة التذكير للمستخدم {telegram_id} في القناة {channel_id}: {e}")


def start_scheduler(connection):
    """
    إعداد الجدولة باستخدام APScheduler لجدولة المهام المتكررة.
    """
    logging.info("بدء إعداد الجدولة")
    try:
        # إنشاء مثيل للجدولة
        scheduler = AsyncIOScheduler()

        # تعريف الوظيفة المجدولة
        async def scheduled_task_executor():
            if connection:
                await execute_scheduled_tasks(connection)
            else:
                logging.warning("لم يتم توفير اتصال بقاعدة البيانات. لن يتم تنفيذ المهام المجدولة.")

        # إضافة الوظائف المجدولة بوضوح مع فواصل زمنية محددة
        logging.info("Starting scheduled task executor job.")
        scheduler.add_job(scheduled_task_executor, 'interval', minutes=1)
        logging.info("تمت إضافة وظيفة execute_scheduled_tasks إلى الجدولة")

        # بدء الجدولة
        scheduler.start()
        logging.info("تم بدء الجدولة. سيتم تشغيل الوظيفة كل دقيقة.")

    except Exception as e:
        # تسجيل الخطأ مع إمكانية اتخاذ إجراء لاحق
        logging.error(f"حدث خطأ أثناء بدء الجدولة: {e}")
        # يمكنك إضافة إشعار أو خطوة بديلة هنا
        # send_alert("خطأ في بدء الجدولة", e)
