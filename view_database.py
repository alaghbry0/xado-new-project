import sqlite3

def view_data():
    conn = sqlite3.connect("database/database.db")
    cursor = conn.cursor()

    # عرض المستخدمين
    print("Users:")
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    for user in users:
        print(f"ID: {user[0]}, Telegram ID: {user[1]}, Username: {user[2]}, Full Name: {user[3]}")

    # عرض الاشتراكات
    print("\nSubscriptions:")
    cursor.execute("SELECT subscriptions.id, users.full_name, subscriptions.subscription_type, subscriptions.expiry_date "
                   "FROM subscriptions "
                   "JOIN users ON subscriptions.user_id = users.id")
    subscriptions = cursor.fetchall()
    for subscription in subscriptions:
        print(f"Subscription ID: {subscription[0]}, User: {subscription[1]}, "
              f"Type: {subscription[2]}, Expiry: {subscription[3]}")

    conn.close()

if __name__ == "__main__":
    try:
        view_data()
    except Exception as e:
        print(f"Error occurred: {e}")
