import sqlite3
from tabulate import tabulate

def view_data():
    conn = sqlite3.connect("database/database.db")
    cursor = conn.cursor()

    # عرض المستخدمين
    print("Users Table:")
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    if users:
        print(tabulate(users, headers=["ID", "Telegram ID", "Username", "Full Name"], tablefmt="pretty"))
    else:
        print("No users found.")

    # عرض الاشتراكات
    print("\nSubscriptions Table:")
    cursor.execute("""
        SELECT subscriptions.id, users.full_name, subscriptions.subscription_type, 
               subscriptions.expiry_date, subscriptions.is_active, subscriptions.reminders_sent
        FROM subscriptions
        JOIN users ON subscriptions.user_id = users.id
    """)
    subscriptions = cursor.fetchall()
    if subscriptions:
        print(tabulate(subscriptions, headers=["ID", "Full Name", "Type", "Expiry", "Active", "Reminders Sent"], tablefmt="pretty"))
    else:
        print("No subscriptions found.")

    # عرض المهام المجدولة
    print("\nScheduled Tasks Table:")
    cursor.execute("""
        SELECT scheduled_tasks.id, scheduled_tasks.task_type, users.full_name, 
               scheduled_tasks.execute_at, scheduled_tasks.status
        FROM scheduled_tasks
        JOIN users ON scheduled_tasks.user_id = users.id
    """)
    tasks = cursor.fetchall()
    if tasks:
        print(tabulate(tasks, headers=["ID", "Task Type", "Full Name", "Execute At", "Status"], tablefmt="pretty"))
    else:
        print("No scheduled tasks found.")

    conn.close()

if __name__ == "__main__":
    try:
        view_data()
    except Exception as e:
        print(f"Error occurred: {e}")
