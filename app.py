import os
from flask import Flask, request, jsonify, render_template
import logging
import sqlite3
from datetime import datetime, timedelta
from flask_cors import CORS

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
def subscribe():
    try:
        data = request.json
        logging.info(f"Received data: {data}")

        telegram_id = data.get("telegram_id")
        subscription_type = data.get("subscription_type")
        logging.debug(f"Received telegram_id: {telegram_id}")
        logging.debug(f"Received subscription_type: {subscription_type}")

        if not telegram_id or not subscription_type:
            return jsonify({"error": "Missing telegram_id or subscription_type"}), 400

        valid_subscription_types = ["Forex VIP Channel", "Crypto VIP Channel"]
        if subscription_type not in valid_subscription_types:
            return jsonify({"error": "Invalid subscription type"}), 400

        conn = sqlite3.connect("database/database.db", timeout=10)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR IGNORE INTO users (telegram_id)
            VALUES (?)
        """, (telegram_id,))

        cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"error": "User not found"}), 404

        user_id = user[0]

        cursor.execute("""
            SELECT expiry_date FROM subscriptions
            WHERE user_id = ? AND subscription_type = ?
        """, (user_id, subscription_type))
        existing_subscription = cursor.fetchone()

        if existing_subscription:
            try:
                current_expiry = datetime.fromisoformat(existing_subscription[0])
                new_expiry = (current_expiry + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("""
                    UPDATE subscriptions
                    SET expiry_date = ?
                    WHERE user_id = ? AND subscription_type = ?
                """, (new_expiry, user_id, subscription_type))
                message = f"تم تجديد اشتراك {subscription_type} حتى {new_expiry}"
            except ValueError:
                return jsonify({"error": "Invalid date format in database."}), 500
        else:
            new_expiry = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO subscriptions (user_id, subscription_type, expiry_date)
                VALUES (?, ?, ?)
            """, (user_id, subscription_type, new_expiry))
            message = f"تم الاشتراك في {subscription_type} بنجاح! ينتهي الاشتراك في {new_expiry}"

        conn.commit()
        conn.close()

        return jsonify({"message": message, "expiry_date": new_expiry}), 200

    except sqlite3.OperationalError as e:
        logging.error(f"Database error: {str(e)}")
        return jsonify({"error": "Database error, please try again later."}), 500

    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# نقطة API للتجديد
@app.route("/api/renew", methods=["POST"])
def renew_subscription():
    data = request.json  # استلام البيانات من واجهة المستخدم
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
        SELECT expiry_date FROM subscriptions
        WHERE user_id = ? AND subscription_type = ?
    """, (user_id, subscription_type))
    existing_subscription = cursor.fetchone()

    if existing_subscription:
        current_expiry = datetime.strptime(existing_subscription[0], "%Y-%m-%d")
        new_expiry = (current_expiry + timedelta(days=30)).strftime("%Y-%m-%d")
        cursor.execute("""
            UPDATE subscriptions
            SET expiry_date = ?
            WHERE user_id = ? AND subscription_type = ?
        """, (new_expiry, user_id, subscription_type))
        conn.commit()
        conn.close()
        return jsonify({"message": f"تم تجديد الاشتراك حتى {new_expiry}"}), 200
    else:
        conn.close()
        return jsonify({"error": "Subscription not found"}), 404

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
    data = request.json
    telegram_id = data.get('telegramId')
    username = data.get('username')

    if not telegram_id:
        logging.error("Telegram ID is missing in the request.")
        return jsonify({"success": False, "message": "Telegram ID is required!"}), 400

    logging.info(f"Verified Telegram ID: {telegram_id}, Username: {username}")
    return jsonify({"success": True, "message": "Telegram ID verified successfully!"})

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
    # قراءة المنفذ من متغير البيئة $PORT، مع قيمة افتراضية 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
