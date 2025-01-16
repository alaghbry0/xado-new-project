import asyncpg
from datetime import datetime
from config import DATABASE_CONFIG


# وظيفة لإنشاء اتصال بقاعدة البيانات
async def create_db_pool():
    return await asyncpg.create_pool(**DATABASE_CONFIG)

# استعلامات إدارة المستخدمين
async def add_user(connection, telegram_id, username=None, full_name=None):
    print(f"Adding user: telegram_id={telegram_id}, username={username}, full_name={full_name}")
    await connection.execute("""
        INSERT INTO users (telegram_id, username, full_name)
        VALUES ($1, $2, $3)
        ON CONFLICT (telegram_id) DO UPDATE
        SET username = $2, full_name = $3
    """, telegram_id, username, full_name)

    # جلب البيانات بعد الإضافة
    result = await connection.fetchrow("SELECT * FROM users WHERE telegram_id = $1", telegram_id)
    print("Inserted user data:", result)  # استخدم المتغير لتجنب التحذير
    return result  # يمكنك إرجاع النتيجة إذا كنت تحتاجها


async def get_user(connection, telegram_id):
    """جلب المستخدم من قاعدة البيانات باستخدام Telegram ID."""
    logging.info(f"Received telegram_id: {telegram_id}, type: {type(telegram_id)}")

    return await connection.fetchrow("""
        SELECT * FROM users WHERE telegram_id = $1
    """, telegram_id)


# استعلامات إدارة الاشتراكات
async def add_subscription(connection, user_id, subscription_type, expiry_date):
    """إضافة اشتراك جديد."""
    await connection.execute("""
        INSERT INTO subscriptions (user_id, subscription_type, expiry_date, is_active)
        VALUES ($1, $2, $3, TRUE)
    """, user_id, subscription_type, expiry_date)

async def update_subscription(connection, subscription_id, new_expiry_date):
    """تحديث الاشتراك بتمديد مدة الاشتراك."""
    await connection.execute("""
        UPDATE subscriptions
        SET expiry_date = $1, is_active = TRUE
        WHERE id = $2
    """, new_expiry_date, subscription_id)

async def get_subscription(connection, user_id, subscription_type):
    """جلب الاشتراك الحالي للمستخدم."""
    return await connection.fetchrow("""
        SELECT * FROM subscriptions
        WHERE user_id = $1 AND subscription_type = $2
    """, user_id, subscription_type)

async def deactivate_subscription(connection, user_id):
    """تعطيل جميع الاشتراكات للمستخدم."""
    await connection.execute("""
        UPDATE subscriptions
        SET is_active = FALSE
        WHERE user_id = $1
    """, user_id)

# استعلامات إدارة المهام المجدولة
async def add_scheduled_task(connection, task_type, user_id, execute_at):
    """إضافة مهمة مجدولة جديدة."""
    await connection.execute("""
        INSERT INTO scheduled_tasks (task_type, user_id, execute_at, status)
        VALUES ($1, $2, $3, 'pending')
    """, task_type, user_id, execute_at)

async def get_pending_tasks(connection):
    """جلب المهام المجدولة الجاهزة للتنفيذ."""
    return await connection.fetch("""
        SELECT * FROM scheduled_tasks
        WHERE status = 'pending' AND execute_at <= NOW()
    """)

async def update_task_status(connection, task_id, status):
    """تحديث حالة المهمة."""
    await connection.execute("""
        UPDATE scheduled_tasks
        SET status = $1
        WHERE id = $2
    """, status, task_id)
