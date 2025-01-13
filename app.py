import os
from aiohttp import web
import aiosqlite
from flask import Flask, request, jsonify, render_template
import logging
from datetime import datetime, timezone, timedelta
import sqlite3
from flask_cors import CORS
from database.db_utils import schedule_remove_user, schedule_reminders, add_user_to_channel, schedule_retry_add_to_channel
from scheduler import start_scheduler
from config import DATABASE_PATH


# إعداد تسجيل الأخطاء والمعلومات
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
CORS(app)  # تمكين CORS لجميع الطلبات


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
        data = await request.json
        logging.info(f"Received data: {data}")

        telegram_id = data.get("telegram_id")
        subscription_type = data.get("subscription_type")

        # التحقق من صحة البيانات المدخلة
        if not telegram_id or not subscription_type:
            logging.error("Missing 'telegram_id' or 'subscription_type'")
            return web.json_response({"error": "Missing 'telegram_id' or 'subscription_type'"}, status=400)

        valid_subscription_types = ["Forex VIP Channel", "Crypto VIP Channel"]
        if subscription_type not in valid_subscription_types:
            logging.error(f"Invalid subscription type: {subscription_type}")
            return web.json_response({"error": "Invalid subscription type"}, status=400)

        # فتح الاتصال بقاعدة البيانات
        async with aiosqlite.connect(DATABASE_PATH) as conn:
            cursor = await conn.cursor()

            # إضافة المستخدم إذا لم يكن موجودًا
            await cursor.execute("""
                INSERT OR IGNORE INTO users (telegram_id)
                VALUES (?)
            """, (telegram_id,))

            # الحصول على user_id
            await cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
            user = await cursor.fetchone()
            if not user:
                logging.error(f"User not found for telegram_id: {telegram_id}")
                return web.json_response({"error": "User not found"}, status=404)

            user_id = user[0]

            # التحقق من الاشتراك الحالي
            await cursor.execute("""
                SELECT expiry_date, is_active FROM subscriptions
                WHERE user_id = ? AND subscription_type = ?
            """, (user_id, subscription_type))
            existing_subscription = await cursor.fetchone()

            if existing_subscription:
                expiry_date, is_active = existing_subscription
                try:
                    current_expiry = datetime.strptime(expiry_date, "%Y-%m-%d %H:%M:%S")
                    if is_active:
                        # تمديد الاشتراك النشط
                        new_expiry = (current_expiry + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
                        message = f"تم تجديد اشتراكك حتى {new_expiry}"
                    else:
                        # إعادة تفعيل الاشتراك
                        new_expiry = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
                        success = await add_user_to_channel(telegram_id, subscription_type)
                        if success:
                            message = f"تم إعادة تفعيل اشتراكك بنجاح! ينتهي اشتراكك في {new_expiry}"
                            await cursor.execute("""
                                UPDATE subscriptions
                                SET is_active = TRUE
                                WHERE user_id = ? AND subscription_type = ?
                            """, (user_id, subscription_type))
                        else:
                            message = "حدث خطأ أثناء إضافة المستخدم إلى القناة. يرجى المحاولة لاحقًا."
                            await schedule_retry_add_to_channel(user_id, subscription_type)

                    # تحديث تاريخ انتهاء الاشتراك
                    await cursor.execute("""
                        UPDATE subscriptions
                        SET expiry_date = ?
                        WHERE user_id = ? AND subscription_type = ?
                    """, (new_expiry, user_id, subscription_type))
                except ValueError as e:
                    logging.error(f"Error parsing expiry_date: {expiry_date} - {str(e)}")
                    return web.json_response({"error": "Invalid date format in database."}, status=500)
            else:
                # اشتراك جديد
                new_expiry = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
                success = await add_user_to_channel(telegram_id, subscription_type)
                if success:
                    message = f"تم اشتراكك بنجاح! ينتهي اشتراكك في {new_expiry}"
                    await cursor.execute("""
                        INSERT INTO subscriptions (user_id, subscription_type, expiry_date, is_active)
                        VALUES (?, ?, ?, TRUE)
                    """, (user_id, subscription_type, new_expiry))

                    # جدولة التذكيرات والإزالة
                    await schedule_reminders(user_id, subscription_type, new_expiry)
                    await schedule_remove_user(user_id, subscription_type, new_expiry)
                else:
                    message = "حدث خطأ أثناء إضافة المستخدم إلى القناة. يرجى المحاولة لاحقًا."
                    await schedule_retry_add_to_channel(user_id, subscription_type)

            # حفظ التغييرات
            await conn.commit()
            logging.info(f"Subscription processed successfully for user_id: {user_id}")
            return web.json_response({"message": message, "expiry_date": new_expiry}, status=200)

    except aiosqlite.OperationalError as e:
        logging.error(f"Database error: {e}")
        return web.json_response({"error": "Database error, please try again later."}, status=500)

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return web.json_response({"error": "An unexpected error occurred"}, status=500)
# نقطة API للتجديد
@app.route("/api/renew", methods=["POST"])
def renew_subscription():
    conn = None
    try:
        # استقبال البيانات من الطلب
        data = request.json
        telegram_id = data.get("telegram_id")
        subscription_type = data.get("subscription_type")

        if not telegram_id or not subscription_type:
            return jsonify({"error": "Missing telegram_id or subscription_type"}), 400

        conn = sqlite3.connect("database/database.db")
        cursor = conn.cursor()

        # الحصول على user_id
        cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"error": "User not found"}), 404

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
                        return jsonify({"error": "Failed to re-add user to the channel"}), 500

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
                schedule_reminders(user_id, subscription_type, new_expiry)
                schedule_remove_user(user_id, subscription_type, new_expiry)

                conn.commit()
                return jsonify({"message": f"تم تجديد الاشتراك حتى {new_expiry}"}), 200
            except ValueError as e:
                logging.error(f"Invalid date format: {expiry_date} - {str(e)}")
                return jsonify({"error": "Invalid date format in database."}), 500
        else:
            return jsonify({"error": "Subscription not found for the provided user and type"}), 404
    except Exception as e:
        logging.error(f"Unexpected error in /api/renew: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500
    finally:
        if conn:
            conn.close()

# نقطة API للتحقق من الاشتراك
@app.route("/api/check_subscription", methods=["GET"])
def check_subscription():
    telegram_id = request.args.get("telegram_id")

    if not telegram_id:
        return jsonify({"error": "Missing telegram_id"}), 400

    conn = sqlite3.connect("database/database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT subscriptions.subscription_type, subscriptions.expiry_date
        FROM subscriptions
        JOIN users ON subscriptions.user_id = users.id
        WHERE users.telegram_id = ?
    """, (telegram_id,))
    subscriptions_data = cursor.fetchall()
    conn.close()

    if not subscriptions_data:
        return jsonify({"message": "No active subscriptions"}), 404

    result = [{"type": sub[0], "expiry_date": sub[1]} for sub in subscriptions_data]
    return jsonify({"subscriptions": result}), 200


@app.route("/", endpoint="index")
def home():
    return render_template("index.html")

@app.route("/shop", endpoint="shop")
def shop():
    return render_template("shop.html", subscriptions=subscriptions)

@app.route('/api/verify', methods=['POST'])
def verify_user():
    try:
        # استخراج البيانات من الطلب
        data = request.json
        telegram_id = data.get('telegramId')
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
        return jsonify({
            "success": True,
            "message": "Telegram ID verified successfully!",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "telegramId": telegram_id,
                "username": username
            }
        }), 200

    except Exception as e:
        # تسجيل أي أخطاء غير متوقعة
        logging.error(f"Unexpected error in /api/verify: {e}")
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred!"
        }), 500
@app.route("/profile", endpoint="profile")
def profile():
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
    return render_template("profile.html", user=user)


if __name__ == "__main__":
    start_scheduler()  # تشغيل جدولة المهام
    # قراءة المنفذ من متغير البيئة $PORT، مع قيمة افتراضية 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
