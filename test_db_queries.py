import asyncio
from app import app,create_db_connection, close_resources
from scheduler import execute_scheduled_tasks

async def main():
    # قم بإنشاء اتصال بقاعدة البيانات
    await create_db_connection()
    # استدعي execute_scheduled_tasks مباشرة
    await execute_scheduled_tasks(app.db_pool)
    # أغلق اتصال قاعدة البيانات
    await close_resources()

if __name__ == "__main__":
    asyncio.run(main())
