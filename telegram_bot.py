from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import logging

# إعداد تسجيل الأخطاء
logging.basicConfig(level=logging.INFO)

# توكن البوت
TOKEN = "7375681204:AAE8CpTeEpEw4gscDX0Caxj2m_rHvHv5IGc"

# رابط التطبيق المصغر
WEB_APP_URL = "https://exaado-mini-app-c04ea61e41f4.herokuapp.com/"

# وظيفة /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    وظيفة ترسل زر فتح التطبيق المصغر عند استخدام /start.
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

# إعداد التطبيق
if __name__ == "__main__":
    application = ApplicationBuilder().token(TOKEN).build()

    # إضافة أوامر البوت
    application.add_handler(CommandHandler("start", start))

    # تشغيل البوت
    application.run_polling()
