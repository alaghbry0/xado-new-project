import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncpg
from config import DATABASE_CONFIG
from scheduler import start_scheduler



async def main():
    # إنشاء اتصال بقاعدة البيانات
    connection = await asyncpg.connect(**DATABASE_CONFIG)

    # استدعِ start_scheduler لتشغيل الجدولة
    start_scheduler(connection)

    # أضف انتظارًا غير نهائي لتبقى الحلقة تعمل
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
