import os
from flask import Flask, render_template

app = Flask(__name__)

# بيانات الاشتراكات الوهمية
subscriptions = [
    {
        "id": 1,
        "name": "Forex VIP Channel",
        "price": 5,
        "details": "اشترك في قناة الفوركس للحصول على توصيات مميزة.",
        "image_url": "assets/images/forex_channel.jpg"
    },
    {
        "id": 2,
        "name": "Crypto VIP Channel",
        "price": 10,
        "details": "اشترك في قناة الكريبتو للحصول على توصيات مميزة.",
        "image_url": "assets/images/crypto_channel.jpg"
    }
]

user_profile = {
    "name": "محمد أحمد",
    "profile_image": "assets/images/user-placeholder.jpg",
    "subscriptions": [
        {
            "name": "Forex VIP Channel",
            "expiry_date": "2025-01-31",
            "image_url": "assets/images/forex_channel.jpg"
        },
        {
            "name": "Crypto VIP Channel",
            "expiry_date": "2025-02-15",
            "image_url": "assets/images/crypto_channel.jpg"
        }
    ]
}


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/shop")
def shop():
    return render_template('shop.html', subscriptions=subscriptions)

@app.route("/profile")
def profile():
    return render_template("profile.html", user=user_profile)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
