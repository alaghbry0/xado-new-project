import sqlite3
from datetime import datetime, timedelta
from telegram import Bot
# استيراد وظيفة الإرسال من telegram_bot
from telegram_bot import send_message_to_user
import asyncio

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



# إعداد توكن البوت ومعرف القناة الافتراضي
TELEGRAM_BOT_TOKEN = "7375681204:AAE8CpTeEpEw4gscDX0Caxj2m_rHvHv5IGc"  # استبدله بالتوكن الخاص بك
DEFAULT_CHANNEL_ID = "-1002277553158"  # المعرف الافتراضي للقناة


# وظيفة جدولة التذكيرات
def schedule_reminders(user_id, subscription_type, expiry_date, reminder_settings=None):
    """
    تقوم بجدولة تذكيرين للمستخدم قبل انتهاء اشتراكه.
    يمكن تخصيص أوقات التذكيرات عبر reminder_settings.
    """
    conn = sqlite3.connect("database/database.db")
    cursor = conn.cursor()

    try:
        # استخدام الإعدادات الافتراضية أو المخصصة
        settings = reminder_settings if reminder_settings else DEFAULT_REMINDER_SETTINGS

        expiry_datetime = datetime.strptime(expiry_date, "%Y-%m-%d %H:%M:%S")
        first_reminder_time = expiry_datetime - timedelta(hours=settings["first_reminder"])
        second_reminder_time = expiry_datetime - timedelta(hours=settings["second_reminder"])

        # جدولة التذكير الأول
        cursor.execute("""
            INSERT INTO scheduled_tasks (task_type, user_id, execute_at, status)
            VALUES (?, ?, ?, ?)
        """, ("first_reminder", user_id, first_reminder_time, "pending"))

        # جدولة التذكير الثاني
        cursor.execute("""
            INSERT INTO scheduled_tasks (task_type, user_id, execute_at, status)
            VALUES (?, ?, ?, ?)
        """, ("second_reminder", user_id, second_reminder_time, "pending"))

        conn.commit()
        print(f"تم جدولة التذكيرات للمستخدم {user_id}.")
    except Exception as e:
        print(f"خطأ أثناء جدولة التذكيرات: {e}")
    finally:
        conn.close()

# وظيفة جدولة إزالة المستخدم
def schedule_remove_user(user_id, subscription_type, expiry_date):
    """
    تقوم بجدولة إزالة المستخدم من القناة بعد انتهاء اشتراكه مباشرة.
    """
    conn = sqlite3.connect("database/database.db")
    cursor = conn.cursor()

    try:
        # حساب وقت الإزالة
        remove_time = datetime.strptime(expiry_date, "%Y-%m-%d %H:%M:%S") + timedelta(seconds=1)

        # إدخال المهمة إلى جدول المهام المجدولة
        cursor.execute("""
            INSERT INTO scheduled_tasks (task_type, user_id, execute_at, status)
            VALUES (?, ?, ?, ?)
        """, ("remove_user", user_id, remove_time, "pending"))

        conn.commit()
        print(f"تم جدولة إزالة المستخدم {user_id} بعد انتهاء الاشتراك.")
    except Exception as e:
        print(f"خطأ أثناء جدولة الإزالة: {e}")
    finally:
        conn.close()


# وظيفة لإضافة المستخدم إلى القناة
def add_user_to_channel(user_id, subscription_type=None, channel_id=None):
    """
    وظيفة لإضافة المستخدم إلى القناة باستخدام Telegram Bot API.
    """
    bot = Bot(token=TELEGRAM_BOT_TOKEN)

    if not channel_id:
        channel_id = DEFAULT_CHANNEL_ID

    try:
        # محاولة إزالة الحظر (إذا كان موجودًا) ثم دعوة المستخدم
        bot.unban_chat_member(chat_id=channel_id, user_id=user_id)
        print(f"تمت إضافة المستخدم {user_id} إلى القناة {channel_id}.")
        return True
    except Exception as e:
        print(f"خطأ أثناء إضافة المستخدم {user_id} إلى القناة {channel_id}: {e}")

        # إذا فشل الإضافة التلقائية، إنشاء رابط دعوة
        try:
            invite_link = bot.create_chat_invite_link(
                chat_id=channel_id,
                member_limit=1,
                expire_date=None
            )
            # إرسال رابط الدعوة عبر دردشة البوت
            asyncio.run(send_message_to_user(
                user_id,
                f"مرحبًا! لم نتمكن من إضافتك مباشرة إلى القناة. يمكنك الانضمام عبر الرابط التالي:\n{invite_link['invite_link']}"
            ))
            return True
        except Exception as invite_error:
            print(f"خطأ أثناء إنشاء رابط الدعوة للمستخدم {user_id}: {invite_error}")
            return False

# وظيفة إزالة المستخدم من القناة
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
        print(f"تمت إزالة المستخدم {user_id} من القناة {channel_id}.")
        return True
    except Exception as e:
        print(f"خطأ أثناء إزالة المستخدم {user_id} من القناة {channel_id}: {e}")
        return False