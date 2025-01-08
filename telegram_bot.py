from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler

# توكن البوت الخاص بك
TOKEN = "7893339065:AAFIy3ooJ1yjobJwJTsnR9ZHWTlQfSf7REo"

# رابط التطبيق المصغر
WEB_APP_URL = "https://exaado-mini-app-c04ea61e41f4.herokuapp.com/"

# وظيفة الاستجابة للأمر /start
async def start(update: Update):
    keyboard = [
        [InlineKeyboardButton("فتح التطبيق المصغر", web_app=WebAppInfo(url=WEB_APP_URL))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "مرحبًا بك! يمكنك إدارة اشتراكاتك عبر التطبيق المصغر:",
        reply_markup=reply_markup
    )

if __name__ == "__main__":
    # إنشاء التطبيق باستخدام ApplicationBuilder
    application = ApplicationBuilder().token(TOKEN).build()

    # إضافة أمر /start
    application.add_handler(CommandHandler("start", start))

    # تشغيل البوت
    application.run_polling()
