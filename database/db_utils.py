from models import ScheduledTask
import logging
from database.init import db

from config import TELEGRAM_BOT_TOKEN, DEFAULT_CHANNEL_ID       # إعداد توكن البوت ومعرف القناة الافتراضي
from datetime import datetime, timedelta
from telegram import Bot
from sqlalchemy.exc import OperationalError
# استيراد وظيفة الإرسال من telegram_bot
from telegram_bot import send_message_to_user
import time

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
async def add_user_to_channel(user_id, subscription_type=None, channel_id=None):
    """
    وظيفة لإضافة المستخدم إلى القناة باستخدام Telegram Bot API.
    """
    bot = Bot(token=TELEGRAM_BOT_TOKEN)

    # تحديد القناة الافتراضية إذا لم يتم تمرير قناة محددة
    if not channel_id:
        channel_id = DEFAULT_CHANNEL_ID

    try:
        # محاولة إزالة الحظر (إذا كان المستخدم محظورًا) ثم دعوة المستخدم
        await bot.unban_chat_member(chat_id=channel_id, user_id=user_id)
        print(f"تمت إضافة المستخدم {user_id} إلى القناة {channel_id}.")
        return True
    except Exception as add_error:
        # تسجيل الخطأ عند فشل الإضافة التلقائية
        print(f"خطأ أثناء إضافة المستخدم {user_id} إلى القناة {channel_id}: {add_error}")

        # إذا فشل الإضافة التلقائية، إنشاء رابط دعوة
        try:
            invite_link = await bot.create_chat_invite_link(
                chat_id=channel_id,
                member_limit=1,  # رابط مخصص لمستخدم واحد فقط
                expire_date=None  # لا يوجد تاريخ انتهاء
            )
            # إرسال رابط الدعوة عبر دردشة البوت
            await send_message_to_user(
                user_id,
                f"مرحبًا! لم نتمكن من إضافتك مباشرة إلى القناة. يمكنك الانضمام عبر الرابط التالي:\n{invite_link.invite_link}"
            )
            print(f"تم إرسال رابط الدعوة إلى المستخدم {user_id}.")
            return True
        except Exception as invite_error:
            # تسجيل الخطأ عند فشل إنشاء رابط الدعوة
            print(f"خطأ أثناء إنشاء رابط الدعوة للمستخدم {user_id} إلى القناة {channel_id}: {invite_error}")
            return False

#دالة لإعادة المحاولة
def schedule_retry_add_to_channel(user_id, subscription_type):
    """
    جدولة محاولة إعادة إضافة المستخدم إلى القناة.
    """
    retry_time = datetime.now() + timedelta(minutes=5)  # المحاولة بعد 5 دقائق

    # إضافة المهمة إلى قاعدة البيانات
    retry_task = ScheduledTask(
        task_type="retry_add",
        user_id=user_id,
        execute_at=retry_time,
        status="pending"
    )
    try:
        db.session.add(retry_task)
        db.session.commit()
        print(f"تم جدولة إعادة المحاولة لإضافة المستخدم {user_id}.")
    except Exception as e:
        db.session.rollback()
        print(f"خطأ أثناء جدولة إعادة المحاولة للمستخدم {user_id}: {e}")

# تنفيذ العمليات على قاعدة البيانات حتى في حالة ظهور خطأ
def execute_with_retry(query, params=None, retries=3, delay=1):
    """
    ينفذ استعلامًا مع إعادة المحاولة عند مواجهة خطأ.
    :param query: نص الاستعلام SQL.
    :param params: الوسائط المستخدمة مع الاستعلام.
    :param retries: عدد مرات إعادة المحاولة.
    :param delay: الفاصل الزمني بين المحاولات (بالثواني).
    :return: True إذا نجح التنفيذ، False إذا استنفدت جميع المحاولات.
    """
    for attempt in range(retries):
        try:
            if params:
                db.session.execute(query, params)
            else:
                db.session.execute(query)
            db.session.commit()
            return True
        except OperationalError as e:
            if "database is locked" in str(e):
                print(f"Database is locked. Retrying in {delay} seconds... (Attempt {attempt + 1}/{retries})")
                time.sleep(delay)
            else:
                db.session.rollback()
                raise e
    print("Failed to execute query after retries.")
    return False

