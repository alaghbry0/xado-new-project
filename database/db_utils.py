from db_queries import add_user, get_user, add_scheduled_task, update_subscription
from aiogram import Bot
import asyncio

from aiogram.exceptions import TelegramAPIError
import logging
from config import TELEGRAM_BOT_TOKEN, DEFAULT_CHANNEL_ID       # إعداد توكن البوت ومعرف القناة الافتراضي
from datetime import datetime, timedelta
# استيراد وظيفة الإرسال من telegram_bot
from telegram_bot import send_message_to_user
import time

telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN)

# الإعدادات الافتراضية للتذكيرات
#DEFAULT_REMINDER_SETTINGS = {
   # "subscription_duration": 30,  # عدد الأيام
    #"first_reminder": 72,  # عدد الساعات قبل انتهاء الاشتراك
    #"second_reminder": 24  # عدد الساعات قبل انتهاء الاشتراك
#}

DEFAULT_REMINDER_SETTINGS = {
    "subscription_duration": 3 / 1440,  # تحويل 3 دقائق إلى أيام (3 ÷ 1440)
    "first_reminder": 2 / 60,  # تحويل دقيقتين إلى ساعات (2 ÷ 60)
    "second_reminder": 1 / 60  # تحويل دقيقة واحدة إلى ساعات (1 ÷ 60)
}

# وظيفة لإضافة المستخدم إلى القناة
async def add_user_to_channel(user_id: int, subscription_type: str = None, channel_id: int = None):
    """
    إرسال رابط دعوة إلى المستخدم ليقوم بالانضمام إلى القناة بنفسه.
    """

    # إذا لم يتم تحديد قناة، استخدم القناة الافتراضية
    if not channel_id:
        channel_id = DEFAULT_CHANNEL_ID

    try:
        # محاولة إزالة الحظر إذا كان المستخدم محظورًا
        try:
            await telegram_bot.unban_chat_member(chat_id=channel_id, user_id=user_id)
            logging.info(f"تم التحقق من أن المستخدم {user_id} ليس محظورًا.")
        except TelegramAPIError as unban_error:
            logging.warning(f"لم يتمكن من إزالة الحظر عن المستخدم {user_id} في القناة {channel_id}: {unban_error}")

        # الحصول على اسم القناة (يمكن التعديل هنا لتحديد الاسم تلقائيًا)
        channel_name = "القناة"  # يمكن تحديث هذا الجزء لجلب الاسم تلقائيًا

        # إنشاء رابط دعوة مخصص لمستخدم واحد
        invite_link = await telegram_bot.create_chat_invite_link(
            chat_id=channel_id,
            member_limit=1,
            expire_date=None  # الرابط بدون تاريخ انتهاء
        )

        # إرسال رابط الدعوة عبر دردشة البوت
        await telegram_bot.send_message(
            chat_id=user_id,
            text=f"مرحبًا! يمكنك الانضمام إلى قناة {channel_name} عبر الرابط التالي:\n{invite_link.invite_link}"
        )
        logging.info(f"تم إرسال رابط الدعوة إلى المستخدم {user_id}.")
        return True

    except TelegramAPIError as invite_error:
        logging.error(
            f"خطأ أثناء إنشاء أو إرسال رابط الدعوة للمستخدم {user_id} إلى القناة {channel_id}: {invite_error}"
        )
        return False
    except Exception as e:
        logging.error(f"خطأ غير متوقع أثناء إرسال رابط الدعوة للمستخدم {user_id} إلى القناة {channel_id}: {e}")
        return False

