from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext

# توكن البوت الخاص بك
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

# رابط التطبيق المصغر
WEB_APP_URL = "https://your-app.herokuapp.com/"

def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id

    # إعداد زر لفتح التطبيق المصغر
    keyboard = [
        [InlineKeyboardButton("فتح التطبيق المصغر", web_app=WEB_APP_URL)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(
        "مرحبًا بك! يمكنك إدارة اشتراكاتك عبر التطبيق المصغر:",
        reply_markup=reply_markup
    )

if __name__ == "__main__":
    # إعداد البوت
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    # أمر /start
    dp.add_handler(CommandHandler("start", start))

    # تشغيل البوت
    updater.start_polling()
    updater.idle()
