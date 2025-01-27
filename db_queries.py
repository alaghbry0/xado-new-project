import asyncpg
from datetime import datetime
from config import DATABASE_CONFIG
import logging


# وظيفة لإنشاء اتصال بقاعدة البيانات
async def create_db_pool():
    return await asyncpg.create_pool(**DATABASE_CONFIG)

# استعلامات إدارة المستخدمين
async def add_user(connection, telegram_id, username=None, full_name=None, wallet_app=None):
    """إضافة مستخدم جديد أو تحديث بيانات مستخدم موجود."""
    try:
        await connection.execute("""
            INSERT INTO users (telegram_id, username, full_name, wallet_app)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (telegram_id) DO UPDATE
            SET username = $2, full_name = $3, wallet_app = $4
        """, telegram_id, username, full_name, wallet_app)
        logging.info(f"User {telegram_id} added/updated successfully.")
        return True
    except Exception as e:
        logging.error(f"Error adding/updating user {telegram_id}: {e}")
        return False



async def get_user(connection, telegram_id):
    """جلب بيانات المستخدم من قاعدة البيانات باستخدام Telegram ID."""
    try:
        user = await connection.fetchrow("""
            SELECT telegram_id, username, full_name, wallet_address, wallet_app, 
                   CASE 
                       WHEN wallet_address IS NOT NULL THEN 'connected'
                       ELSE 'disconnected'
                   END AS wallet_status
            FROM users
            WHERE telegram_id = $1
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
async def add_subscription(connection, telegram_id: int, channel_id: int, subscription_type_id: int, expiry_date, is_active=True):
    """
    إضافة اشتراك جديد.
    """
    try:
        await connection.execute("""
            INSERT INTO subscriptions (telegram_id, channel_id, subscription_type_id, expiry_date, is_active)
            VALUES ($1, $2, $3, $4, $5)
        """, telegram_id, channel_id, subscription_type_id, expiry_date, is_active)
        logging.info(f"تمت إضافة اشتراك جديد للمستخدم {telegram_id} في القناة {channel_id}. ينتهي في: {expiry_date}.")
        return True
    except Exception as e:
        logging.error(f"خطأ أثناء إضافة اشتراك للمستخدم {telegram_id} في القناة {channel_id}: {e}")
        return False





async def update_subscription(connection, telegram_id: int, channel_id: int, subscription_type_id: int, new_expiry_date, is_active=True):
    """
    تحديث الاشتراك بتمديد مدة الاشتراك وتحديث حالته.
    """
    try:
        query = """
            UPDATE subscriptions
            SET expiry_date = $1, is_active = $2, subscription_type_id = $3
            WHERE telegram_id = $4 AND channel_id = $5
        """
        await connection.execute(query, new_expiry_date, is_active, subscription_type_id, telegram_id, channel_id)
        logging.info(f"تم تحديث الاشتراك للمستخدم {telegram_id} في القناة {channel_id}: expiry_date={new_expiry_date}, is_active={is_active}.")
        return True
    except Exception as e:
        logging.error(f"خطأ أثناء تحديث الاشتراك للمستخدم {telegram_id} في القناة {channel_id}: {e}")
        return False




async def get_subscription(connection, telegram_id: int, channel_id: int):
    """
    جلب الاشتراك الحالي للمستخدم.
    """
    try:
        subscription = await connection.fetchrow("""
            SELECT * FROM subscriptions
            WHERE telegram_id = $1 AND channel_id = $2
        """, telegram_id, channel_id)

        # التحقق مما إذا كان الاشتراك قد انتهى
        if subscription and subscription['expiry_date'] < datetime.now():
            await connection.execute("""
                UPDATE subscriptions
                SET is_active = FALSE
                WHERE id = $1
            """, subscription['id'])
            subscription = {**subscription, 'is_active': False}
            logging.info(f"Subscription for user {telegram_id} in channel {channel_id} marked as inactive.")

        return subscription
    except Exception as e:
        logging.error(f"Error retrieving subscription for user {telegram_id} in channel {channel_id}: {e}")
        return None


async def deactivate_subscription(connection, telegram_id: int, channel_id: int = None):
    """
    تعطيل جميع الاشتراكات أو اشتراك معين للمستخدم.
    """
    try:
        if channel_id:
            await connection.execute("""
                UPDATE subscriptions
                SET is_active = FALSE
                WHERE telegram_id = $1 AND channel_id = $2
            """, telegram_id, channel_id)
            logging.info(f"Subscription for user {telegram_id} with channel {channel_id} deactivated.")
        else:
            await connection.execute("""
                UPDATE subscriptions
                SET is_active = FALSE
                WHERE telegram_id = $1
            """, telegram_id)
            logging.info(f"All subscriptions for user {telegram_id} deactivated.")
        return True
    except Exception as e:
        logging.error(f"Error deactivating subscription(s) for user {telegram_id}: {e}")
        return False


# استعلامات إدارة المهام المجدولة
async def add_scheduled_task(connection, task_type, telegram_id, channel_id, execute_at, clean_up=True):
    """
    إضافة مهمة مجدولة جديدة مع دعم حذف المهام القديمة.
    """
    try:
        # إذا كان clean_up مفعلاً، حذف المهام القديمة
        if clean_up:
            await connection.execute("""
                DELETE FROM scheduled_tasks
                WHERE telegram_id = $1 AND channel_id = $2 AND task_type = $3
            """, telegram_id, channel_id, task_type)

        # إضافة المهمة الجديدة إلى جدول التذكيرات
        await connection.execute("""
            INSERT INTO scheduled_tasks (task_type, telegram_id, channel_id, execute_at, status)
            VALUES ($1, $2, $3, $4, 'pending')
        """, task_type, telegram_id, channel_id, execute_at)

        logging.info(
            f"Scheduled task '{task_type}' for user {telegram_id} and channel {channel_id} at {execute_at}."
        )
        return True
    except Exception as e:
        logging.error(
            f"Error adding scheduled task '{task_type}' for user {telegram_id} and channel {channel_id}: {e}"
        )
        return False

async def get_pending_tasks(connection, channel_id=None):
    """
    جلب المهام المعلقة التي يجب تنفيذها في الوقت الحالي.
    """
    try:
        logging.info("تنفيذ استعلام جلب المهام المعلقة.")
        logging.info(f"الوقت الحالي على الخادم: {datetime.now()} (المنطقة الزمنية للخادم)")
        logging.info("استعلام المهام المعلقة التي حالتها 'pending' وزمن تنفيذها <= الآن.")

        # الاستعلام الأساسي
        base_query = """
            SELECT *
            FROM scheduled_tasks
            WHERE status = 'pending'
              AND execute_at <= NOW()
        """
        parameters = []

        # إذا تم تحديد channel_id، إضافة شرط إضافي
        if channel_id:
            base_query += " AND channel_id = $1"
            parameters.append(channel_id)

        # تنفيذ الاستعلام
        tasks = await connection.fetch(base_query, *parameters)

        # تسجيل النتائج
        logging.info(f"تم جلب {len(tasks)} مهمة معلقة (channel_id: {channel_id}).")
        for task in tasks:
            logging.info(f"Task Details: {task}")
        return tasks
    except Exception as e:
        logging.error(f"خطأ أثناء استعلام المهام المعلقة (channel_id: {channel_id}): {e}")
        return []


async def update_task_status(connection, task_id, status):
    """
    تحديث حالة المهمة في جدول scheduled_tasks.
    Args:
        connection: اتصال قاعدة البيانات.
        task_id: معرف المهمة التي سيتم تحديث حالتها.
        status: الحالة الجديدة التي سيتم تعيينها للمهمة.
    """
    query = """
        UPDATE scheduled_tasks
        SET status = $1
        WHERE id = $2
    """
    try:
        # تنفيذ التحديث
        await connection.execute(query, status, task_id)
        logging.info(f"تم تحديث حالة المهمة {task_id} إلى {status}.")
        return True
    except Exception as e:
        logging.error(f"خطأ أثناء تحديث حالة المهمة {task_id}. الاستعلام: {query}, المعلمات: [status={status}, task_id={task_id}], الخطأ: {e}")
        return False