# وظيفة جدولة التذكيرات
async def schedule_reminders(connection, user_id: int, expiry_date: datetime, reminder_settings=None):
    """
    جدولة التذكيرات بناءً على تاريخ انتهاء الاشتراك.
    """
    try:
        # إعدادات التذكير الافتراضية للتطوير والاختبار
        settings = reminder_settings or {
            "first_reminder": 2,  # أول تذكير قبل دقيقتين
            "second_reminder": 1  # ثاني تذكير قبل دقيقة
        }

        # التأكد من أن expiry_date هو كائن datetime
        if isinstance(expiry_date, str):
            expiry_date = datetime.strptime(expiry_date, "%Y-%m-%d %H:%M:%S")
        logging.info(f"expiry_date is {expiry_date}, type: {type(expiry_date)}")

        # حذف جميع التذكيرات القديمة للمستخدم
        deleted_count = await connection.execute("""
            DELETE FROM scheduled_tasks
            WHERE user_id = $1 AND task_type IN ('first_reminder', 'second_reminder')
        """, user_id)
        logging.info(f"Deleted old reminder tasks for user_id: {user_id}, count: {deleted_count}")

        # حساب الأوقات الجديدة للتذكيرات
        first_reminder_time = expiry_date - timedelta(minutes=settings["first_reminder"])
        second_reminder_time = expiry_date - timedelta(minutes=settings["second_reminder"])

        # إضافة المهام الجديدة إلى قاعدة البيانات
        first_task_result = await add_scheduled_task(connection, "first_reminder", user_id, first_reminder_time)
        logging.info(f"Added first reminder task for user_id: {user_id}, result: {first_task_result}")

        second_task_result = await add_scheduled_task(connection, "second_reminder", user_id, second_reminder_time)
        logging.info(f"Added second reminder task for user_id: {user_id}, result: {second_task_result}")

        # حذف التذكيرات القديمة التي انتهت صلاحيتها منذ أكثر من 48 ساعة
        cleaned_count = await connection.execute("""
            DELETE FROM scheduled_tasks
            WHERE status = 'completed' AND execute_at <= NOW() - INTERVAL '48 HOURS'
        """)
        logging.info(f"Cleaned up completed tasks older than 48 hours, count: {cleaned_count}")

        logging.info(f"Finished scheduling reminders for user_id: {user_id}.")
    except Exception as e:
        logging.error(f"Error in schedule_reminders for user_id: {user_id}: {e}")


# وظيفة جدولة إزالة المستخدم
async def schedule_remove_user(connection, user_id: int, expiry_date: datetime):
    try:
        # حذف أي مهام إزالة قديمة قبل إضافة المهمة الجديدة
        await connection.execute("""
            DELETE FROM scheduled_tasks
            WHERE user_id = $1 AND task_type = 'remove_user';
        """, user_id)

        # حساب وقت الإزالة الجديد
        remove_time = expiry_date + timedelta(seconds=1)

        # إضافة المهمة الجديدة إلى قاعدة البيانات
        await add_scheduled_task(connection, "remove_user", user_id, remove_time)

        # حذف التذكيرات القديمة التي انتهت صلاحيتها منذ أكثر من 48 ساعة
        await connection.execute("""
            DELETE FROM scheduled_tasks
            WHERE status = 'completed' AND execute_at <= NOW() - INTERVAL '48 HOURS';
        """)

        logging.info(f"تم جدولة إزالة المستخدم {user_id} بعد انتهاء الاشتراك.")
    except Exception as e:
        logging.error(f"خطأ أثناء جدولة إزالة المستخدم {user_id}: {e}")


# وظيفة لإزالة المستخدم من القناة باستخدام Telegram Bot API
async def remove_user_from_channel(user_id: int, channel_id: int = None):
    try:
        # استخدام DEFAULT_CHANNEL_ID إذا لم يتم تمرير channel_id
        if not channel_id:
            channel_id = DEFAULT_CHANNEL_ID
            logging.info(f"لم يتم تقديم channel_id. سيتم استخدام القناة الافتراضية: {DEFAULT_CHANNEL_ID}.")

        # محاولة إزالة المستخدم من القناة
        await telegram_bot.ban_chat_member(chat_id=channel_id, user_id=user_id)
        logging.info(f"تمت إزالة المستخدم {user_id} من القناة {channel_id}.")
        return True
    except TelegramAPIError as e:
        logging.error(f"فشل إزالة المستخدم {user_id} من القناة {channel_id}: {e}")
        return False
    except Exception as e:
        logging.error(f"خطأ غير متوقع أثناء إزالة المستخدم {user_id} من القناة {channel_id}: {e}")
        return False



async def update_all_subscriptions(connection):
    """
    تحديث جميع الاشتراكات بناءً على تاريخ انتهاء الصلاحية.
    يتم تعطيل الاشتراكات التي انتهت صلاحيتها.
    """
    try:
        # جلب جميع الاشتراكات النشطة
        subscriptions = await connection.fetch("""
            SELECT id, user_id, expiry_date
            FROM subscriptions
            WHERE is_active = TRUE
        """)
        logging.info(f"Found {len(subscriptions)} active subscriptions to check.")

        # الوقت الحالي
        now = datetime.now()

        # تعطيل الاشتراكات التي انتهت صلاحيتها
        for subscription in subscriptions:
            if subscription['expiry_date'] < now:
                await connection.execute("""
                    UPDATE subscriptions
                    SET is_active = FALSE
                    WHERE id = $1
                """, subscription['id'])
                logging.info(f"Subscription {subscription['id']} set to inactive.")

        logging.info("Completed updating all subscriptions.")
    except Exception as e:
        logging.error(f"Error in update_all_subscriptions: {e}")



