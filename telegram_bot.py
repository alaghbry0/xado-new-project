from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import logging
from config import TELEGRAM_BOT_TOKEN
from telegram import Bot

# إنشاء كائن البوت
telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN)

# إعداد تسجيل الأخطاء
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# رابط التطبيق المصغر
WEB_APP_URL = "https://exaado-mini-app-c04ea61e41f4.herokuapp.com/"

# وظيفة /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    إرسال زر فتح التطبيق المصغر عند استخدام /start.
    """
    try:
        user_id = update.message.from_user.id
        username = update.message.from_user.username

        # إعداد زر التطبيق المصغر
        keyboard = [
            [InlineKeyboardButton("فتح التطبيق المصغر", web_app=WebAppInfo(url=WEB_APP_URL))]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # سجل بيانات المستخدم
        logging.info(f"/start command triggered by User ID: {user_id}, Username: {username}")

        # إرسال الرسالة مع الزر
        await update.message.reply_text(
            "مرحبًا! اضغط على الزر أدناه لفتح التطبيق المصغر:",
            reply_markup=reply_markup
        )
    except Exception as e:
        logging.error(f"Error in /start command: {e}")
        await update.message.reply_text("حدث خطأ أثناء إعداد التطبيق المصغر. يرجى المحاولة لاحقًا.")

# وظيفة لإرسال رسالة عبر دردشة البوت
async def send_message_to_user(user_id: int, message: str):
    """
    إرسال رسالة مباشرة إلى مستخدم عبر دردشة البوت.
    """
    try:
        await telegram_bot.send_message(chat_id=user_id, text=message)
        logging.info(f"تم إرسال الرسالة إلى المستخدم {user_id}: {message}")
    except Exception as e:
        logging.error(f"خطأ أثناء إرسال الرسالة إلى المستخدم {user_id}: {e}")

# إعداد التطبيق وتشغيله
def main():
    """
    إنشاء التطبيق وتشغيله باستخدام polling.
    """
    try:
        application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

        # إضافة أوامر البوت
        application.add_handler(CommandHandler("start", start))

        # تشغيل البوت
        application.run_polling()
    except Exception as e:
        logging.error(f"خطأ أثناء تشغيل البوت: {e}")

if __name__ == "__main__":
    main()
