import asyncpg
import asyncio
from config import DATABASE_CONFIG, TELEGRAM_BOT_TOKEN
from quart import Quart, request, jsonify, render_template, Response
import logging
import os
from scheduler import start_scheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from quart_cors import cors
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from datetime import datetime, timezone, timedelta
from db_queries import add_user, get_user, add_subscription, update_subscription, get_subscription, add_scheduled_task
from database.db_utils import add_user_to_channel, close_telegram_bot_session
from Crypto.Signature import pkcs1_15
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from dotenv import load_dotenv
load_dotenv()  # تحميل متغيرات البيئة

telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN)

# إنشاء التطبيق
app = Quart(__name__, static_folder="static")
app = cors(app, allow_origin="*")  # تمكين CORS لجميع الطلبات

# تحميل المفتاح الخاص من متغير البيئة
private_key_content = os.environ.get("PRIVATE_KEY")

# التحقق من وجود المفتاح في البيئة
if not private_key_content:
    raise ValueError("PRIVATE_KEY environment variable is not set.")

# استيراد المفتاح الخاص
private_key = RSA.import_key(private_key_content)

# الرسالة التي تريد توقيعها
message = b"transaction data"
hash_msg = SHA256.new(message)

# توقيع الرسالة باستخدام المفتاح الخاص
signature = pkcs1_15.new(private_key).sign(hash_msg)

# طباعة التوقيع
print("Signed message:", signature.hex())
print(os.environ.get("PRIVATE_KEY"))



async def setup_scheduler():
    logging.info("Calling start_scheduler from app.py")
    try:
        start_scheduler(app.db_pool)
        logging.info("start_scheduler تم استدعاؤها بنجاح.")
    except Exception as e:
        logging.error(f"خطأ أثناء استدعاء start_scheduler: {e}")

@app.before_serving
async def create_db_connection():
    # إنشاء اتصال مع قاعدة البيانات عند بدء التطبيق
    try:
        app.db_pool = await asyncpg.create_pool(**DATABASE_CONFIG)
        logging.info("تم إنشاء اتصال قاعدة البيانات بنجاح.")
    except Exception as e:
        logging.error(f"حدث خطأ أثناء إنشاء اتصال قاعدة البيانات: {e}")
        return

    # إعداد الجدولة
    await setup_scheduler()

@app.after_serving
async def close_resources():
    """
    إغلاق جميع الموارد (جلسة البوت وقاعدة البيانات) عند إيقاف التطبيق.
    """
    try:
        # إغلاق جلسة البوت
        await close_telegram_bot_session()

        # إغلاق الاتصال بقاعدة البيانات
        await app.db_pool.close()
        logging.info("تم إغلاق جميع الموارد بنجاح (جلسة البوت وقاعدة البيانات).")
    except Exception as e:
        logging.error(f"حدث خطأ أثناء إغلاق الموارد: {e}")

# إعداد تسجيل الأخطاء والمعلومات
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


