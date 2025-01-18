import asyncpg
from datetime import datetime
from config import DATABASE_CONFIG
import logging


# وظيفة لإنشاء اتصال بقاعدة البيانات
async def create_db_pool():
    return await asyncpg.create_pool(**DATABASE_CONFIG)

# استعلامات إدارة المستخدمين
async def add_user(connection, telegram_id, username=None, full_name=None):
    """إضافة مستخدم جديد أو تحديث بيانات مستخدم موجود."""
    try:
        await connection.execute("""
            INSERT INTO users (telegram_id, username, full_name)
            VALUES ($1, $2, $3)
            ON CONFLICT (telegram_id) DO UPDATE
            SET username = $2, full_name = $3
        """, telegram_id, username, full_name)
        logging.info(f"User {telegram_id} added/updated successfully.")
        return True
    except Exception as e:
        logging.error(f"Error adding/updating user {telegram_id}: {e}")
        return False


async def get_user(connection, telegram_id):
    """جلب المستخدم من قاعدة البيانات باستخدام Telegram ID."""
    try:
        user = await connection.fetchrow("""
            SELECT * FROM users WHERE telegram_id = $1
        """, telegram_id)
        if user:
            logging.info(f"User {telegram_id} found in database.")
        else:
            logging.warning(f"User {telegram_id} not found in database.")
        return user
    except Exception as e:
        logging.error(f"Error fetching user {telegram_id}: {e}")
        return None


# استعلامات إدارة الاشتراكات
async def add_subscription(connection, user_id, subscription_type, expiry_date, is_active=True):
    """إضافة اشتراك جديد."""
    try:
        await connection.execute("""
            INSERT INTO subscriptions (user_id, subscription_type, expiry_date, is_active)
            VALUES ($1, $2, $3, $4)
        """, user_id, subscription_type, expiry_date, is_active)
        logging.info(f"Subscription for user {user_id} with type {subscription_type} added. Expiry date: {expiry_date}.")
        return True
    except Exception as e:
        logging.error(f"Error adding subscription for user {user_id} with type {subscription_type}: {e}")
        return False


async def update_subscription(connection, subscription_id, subscription_type, new_expiry_date, is_active):
    """تحديث الاشتراك بتمديد مدة الاشتراك وتحديث حالته."""
    try:
        await connection.execute("""
            UPDATE subscriptions
            SET expiry_date = $1, is_active = $2
            WHERE id = $3 AND subscription_type = $4
        """, new_expiry_date, is_active, subscription_id, subscription_type)
        logging.info(f"Subscription {subscription_id} with type {subscription_type} updated: expiry_date={new_expiry_date}, is_active={is_active}.")
        return True
    except Exception as e:
        logging.error(f"Error updating subscription {subscription_id} with type {subscription_type}: {e}")
        return False



async def get_subscription(connection, user_id, subscription_type):
    """جلب الاشتراك الحالي للمستخدم."""
    try:
        subscription = await connection.fetchrow("""
            SELECT * FROM subscriptions
            WHERE user_id = $1 AND subscription_type = $2
        """, user_id, subscription_type)

        # التحقق مما إذا كان الاشتراك قد انتهى
        if subscription and subscription['expiry_date'] < datetime.now():
            await connection.execute("""
                UPDATE subscriptions
                SET is_active = FALSE
                WHERE id = $1
            """, subscription['id'])
            subscription = {**subscription, 'is_active': False}

        return subscription
    except Exception as e:
        logging.error(f"Error retrieving subscription for user {user_id} with type {subscription_type}: {e}")
        return None


async def deactivate_subscription(connection, user_id, subscription_type=None):
    """تعطيل جميع الاشتراكات أو اشتراك معين للمستخدم."""
    try:
        if subscription_type:
            await connection.execute("""
                UPDATE subscriptions
                SET is_active = FALSE
                WHERE user_id = $1 AND subscription_type = $2
            """, user_id, subscription_type)
            logging.info(f"Subscription for user {user_id} with type {subscription_type} deactivated.")
        else:
            await connection.execute("""
                UPDATE subscriptions
                SET is_active = FALSE
                WHERE user_id = $1
            """, user_id)
            logging.info(f"All subscriptions for user {user_id} deactivated.")
        return True
    except Exception as e:
        logging.error(f"Error deactivating subscription(s) for user {user_id}: {e}")
        return False

# استعلامات إدارة المهام المجدولة
async def add_scheduled_task(connection, task_type, user_id, subscription_type, execute_at):
    """إضافة مهمة مجدولة جديدة مرتبطة بنوع الاشتراك."""
    try:
        await connection.execute("""
            INSERT INTO scheduled_tasks (task_type, user_id, subscription_type, execute_at, status)
            VALUES ($1, $2, $3, $4, 'pending')
        """, task_type, user_id, subscription_type, execute_at)
        logging.info(f"Scheduled task '{task_type}' for user {user_id} and subscription type {subscription_type} at {execute_at}.")
        return True
    except Exception as e:
        logging.error(f"Error adding scheduled task '{task_type}' for user {user_id} and subscription type {subscription_type}: {e}")
        return False


async def get_active_subscriptions(connection, user_id, subscription_type=None):
    """جلب جميع الاشتراكات أو اشتراك محدد للمستخدم، مع تحديث is_active إذا لزم."""
    try:
        if subscription_type:
            subscriptions = await connection.fetch("""
                SELECT * FROM subscriptions
                WHERE user_id = $1 AND subscription_type = $2
            """, user_id, subscription_type)
        else:
            subscriptions = await connection.fetch("""
                SELECT * FROM subscriptions
                WHERE user_id = $1
            """, user_id)

        # تحقق من تاريخ انتهاء كل اشتراك وقم بتحديث حالة is_active إذا انتهى
        for subscription in subscriptions:
            if subscription['expiry_date'] < datetime.now() and subscription['is_active']:
                await connection.execute("""
                    UPDATE subscriptions
                    SET is_active = FALSE
                    WHERE id = $1
                """, subscription['id'])
                subscription['is_active'] = False

        return subscriptions
    except Exception as e:
        logging.error(f"Error fetching active subscriptions for user {user_id}: {e}")
        return []

async def get_pending_tasks(connection, subscription_type=None):
    """جلب المهام المجدولة الجاهزة للتنفيذ، مع خيار تصفيتها بناءً على نوع الاشتراك."""
    try:
        if subscription_type:
            tasks = await connection.fetch("""
                SELECT * FROM scheduled_tasks
                WHERE status = 'pending' AND execute_at <= NOW() AND subscription_type = $1
            """, subscription_type)
        else:
            tasks = await connection.fetch("""
                SELECT * FROM scheduled_tasks
                WHERE status = 'pending' AND execute_at <= NOW()
            """)

        logging.info(f"Pending tasks retrieved: {len(tasks)} tasks found.")
        return tasks
    except Exception as e:
        logging.error(f"Error fetching pending tasks: {e}")
        return []


async def update_task_status(connection, task_id, status):
    """تحديث حالة المهمة."""
    try:
        await connection.execute("""
            UPDATE scheduled_tasks
            SET status = $1
            WHERE id = $2
        """, status, task_id)
        logging.info(f"Task {task_id} status updated to {status}.")
        return True
    except Exception as e:
        logging.error(f"Error updating task status for task {task_id}: {e}")
        return False