# وظيفة جدولة التذكيرات
async def schedule_reminders(user_id, subscription_type, expiry_date, reminder_settings=None):
    """
    تقوم بجدولة تذكيرين للمستخدم قبل انتهاء اشتراكه.
    يمكن تخصيص أوقات التذكيرات عبر reminder_settings.
    """
    try:
        # استخدام الإعدادات الافتراضية أو المخصصة
        settings = reminder_settings if reminder_settings else DEFAULT_REMINDER_SETTINGS

        # التأكد من أن expiry_date هو كائن datetime
        if isinstance(expiry_date, str):
            logging.info(f"Parsing expiry_date from string: {expiry_date}")
            expiry_date = datetime.strptime(expiry_date, "%Y-%m-%d %H:%M:%S")
            logging.info(f"Expiry date after parsing (datetime object): {expiry_date}")

        # حساب أوقات التذكيرات
        first_reminder_time = expiry_date - timedelta(hours=settings["first_reminder"])
        second_reminder_time = expiry_date - timedelta(hours=settings["second_reminder"])

        # استخدام db.engine لإضافة المهام إلى قاعدة البيانات
        async with db.engine.begin() as conn:
            # إضافة التذكير الأول
            await conn.execute(
                db.insert(ScheduledTask).values(
                    task_type="first_reminder",
                    user_id=user_id,
                    execute_at=first_reminder_time,
                    status="pending"
                )
            )
            logging.info(f"First reminder scheduled for user {user_id} at {first_reminder_time}")

            # إضافة التذكير الثاني
            await conn.execute(
                db.insert(ScheduledTask).values(
                    task_type="second_reminder",
                    user_id=user_id,
                    execute_at=second_reminder_time,
                    status="pending"
                )
            )
            logging.info(f"Second reminder scheduled for user {user_id} at {second_reminder_time}")

        logging.info(f"تم جدولة التذكيرات للمستخدم {user_id}.")
    except Exception as e:
        logging.error(f"خطأ أثناء جدولة التذكيرات: {e}")

# وظيفة جدولة إزالة المستخدم
async def schedule_remove_user(user_id, subscription_type, expiry_date):
    """
    تقوم بجدولة إزالة المستخدم من القناة بعد انتهاء اشتراكه مباشرة.
    """
    try:
        # التأكد من أن expiry_date هو كائن datetime
        if isinstance(expiry_date, str):
            expiry_date = datetime.strptime(expiry_date, "%Y-%m-%d %H:%M:%S")

        # حساب وقت الإزالة
        remove_time = expiry_date + timedelta(seconds=1)

        # استخدام db.engine لإضافة المهمة إلى قاعدة البيانات
        async with db.engine.begin() as conn:
            await conn.execute(
                db.insert(ScheduledTask).values(
                    task_type="remove_user",
                    user_id=user_id,
                    execute_at=remove_time,
                    status="pending"
                )
            )
        logging.info(f"تم جدولة إزالة المستخدم {user_id} بعد انتهاء الاشتراك.")
    except Exception as e:
        logging.error(f"خطأ أثناء جدولة الإزالة: {e}")

# وظيفة لإزالة المستخدم من القناة باستخدام Telegram Bot API
def remove_user_from_channel(user_id, subscription_type=None, channel_id=None):
    """
    وظيفة لإزالة المستخدم من القناة باستخدام Telegram Bot API.
    """
    bot = Bot(token=TELEGRAM_BOT_TOKEN)

    # استخدام القناة الافتراضية إذا لم يتم تمرير قناة محددة
    if not channel_id:
        channel_id = DEFAULT_CHANNEL_ID

    try:
        # إزالة المستخدم من القناة
        bot.ban_chat_member(chat_id=channel_id, user_id=user_id)
        logging.info(f"تمت إزالة المستخدم {user_id} من القناة {channel_id}.")
        return True
    except Exception as e:
        logging.error(f"خطأ أثناء إزالة المستخدم {user_id} من القناة {channel_id}: {e}")
        return False
