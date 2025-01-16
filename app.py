import asyncpg
import asyncio
from config import DATABASE_CONFIG
from quart import Quart, request, jsonify, render_template
import logging
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from datetime import datetime, timezone, timedelta
from quart_cors import cors
from database.db_utils import schedule_remove_user, schedule_reminders, add_user_to_channel
# إنشاء التطبيق
app = Quart(__name__)
app = cors(app)  # تمكين CORS لجميع الطلبات

@app.before_serving
async def create_db_connection():
    # إنشاء اتصال مع قاعدة البيانات عند بدء التطبيق
    app.db_pool = await asyncpg.create_pool(**DATABASE_CONFIG)
    logging.info("Database connection established!")

@app.after_serving
async def close_db_connection():
    # إغلاق الاتصال بقاعدة البيانات عند إيقاف التطبيق
    await app.db_pool.close()
    logging.info("Database connection closed!")

# إعداد تسجيل الأخطاء والمعلومات
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


# بيانات الاشتراكات الوهمية
subscriptions = [
    {
        "id": 1,
        "name": "Forex VIP Channel",
        "price": 5,
        "details": "اشترك في قناة الفوركس للحصول على توصيات مميزة.",
        "image_url": "assets/img/forex_channel.jpg"
    },
    {
        "id": 2,
        "name": "Crypto VIP Channel",
        "price": 10,
        "details": "اشترك في قناة الكريبتو للحصول على توصيات مميزة.",
        "image_url": "assets/img/crypto_channel.jpg"
    }
]