# نقطة API للاشتراك
@app.route("/api/subscribe", methods=["POST"])
async def subscribe():
    """
    معالجة طلب الاشتراك أو تجديد الاشتراك.
    """
    try:
        # استقبال البيانات من الطلب
        data = await request.get_json()
        telegram_id = int(data.get("telegram_id"))
        subscription_type_id = int(data.get("subscription_type_id"))
        username = data.get("username", None)  # اسم المستخدم (اختياري)
        full_name = data.get("full_name", None)  # الاسم الكامل (اختياري)
        payment_reference = data.get("payment_reference")  # مرجع الدفع
        logging.info(f"Received telegram_id: {telegram_id}, subscription_type_id: {subscription_type_id}")

        # التحقق من صحة البيانات المدخلة
        if not telegram_id or not subscription_type_id:
            error_message = "Missing 'telegram_id' or 'subscription_type_id'"
            logging.error(error_message)
            return jsonify({"error": error_message}), 400

        async with app.db_pool.acquire() as connection:
            # التحقق من وجود المستخدم في جدول users
            user = await get_user(connection, telegram_id)
            if not user:
                # إذا لم يكن المستخدم موجودًا، يتم إضافته
                added = await add_user(connection, telegram_id, username=username, full_name=full_name)
                if not added:
                    logging.error(f"Failed to add user {telegram_id} to the users table.")
                    return jsonify({"error": "Failed to register the user."}), 500
            else:
                # تحديث بيانات المستخدم إذا كان موجودًا
                await add_user(connection, telegram_id, username=username, full_name=full_name)
            # جلب تفاصيل الاشتراك من جدول subscription_types
            subscription_type = await connection.fetchrow(
                "SELECT id, name, channel_id FROM subscription_types WHERE id = $1", subscription_type_id
            )

            if not subscription_type:
                error_message = f"Invalid subscription_type_id: {subscription_type_id}"
                logging.error(error_message)
                return jsonify({"error": error_message}), 400

            subscription_name = subscription_type['name']
            channel_id = subscription_type['channel_id']

            # التحقق من وجود الاشتراك الحالي بناءً على telegram_id
            subscription = await connection.fetchrow(
                """
                SELECT * FROM subscriptions 
                WHERE telegram_id = $1 AND channel_id = $2
                """, telegram_id, channel_id
            )
            logging.info(f"Subscription retrieved: {subscription}")

            # تحديد تاريخ انتهاء الاشتراك الجديد
            current_time = datetime.now()
            if subscription:
                if subscription['is_active'] and subscription['expiry_date'] >= current_time:
                    # تمديد الاشتراك النشط
                    new_expiry = subscription['expiry_date'] + timedelta(minutes=7)
                else:
                    # تجديد الاشتراك المنتهي
                    new_expiry = current_time + timedelta(minutes=7)

                # تحديث الاشتراك
                await update_subscription(
                    connection,
                    telegram_id=telegram_id,
                    channel_id=channel_id,
                    subscription_type_id=subscription_type_id,
                    new_expiry_date=new_expiry,
                    is_active=True
                )

                logging.info(f"Subscription for user {telegram_id} updated until {new_expiry}.")
            else:
                # إضافة اشتراك جديد
                new_expiry = current_time + timedelta(minutes=7)
                added = await add_subscription(
                    connection,
                    telegram_id=telegram_id,
                    channel_id=channel_id,
                    subscription_type_id=subscription_type_id,
                    expiry_date=new_expiry,
                    is_active=True
                )
                if not added:
                    logging.error(f"Failed to add a new subscription for user {telegram_id}.")
                    return jsonify({"error": "Failed to create a subscription."}), 500

            # إرسال المستخدم إلى القناة
            channel_added = await add_user_to_channel(telegram_id, subscription_type_id, app.db_pool)
            if not channel_added:
                error_message = f"Failed to add user {telegram_id} to channel {channel_id}."
                logging.error(error_message)
                return jsonify({"error": error_message}), 500

            # إضافة المهام المجدولة
            reminders = [
                ("first_reminder", new_expiry - timedelta(minutes=4)),
                ("second_reminder", new_expiry - timedelta(minutes=2)),
                ("remove_user", new_expiry),
            ]

            for task_type, execute_time in reminders:
                await add_scheduled_task(connection, task_type, telegram_id, channel_id, execute_time)
                logging.info(f"Task '{task_type}' added at {datetime.now()}, scheduled to run at {execute_time}")

        # إرسال رسالة النجاح
        message = f"تم الاشتراك في {subscription_name} حتى {new_expiry.strftime('%Y-%m-%d %H:%M:%S')}."
        return jsonify({"message": message, "expiry_date": new_expiry.strftime('%Y-%m-%d %H:%M:%S')}), 200

    except Exception as e:
        logging.error(f"Unexpected error in subscribe: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500


# نقطة API للتجديد
@app.route("/api/renew", methods=["POST"])
async def renew_subscription():
    conn = None
    try:
        # استقبال البيانات من الطلب
        data = await request.json
        telegram_id = data.get("telegram_id")
        subscription_type_id = data.get("subscription_type_id")

        if not telegram_id or not subscription_type_id:
            return await jsonify({"error": "Missing telegram_id or subscription_type_id"}), 400

        conn = sqlite3.connect("database/database.db")
        cursor = conn.cursor()

        # الحصول على user_id
        cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
        user = cursor.fetchone()
        if not user:
            return await jsonify({"error": "User not found"}), 404

        user_id = user[0]

        # التحقق من الاشتراك الحالي
        cursor.execute("""
            SELECT expiry_date, is_app.pyFROM subscriptions
            WHERE user_id = ? AND subscription_type_id = ?
        """, (user_id, subscription_type_id))
        existing_subscription = cursor.fetchone()

        if existing_subscription:
            expiry_date, is_app.py= existing_subscription
            try:
                current_expiry = datetime.strptime(expiry_date, "%Y-%m-%d %H:%M:%S")

                if is_active:
                    # تمديد الاشتراك الحالي
                    new_expiry = (current_expiry + timedelta(minutes=3)).strftime("%Y-%m-%d %H:%M:%S")
                else:
                    # إعادة تفعيل الاشتراك
                    new_expiry = (datetime.now() + timedelta(minutes=3)).strftime("%Y-%m-%d %H:%M:%S")

                    # محاولة إعادة إضافة المستخدم إلى القناة
                    success = add_user_to_channel(telegram_id, subscription_type_id)
                    if not success:
                        return await jsonify({"error": "Failed to re-add user to the channel"}), 500

                    # تحديث حالة الاشتراك
                    cursor.execute("""
                        UPDATE subscriptions
                        SET is_app.py= TRUE
                        WHERE user_id = ? AND subscription_type_id = ?
                    """, (user_id, subscription_type_id))

                # تحديث تاريخ انتهاء الاشتراك
                cursor.execute("""
                    UPDATE subscriptions
                    SET expiry_date = ?
                    WHERE user_id = ? AND subscription_type_id = ?
                """, (new_expiry, user_id, subscription_type_id))

                # إعادة جدولة التذكيرات والإزالة
                await schedule_reminders(user_id, subscription_type_id, new_expiry)
                await schedule_remove_user(user_id, subscription_type_id, new_expiry)

                conn.commit()
                return jsonify({"message": f"تم تجديد الاشتراك حتى {new_expiry}"}), 200
            except ValueError as app_error:
                logging.error(f"Invalid date format: {expiry_date} - {str(app_error)}")
                return jsonify({"error": "Invalid date format in database."}), 500
        else:
            return jsonify({"error": "Subscription not found for the provided user and type"}), 404
    except Exception as Un_error:
        logging.error(f"Unexpected error in /api/renew: {str(Un_error)}")
        return jsonify({"error": "An unexpected error occurred"}), 500
    finally:
        if conn:
            conn.close()

# نقطة API للتحقق من الاشتراك
@app.route("/api/check_subscription", methods=["GET"])
async def check_subscription():
    """
    التحقق من اشتراكات المستخدم بناءً على `telegram_id`.
    """
    try:
        # الحصول على `telegram_id` من بارامترات الطلب
        telegram_id = request.args.get("telegram_id")
        if not telegram_id:
            logging.error("Missing 'telegram_id'")
            return jsonify({"error": "Missing 'telegram_id'"}), 400

        # التحقق من صحة `telegram_id`
        try:
            telegram_id = int(telegram_id)
            logging.info(f"Received telegram_id: {telegram_id}, type: {type(telegram_id)}")
        except ValueError:
            logging.error("Invalid 'telegram_id' format")
            return jsonify({"error": "Invalid 'telegram_id' format"}), 400

        async with app.db_pool.acquire() as connection:
            # البحث عن الاشتراكات المرتبطة بـ `telegram_id`
            user_subscriptions = await connection.fetch("""
                SELECT 
                    s.subscription_type_id, 
                    s.expiry_date, 
                    s.is_active,
                    st.channel_id,
                    st.name AS subscription_name
                FROM subscriptions s
                JOIN subscription_types st ON s.channel_id = st.channel_id
                WHERE s.telegram_id = $1
            """, telegram_id)

            # التحقق من وجود اشتراكات
            if not user_subscriptions:
                logging.info(f"No subscriptions found for telegram_id: {telegram_id}")
                return jsonify({"message": "No subscriptions"}), 404

            # تجهيز البيانات للإرجاع
            result = [
                {
                    "subscription_type_id": sub['subscription_type_id'],
                    "channel_id": sub['channel_id'],
                    "subscription_name": sub['subscription_name'],
                    "expiry_date": sub['expiry_date'].strftime('%Y-%m-%d %H:%M:%S'),
                    "is_active": sub['is_active']
                }
                for sub in user_subscriptions
            ]

        # إرجاع البيانات
        logging.info(f"Subscriptions retrieved for telegram_id: {telegram_id}: {result}")
        return jsonify({"subscriptions": result}), 200

    except Exception as e:
        # معالجة أي أخطاء غير متوقعة
        logging.error(f"Error in check_subscription: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.route("/tonconnect-manifest.json", methods=["GET", "OPTIONS"])
async def serve_manifest():
    """
    خدمة ملف tonconnect-manifest.json مع دعم CORS.
    """
    return await app.send_static_file("tonconnect-manifest.json")


@app.route("/api/link-wallet", methods=["POST"])
async def link_wallet():
    try:
        # استلام البيانات من الطلب
        data = await request.get_json()
        telegram_id = int(data.get("telegram_id"))
        wallet_address = data.get("wallet_address")
        username = data.get("username")
        full_name = data.get("full_name")
        wallet_app = data.get("wallet_app")
        wallet_connected = data.get("wallet_connected", True)  # حالة الاتصال (True عند الربط)

        # إذا كان wallet_address كائنًا، استخراج العنوان النصي فقط
        if isinstance(wallet_address, dict) and "address" in wallet_address:
            wallet_address = wallet_address["address"]

        async with app.db_pool.acquire() as connection:
            # التحقق مما إذا كان المستخدم موجودًا
            user = await get_user(connection, telegram_id)

            if user:
                # تحديث البيانات
                if wallet_connected:
                    query = """
                    UPDATE users
                    SET wallet_address = $1,
                        wallet_app = $2,
                        username = $3,
                        full_name = $4
                    WHERE telegram_id = $5
                    """
                    await connection.execute(query, wallet_address, wallet_app, username, full_name, telegram_id)
                    logging.info(f"Updated user {telegram_id} with new wallet details.")
                else:
                    # إذا كانت المحفظة مفصولة، قم بإزالة عنوان المحفظة
                    query = """
                    UPDATE users
                    SET wallet_address = NULL,
                        wallet_app = NULL
                    WHERE telegram_id = $1
                    """
                    await connection.execute(query, telegram_id)
                    logging.info(f"User {telegram_id}'s wallet disconnected.")
            else:
                # إضافة المستخدم الجديد
                await add_user(connection, telegram_id, username=username, full_name=full_name)
                if wallet_connected:
                    query = """
                    UPDATE users
                    SET wallet_address = $1,
                        wallet_app = $2
                    WHERE telegram_id = $3
                    """
                    await connection.execute(query, wallet_address, wallet_app, telegram_id)
                    logging.info(f"Added user {telegram_id} and set wallet details.")

        message = "Wallet details updated successfully!" if wallet_connected else "Wallet disconnected successfully!"
        return jsonify({"message": message}), 200

    except ValueError as ve:
        logging.error(f"Invalid input data: {ve}")
        return jsonify({"error": "Invalid input data"}), 400
    except Exception as e:
        logging.error(f"Error linking wallet: {e}")
        return jsonify({"error": "Internal server error"}), 500



@app.route("/", endpoint="index")
async def home():
    return await render_template("index.html")

@app.route("/shop", endpoint="shop")
async def shop():
    async with app.db_pool.acquire() as connection:
        subscriptions = await connection.fetch("""
            SELECT id, name, price, details, image_url
            FROM subscription_types
            WHERE is_active = TRUE
        """)
    return await render_template("shop.html", subscriptions=subscriptions)

@app.route('/api/verify', methods=['POST'])
async def verify_user():
    try:
        # استخراج البيانات من الطلب
        data = await request.json
        telegram_id =  data.get('telegramId')
        username = data.get('username')

        # تحقق من الحقول المفقودة أو القيم غير الصالحة
        if not telegram_id or not isinstance(telegram_id, int):
            logging.error("Telegram ID is missing or invalid in the request.")
            return jsonify({
                "success": False,
                "message": "Telegram ID is required and must be an integer!"
            }), 400

        if not username or not isinstance(username, str):
            logging.warning("Username is missing or invalid in the request.")
            username = "Unknown User"  # اسم افتراضي إذا كان مفقودًا

        # تسجيل بيانات الطلب
        client_ip = request.remote_addr
        logging.info(f"Verified Telegram ID: {telegram_id}, Username: {username}, IP: {client_ip}")

        # إرسال الاستجابة الناجحة
        return await jsonify({
            "success": True,
            "message": "Telegram ID verified successfully!",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "telegramId": telegram_id,
                "username": username
            }
        }), 200

    except Exception as app_error:
        # تسجيل أي أخطاء غير متوقعة
        logging.error(f"Unexpected error in /api/verify: {app_error}")
        return await jsonify({
            "success": False,
            "message": "An unexpected error occurred!"
        }), 500
@app.route("/profile", endpoint="profile")
async def profile():
    user = {
        "name": "محمد أحمد",
        "profile_image": "assets/img/user-placeholder.jpg",
        "subscriptions": [
            {
                "name": "Forex VIP Channel",
                "expiry_date": "2025-02-01",
                "image_url": "assets/img/forex_channel.jpg"
            },
            {
                "name": "Crypto VIP Channel",
                "expiry_date": "2025-02-15",
                "image_url": "assets/img/crypto_channel.jpg"
            }
        ]
    }
    return await render_template("profile.html", user=user)


# نقطة نهاية اختبارية
@app.route("/")
async def home():
    return "Hello, Quart!"

# تشغيل التطبيق
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)