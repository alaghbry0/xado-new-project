import os
import asyncpg
from dotenv import load_dotenv
load_dotenv()  # تحميل متغيرات البيئة



# إعداد اتصال قاعدة البيانات
DATABASE_CONFIG = {
    'user': os.environ.get('DB_USER', 'exaado_user'),
    'password': os.environ.get('DB_PASSWORD', 'Moh*770175667'),
    'database': os.environ.get('DB_NAME', 'exaado_db'),
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': int(os.environ.get('DB_PORT', 5432)),
}

async def connect_to_db():
    pool = await asyncpg.create_pool(
        dsn=DATABASE_URI,
        command_timeout=60,
        server_settings={
            "client_encoding": "UTF8"  # فرض الترميز
        }
    )
    return pool



DATABASE_URI = f"postgresql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"

TELEGRAM_BOT_TOKEN = "7490344438:AAHtSw6V0vTn7i1mIIuGPgJ_PqDTJXKAeos"