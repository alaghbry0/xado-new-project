from db_queries import add_user, add_scheduled_task
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
# وظيفة لإضافة المستخدم إلى القناة
async def add_user_to_channel(user_id: int, subscription_type: str = None, channel_id: int = None):
    """
    إرسال رابط دعوة إلى المستخدم ليقوم بالانضمام إلى القناة بنفسه.
    """
    if not channel_id:
        channel_id = DEFAULT_CHANNEL_ID

    try:
        # محاولة إزالة الحظر إذا كان المستخدم محظورًا
        try:
            await telegram_bot.unban_chat_member(chat_id=channel_id, user_id=user_id)
            logging.info(f"تم التحقق من أن المستخدم {user_id} ليس محظورًا.")
        except TelegramAPIError as unban_error:
            logging.warning(f"لم يتمكن من إزالة الحظر عن المستخدم {user_id} في القناة {channel_id}: {unban_error}")

        # الحصول على اسم القناة من القاموس أو استخدام طريقة get_chat
        channel_name = "القناة"  # أو استخدام طريقة معينة لاستخراج الاسم

        # إنشاء رابط دعوة
        invite_link = await telegram_bot.create_chat_invite_link(
            chat_id=channel_id,
            member_limit=1,
            expire_date=None
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
            f"خطأ أثناء إنشاء أو إرسال رابط الدعوة للمستخدم {user_id} إلى القناة {channel_id}: {invite_error}")
        return False
    except Exception as e:
        logging.error(f"خطأ غير متوقع أثناء إرسال رابط الدعوة للمستخدم {user_id} إلى القناة {channel_id}: {e}")
        return False

# وظيفة جدولة التذكيرات
async def schedule_reminders(connection, user_id: int, subscription_type: str, expiry_date: datetime, reminder_settings=None):
    """
    تقوم بجدولة تذكيرين للمستخدم قبل انتهاء اشتراكه.
    يمكن تخصيص أوقات التذكيرات عبر reminder_settings.
    """
    try:
        # استخدام الإعدادات الافتراضية أو المخصصة
        settings = reminder_settings if reminder_settings else {
            "first_reminder": 72,  # عدد الساعات قبل انتهاء الاشتراك
            "second_reminder": 24  # عدد الساعات قبل انتهاء الاشتراك
        }

        # التأكد من أن expiry_date هو كائن datetime
        if isinstance(expiry_date, str):
            logging.info(f"Parsing expiry_date from string: {expiry_date}")
            expiry_date = datetime.strptime(expiry_date, "%Y-%m-%d %H:%M:%S")
            logging.info(f"Expiry date after parsing (datetime object): {expiry_date}")

        # حساب أوقات التذكيرات
        first_reminder_time = expiry_date - timedelta(hours=settings["first_reminder"])
        second_reminder_time = expiry_date - timedelta(hours=settings["second_reminder"])

        # استخدام استعلامات db_queries لإضافة المهام إلى قاعدة البيانات
        await add_scheduled_task(connection, "first_reminder", user_id, first_reminder_time)
        logging.info(f"First reminder scheduled for user {user_id} at {first_reminder_time}")

        await add_scheduled_task(connection, "second_reminder", user_id, second_reminder_time)
        logging.info(f"Second reminder scheduled for user {user_id} at {second_reminder_time}")

        logging.info(f"تم جدولة التذكيرات للمستخدم {user_id}.")
    except Exception as e:
        logging.error(f"خطأ أثناء جدولة التذكيرات: {e}")


# وظيفة جدولة إزالة المستخدم
async def schedule_remove_user(connection, user_id: int, expiry_date: datetime):
    """
    جدولة إزالة المستخدم من القناة بعد انتهاء اشتراكه مباشرة.
    """
    try:
        # التأكد من أن expiry_date هو كائن datetime
        if isinstance(expiry_date, str):
            logging.info(f"Parsing expiry_date from string: {expiry_date}")
            expiry_date = datetime.strptime(expiry_date, "%Y-%m-%d %H:%M:%S")
            logging.info(f"Expiry date after parsing (datetime object): {expiry_date}")

        # حساب وقت الإزالة
        remove_time = expiry_date + timedelta(seconds=1)
        logging.info(f"Calculated remove_time as {remove_time}.")

        # استخدام db_queries لإضافة المهمة إلى قاعدة البيانات
        await add_scheduled_task(connection, "remove_user", user_id, remove_time)
        logging.info(f"User removal scheduled at {remove_time} for user {user_id}.")
    except Exception as e:
        logging.error(f"Error scheduling user removal: {e}")
# وظيفة لإزالة المستخدم من القناة باستخدام Telegram Bot API
async def remove_user_from_channel(user_id: int, channel_id: int = None):
    """
    إزالة المستخدم من القناة باستخدام aiogram.
    """
    try:
        # إذا لم يتم تمرير channel_id، نستخدم القناة الافتراضية
        if not channel_id:
            channel_id = DEFAULT_CHANNEL_ID
            logging.info(f"No channel_id provided. Using default channel {DEFAULT_CHANNEL_ID}.")

        # إزالة المستخدم من القناة
        await telegram_bot.ban_chat_member(chat_id=channel_id, user_id=user_id)
        logging.info(f"User {user_id} was removed from channel {channel_id}.")
        return True
    except TelegramAPIError as e:
        logging.error(f"Failed to remove user {user_id} from channel {channel_id}: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error while removing user {user_id} from channel {channel_id}: {e}")
        return False