# نقطة API للاشتراك
@app.route("/api/subscribe", methods=["POST"])
async def subscribe():
    try:
        # استقبال البيانات من الطلب
        data = await request.get_json()
        telegram_id = int(data.get("telegram_id"))
        subscription_type = data.get("subscription_type")
        logging.info(f"Received telegram_id: {telegram_id}, type: {type(telegram_id)}")

        # التحقق من صحة البيانات المدخلة
        if not telegram_id or not subscription_type:
            logging.error("Missing 'telegram_id' or 'subscription_type'")
            return jsonify({"error": "Missing 'telegram_id' or 'subscription_type"}), 400

        valid_subscription_types = ["Forex VIP Channel", "Crypto VIP Channel"]
        if subscription_type not in valid_subscription_types:
            logging.error(f"Invalid subscription type: {subscription_type}")
            return jsonify({"error": "Invalid subscription type"}), 400

        async with app.db_pool.acquire() as connection:
            # البحث عن المستخدم
            user = await connection.fetchrow(
                "SELECT * FROM users WHERE telegram_id = $1", telegram_id
            )

            if not user:
                # إضافة المستخدم
                await connection.execute(
                    "INSERT INTO users (telegram_id) VALUES ($1)", telegram_id
                )
                user = await connection.fetchrow(
                    "SELECT * FROM users WHERE telegram_id = $1", telegram_id
                )

            # البحث عن الاشتراك
            subscription = await connection.fetchrow(
                "SELECT * FROM subscriptions WHERE user_id = $1 AND subscription_type = $2",
                user['id'], subscription_type
            )

            if subscription:
                if subscription['is_active']:
                    # تمديد الاشتراك
                    new_expiry = subscription['expiry_date'] + timedelta(minutes=3)
                    await connection.execute(
                        "UPDATE subscriptions SET expiry_date = $1 WHERE id = $2",
                        new_expiry, subscription['id']
                    )
                    message = f"تم تجديد اشتراكك حتى {new_expiry.strftime('%Y-%m-%d %H:%M:%S')}"
                else:
                    # إعادة تفعيل الاشتراك
                    new_expiry = datetime.now() + timedelta(minutes=3)
                    success = await add_user_to_channel(telegram_bot, user['telegram_id'], subscription_type)

                    if success:
                        await connection.execute(
                            "UPDATE subscriptions SET is_active = TRUE, expiry_date = $1 WHERE id = $2",
                            new_expiry, subscription['id']
                        )
                        message = f"تم إعادة تفعيل اشتراكك بنجاح! ينتهي اشتراكك في {new_expiry.strftime('%Y-%m-%d %H:%M:%S')}"
                    else:
                        logging.error(f"Failed to add user {user['telegram_id']} to channel.")
                        message = "حدث خطأ أثناء إضافة المستخدم إلى القناة. سيتم المحاولة لاحقًا."

            else:
                # إنشاء اشتراك جديد
                new_expiry = datetime.now() + timedelta(minutes=3)
                success = await add_user_to_channel(user['telegram_id'], subscription_type)
                if success:
                    await connection.execute(
                        """
                        INSERT INTO subscriptions (user_id, subscription_type, expiry_date, is_active)
                        VALUES ($1, $2, $3, TRUE)
                        """, user['id'], subscription_type, new_expiry
                    )
                    # جدولة التذكيرات والإزالة
                    await schedule_reminders(connection, user['id'], subscription_type, new_expiry)
                    await schedule_remove_user(connection, user['id'], new_expiry)
                    message = f"تم اشتراكك بنجاح! ينتهي اشتراكك في {new_expiry.strftime('%Y-%m-%d %H:%M:%S')}"
                else:
                    logging.error(f"Failed to add user {user['telegram_id']} to channel.")
                    message = "حدث خطأ أثناء إضافة المستخدم إلى القناة. سيتم المحاولة لاحقًا."

        logging.info(f"Subscription processed successfully for user_id: {user['id']}")
        return jsonify({"message": message, "expiry_date": new_expiry.strftime('%Y-%m-%d %H:%M:%S')}), 200

    except Exception as e:
        logging.error(f"Error in subscribe: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

# نقطة API للتجديد
@app.route("/api/renew", methods=["POST"])
async def renew_subscription():
    conn = None
    try:
        # استقبال البيانات من الطلب
        data = await request.json
        telegram_id = data.get("telegram_id")
        subscription_type = data.get("subscription_type")

        if not telegram_id or not subscription_type:
            return await jsonify({"error": "Missing telegram_id or subscription_type"}), 400

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
            SELECT expiry_date, is_active FROM subscriptions
            WHERE user_id = ? AND subscription_type = ?
        """, (user_id, subscription_type))
        existing_subscription = cursor.fetchone()

        if existing_subscription:
            expiry_date, is_active = existing_subscription
            try:
                current_expiry = datetime.strptime(expiry_date, "%Y-%m-%d %H:%M:%S")

                if is_active:
                    # تمديد الاشتراك الحالي
                    new_expiry = (current_expiry + timedelta(minutes=3)).strftime("%Y-%m-%d %H:%M:%S")
                else:
                    # إعادة تفعيل الاشتراك
                    new_expiry = (datetime.now() + timedelta(minutes=3)).strftime("%Y-%m-%d %H:%M:%S")

                    # محاولة إعادة إضافة المستخدم إلى القناة
                    success = add_user_to_channel(telegram_id, subscription_type)
                    if not success:
                        return await jsonify({"error": "Failed to re-add user to the channel"}), 500

                    # تحديث حالة الاشتراك
                    cursor.execute("""
                        UPDATE subscriptions
                        SET is_active = TRUE
                        WHERE user_id = ? AND subscription_type = ?
                    """, (user_id, subscription_type))

                # تحديث تاريخ انتهاء الاشتراك
                cursor.execute("""
                    UPDATE subscriptions
                    SET expiry_date = ?
                    WHERE user_id = ? AND subscription_type = ?
                """, (new_expiry, user_id, subscription_type))

                # إعادة جدولة التذكيرات والإزالة
                await schedule_reminders(user_id, subscription_type, new_expiry)
                await schedule_remove_user(user_id, subscription_type, new_expiry)

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
    try:
        # الحصول على `telegram_id` من بارامترات الطلب
        telegram_id = int(request.args.get("telegram_id"))
        logging.info(f"Received telegram_id: {telegram_id}, type: {type(telegram_id)}")
        # التحقق من وجود `telegram_id`
        if not telegram_id:
            logging.error("Missing 'telegram_id'")
            return jsonify({"error": "Missing 'telegram_id'"}), 400

        async with app.db_pool.acquire() as connection:
            # البحث عن المستخدم في قاعدة البيانات
            user = await connection.fetchrow(
                "SELECT * FROM users WHERE telegram_id = $1", telegram_id
            )

            # التحقق من وجود المستخدم
            if not user:
                logging.error(f"No user found with telegram_id: {telegram_id}")
                return jsonify({"error": "User not found"}), 404

            # جلب جميع الاشتراكات للمستخدم
            user_subscriptions = await connection.fetch(
                "SELECT * FROM subscriptions WHERE user_id = $1", user['id']
            )

            # التحقق من وجود اشتراكات
            if not user_subscriptions:
                logging.info(f"No active subscriptions found for user_id: {user['id']}")
                return jsonify({"message": "No active subscriptions"}), 404

            # تجهيز البيانات لإرجاعها
            result = [
                {
                    "subscription_type": sub['subscription_type'],
                    "expiry_date": sub['expiry_date'].strftime('%Y-%m-%d %H:%M:%S'),
                    "is_active": sub['is_active']
                }
                for sub in user_subscriptions
            ]

        # إرجاع البيانات
        logging.info(f"Subscriptions retrieved for user_id: {user['id']}")
        return jsonify({"subscriptions": result}), 200

    except Exception as e:
        # معالجة أي أخطاء غير متوقعة
        logging.error(f"Error in check_subscription: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500



@app.route("/", endpoint="index")
async def home():
    return await render_template("index.html")

@app.route("/shop", endpoint="shop")
async def shop():
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