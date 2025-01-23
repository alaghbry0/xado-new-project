from db_queries import add_user, get_user, add_scheduled_task, update_subscription
from aiogram import Bot
import asyncio
from aiogram.exceptions import TelegramAPIError
import logging
from config import TELEGRAM_BOT_TOKEN     # إعداد توكن البوت
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


# وظيفة لإضافة المستخدم إلى القناة
async def add_user_to_channel(telegram_id: int, subscription_type_id: int, db_pool):
    """
    إضافة المستخدم إلى القناة المحددة أو إرسال دعوة إذا لم يكن موجودًا.
    """
    try:
        # جلب تفاصيل الاشتراك بناءً على subscription_type_id
        async with db_pool.acquire() as connection:
            subscription_type = await connection.fetchrow(
                "SELECT channel_id, name FROM subscription_types WHERE id = $1", subscription_type_id
            )

        if not subscription_type:
            logging.error(f"لم يتم العثور على نوع الاشتراك {subscription_type_id}.")
            return False

        channel_id = subscription_type['channel_id']
        channel_name = subscription_type['name']  # اسم القناة

        # التحقق مما إذا كان المستخدم موجودًا بالفعل في القناة
        try:
            member = await telegram_bot.get_chat_member(chat_id=channel_id, user_id=telegram_id)
            if member.status in ['member', 'administrator', 'creator']:
                # المستخدم موجود بالفعل في القناة
                logging.info(f"المستخدم {telegram_id} موجود بالفعل في القناة {channel_id}.")
                # إرسال رسالة تأكيد التجديد
                success = await send_message(telegram_id, f"تم تجديد اشتراكك في القناة {channel_name} بنجاح!")
                if success:
                    logging.info(f"تم إرسال رسالة تجديد الاشتراك للمستخدم {telegram_id}.")
                return True
        except TelegramAPIError as member_check_error:
            logging.info(f"فشل التحقق من عضوية المستخدم {telegram_id} في القناة {channel_id}: {member_check_error}")
            # نستمر إذا لم يكن المستخدم موجودًا

        # التحقق من أن المستخدم ليس محظورًا قبل محاولة الإضافة
        try:
            await telegram_bot.unban_chat_member(chat_id=channel_id, user_id=telegram_id)
            logging.info(f"تم التحقق من أن المستخدم {telegram_id} ليس محظورًا.")
        except TelegramAPIError as unban_error:
            logging.warning(f"لم يتمكن من إزالة الحظر عن المستخدم {telegram_id} في القناة {channel_id}: {unban_error}")

        # إذا لم يكن المستخدم موجودًا، نقوم بإنشاء وإرسال دعوة
        invite_link = await telegram_bot.create_chat_invite_link(
            chat_id=channel_id,
            member_limit=1,
            expire_date=None  # الرابط بدون تاريخ انتهاء
        )

        # إرسال رابط الدعوة عبر الوظيفة الموحدة
        success = await send_message(
            telegram_id,
            f"لقد تم معالجة اشتراكك بنجاح! يمكنك الانضمام إلى قناة {channel_name} عبر هذا الرابط:\n{invite_link.invite_link}"
        )
        if success:
            logging.info(f"تم إرسال رابط الدعوة إلى المستخدم {telegram_id} للقناة {channel_name}.")
        else:
            logging.warning(f"فشل إرسال رابط الدعوة إلى المستخدم {telegram_id}.")

        return success

    except TelegramAPIError as invite_error:
        logging.error(
            f"خطأ أثناء إنشاء أو إرسال رابط الدعوة للمستخدم {telegram_id} إلى القناة {subscription_type_id}: {invite_error}"
        )
        return False
    except Exception as e:
        logging.error(f"خطأ غير متوقع أثناء إرسال رابط الدعوة للمستخدم {telegram_id} إلى القناة {subscription_type_id}: {e}")
        return False



