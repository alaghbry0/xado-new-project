from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import sqlite3
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
import logging

# توكن البوت
TOKEN = "7375681204:AAE8CpTeEpEw4gscDX0Caxj2m_rHvHv5IGc"

# رابط التطبيق المصغر
WEB_APP_URL = "https://exaado-mini-app-c04ea61e41f4.herokuapp.com/"

# وظيفة /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # إعداد زر التطبيق المصغر
        keyboard = [
            [InlineKeyboardButton("فتح التطبيق المصغر", web_app=WebAppInfo(url=WEB_APP_URL))]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # عرض بيانات المستخدم في السجل
        user_id = update.message.from_user.id
        username = update.message.from_user.username
        logging.info(f"Start command triggered by User ID: {user_id}, Username: {username}")

        # إرسال الرسالة مع الزر
        await update.message.reply_text(
            "مرحبًا بك! يمكنك إدارة اشتراكاتك عبر التطبيق المصغر:",
            reply_markup=reply_markup
        )
    except Exception as e:
        logging.error(f"Error in /start command: {e}")
        await update.message.reply_text("حدث خطأ أثناء إعداد التطبيق المصغر. يرجى المحاولة لاحقًا.")

# وظيفة الاشتراك
async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Forex VIP - $5", callback_data="subscribe_forex")],
        [InlineKeyboardButton("Crypto VIP - $10", callback_data="subscribe_crypto")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "اختر خطة الاشتراك:",
        reply_markup=reply_markup
    )

# معالجة اختيار الخطة
async def handle_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    print("Button clicked")
    print(f"Callback Data: {query.data}")

    # معلومات المستخدم
    user_id = query.from_user.id
    username = query.from_user.username
    full_name = query.from_user.full_name

    # تحديد نوع الاشتراك بناءً على الزر الذي تم النقر عليه
    if query.data == "subscribe_forex":
        subscription_type = "Forex VIP"
    elif query.data == "subscribe_crypto":
        subscription_type = "Crypto VIP"
    else:
        await query.edit_message_text("حدث خطأ. برجاء المحاولة مرة أخرى.")
        return

    # الاتصال بقاعدة البيانات
    conn = sqlite3.connect("database/database.db")
    cursor = conn.cursor()

    # إضافة المستخدم إذا لم يكن موجودًا
    cursor.execute("""
        INSERT OR IGNORE INTO users (telegram_id, username, full_name)
        VALUES (?, ?, ?)
    """, (user_id, username, full_name))

    # الحصول على معرف المستخدم من جدول المستخدمين
    cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (user_id,))
    db_user_id = cursor.fetchone()[0]

    # التحقق من وجود اشتراك لنفس المستخدم ونفس النوع
    cursor.execute("""
        SELECT expiry_date FROM subscriptions
        WHERE user_id = ? AND subscription_type = ?
    """, (db_user_id, subscription_type))

    existing_subscription = cursor.fetchone()

    if existing_subscription:
        # إذا كان الاشتراك موجودًا، أضف 30 يومًا إلى تاريخ انتهاء الاشتراك الحالي
        current_expiry_date = datetime.strptime(existing_subscription[0], "%Y-%m-%d")
        new_expiry_date = (current_expiry_date + timedelta(minutes=3)).strftime("%Y-%m-%d")

        cursor.execute("""
            UPDATE subscriptions
            SET expiry_date = ?
            WHERE user_id = ? AND subscription_type = ?
        """, (new_expiry_date, db_user_id, subscription_type))
        print("Subscription updated!")
        confirmation_message = f"تم تجديد الاشتراك في {subscription_type} حتى {new_expiry_date}."
    else:
        # إذا لم يكن الاشتراك موجودًا، قم بإضافته مع مدة 30 يومًا
        new_expiry_date = (datetime.now() + timedelta(minutes=3)).strftime("%Y-%m-%d")
        cursor.execute("""
            INSERT INTO subscriptions (user_id, subscription_type, expiry_date)
            VALUES (?, ?, ?)
        """, (db_user_id, subscription_type, new_expiry_date))
        print("Subscription added!")
        confirmation_message = f"تم الاشتراك في {subscription_type} بنجاح! ينتهي الاشتراك في {new_expiry_date}."

    # حفظ التغييرات وإغلاق الاتصال
    conn.commit()
    conn.close()

    print("Data saved successfully!")

    # رسالة تأكيد الاشتراك
    await query.edit_message_text(confirmation_message)

# إعدادات تسجيل الأخطاء
logging.basicConfig(level=logging.INFO)

async def send_message(bot, chat_id, message):
    print(f"Sending message to {chat_id}: {message}")  # لتتبع التنفيذ
    await bot.send_message(chat_id=chat_id, text=message)

    # سجل الإشعار في قاعدة البيانات
    conn = sqlite3.connect("database/database.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO notifications (user_id, subscription_id, message, sent_at)
        VALUES ((SELECT id FROM users WHERE telegram_id = ?), ?, ?, ?)
    """, (chat_id, None, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def schedule_reminders(app):
    """جدولة التذكيرات بناءً على تواريخ الاشتراكات."""
    conn = sqlite3.connect("database/database.db")
    cursor = conn.cursor()

    # جلب الاشتراكات
    cursor.execute("""
        SELECT subscriptions.id, users.telegram_id, subscriptions.subscription_type, subscriptions.expiry_date
        FROM subscriptions
        JOIN users ON subscriptions.user_id = users.id
    """)
    subscriptions = cursor.fetchall()

    scheduler = BackgroundScheduler()
    scheduler.start()

    for subscription in subscriptions:
        subscription_id, telegram_id, subscription_type, expiry_date = subscription

        # تحويل تاريخ انتهاء الاشتراك إلى كائن datetime
        expiry_date_obj = datetime.strptime(expiry_date, "%Y-%m-%d %H:%M:%S")

        # حساب أوقات التذكيرات
        first_reminder = expiry_date_obj - timedelta(minutes=2)
        second_reminder = expiry_date_obj - timedelta(minutes=1)

        # جدولة التذكير الأول
        if first_reminder > datetime.now():
            logging.info(f"Scheduling first reminder for {subscription_type} at {first_reminder}")
            scheduler.add_job(
                lambda: app.create_task(send_message(
                    app.bot,
                    telegram_id,
                    f"تذكير: اشتراكك في {subscription_type} سينتهي خلال 48 ساعة. يرجى التجديد لتجنب الإيقاف."
                )),
                trigger=DateTrigger(run_date=first_reminder)
            )

        # جدولة التذكير الثاني
        if second_reminder > datetime.now():
            logging.info(f"Scheduling second reminder for {subscription_type} at {second_reminder}")
            scheduler.add_job(
                lambda: app.create_task(send_message(
                    app.bot,
                    telegram_id,
                    f"تذكير: اشتراكك في {subscription_type} سينتهي خلال 24 ساعة. يرجى التجديد لتجنب الإيقاف."
                )),
                trigger=DateTrigger(run_date=second_reminder)
            )

    conn.close()




# إعداد التطبيق وجدولة التذكيرات
if __name__ == "__main__":
    application = ApplicationBuilder().token(TOKEN).build()

    # إضافة أوامر البوت
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CallbackQueryHandler(handle_subscription))

    # جدولة التذكيرات
    schedule_reminders(application)

    # تشغيل البوت
    application.run_polling()