# وظيفة لإزالة المستخدم من القناة باستخدام Telegram Bot API
async def remove_user_from_channel(connection, telegram_id: int, channel_id: int):
    """
    إزالة المستخدم من القناة وإرسال رسالة إشعار باستخدام send_message.
    """
    try:
        # جلب اسم القناة من قاعدة البيانات
        subscription_type = await connection.fetchrow(
            "SELECT name FROM subscription_types WHERE channel_id = $1", channel_id
        )

        if not subscription_type:
            logging.error(f"لم يتم العثور على القناة {channel_id}.")
            return False

        channel_name = subscription_type['name']

        # محاولة إزالة المستخدم من القناة
        try:
            await telegram_bot.ban_chat_member(chat_id=channel_id, user_id=telegram_id)
            logging.info(f"تمت إزالة المستخدم {telegram_id} من القناة {channel_id}.")
        except TelegramAPIError as e:
            logging.error(f"فشل إزالة المستخدم {telegram_id} من القناة {channel_id}: {e}")
            return False

        # إرسال رسالة إشعار للمستخدم
        removal_message = (
            f"لقد تم إخراجك من قناة '{channel_name}' لعدم التجديد .\n"
            "مرحب بك للعودة في أي وقت! يُرجى تجديد الاشتراك للانضمام مجددًا."
        )
        success = await send_message(telegram_id, removal_message)
        if success:
            logging.info(f"تم إرسال رسالة الإخطار للمستخدم {telegram_id}.")
        else:
            logging.warning(f"فشل إرسال رسالة الإخطار للمستخدم {telegram_id}.")

        return True
    except Exception as e:
        logging.error(f"خطأ غير متوقع أثناء إزالة المستخدم {telegram_id} من القناة {channel_id}: {e}")
        return False

async def send_message(telegram_id: int, message: str):
    """
    إرسال رسالة مباشرة إلى مستخدم عبر دردشة البوت باستخدام aiogram.
    """
    try:
        # التحقق مما إذا كانت دردشة المستخدم نشطة
        if not await is_chat_active(telegram_id):
            logging.warning(f"Skipping message for user {telegram_id} as they don't have an active chat.")
            return False

        # إرسال الرسالة
        await telegram_bot.send_message(chat_id=telegram_id, text=message)
        logging.info(f"تم إرسال الرسالة إلى المستخدم {telegram_id}: {message}")
        return True
    except TelegramAPIError as e:
        if "chat not found" in str(e).lower():
            logging.error(f"Chat not found for user {telegram_id}. ربما قام المستخدم بحظر البوت أو لم يبدأ المحادثة.")
        else:
            logging.error(f"خطأ في Telegram API أثناء إرسال الرسالة إلى المستخدم {telegram_id}: {e}")
        return False
    except Exception as e:
        logging.error(f"خطأ غير متوقع أثناء إرسال الرسالة إلى المستخدم {telegram_id}: {e}")
        return False


async def is_chat_active(telegram_id: int):
    """
    التحقق مما إذا كانت دردشة المستخدم مع البوت نشطة.
    """
    try:
        # محاولة الحصول على معلومات الدردشة
        chat = await telegram_bot.get_chat(chat_id=telegram_id)
        return chat is not None
    except TelegramAPIError as e:
        if "chat not found" in str(e).lower():
            logging.warning(f"Chat not active for user {telegram_id}. ربما لم يبدأ المستخدم المحادثة أو قام بحظر البوت.")
        else:
            logging.error(f"Telegram API error while checking chat status for user {telegram_id}: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error while checking chat status for user {telegram_id}: {e}")
        return False

async def close_telegram_bot_session():
    """
    إغلاق جلسة Telegram Bot API.
    """
    try:
        await telegram_bot.session.close()
        logging.info("تم إغلاق جلسة Telegram Bot API بنجاح.")
    except Exception as e:
        logging.error(f"خطأ أثناء إغلاق جلسة Telegram Bot API: {e}")



