import asyncio
from db_queries import create_db_pool, add_user, get_user

async def test_queries():
    # إنشاء اتصال بقاعدة البيانات
    db_pool = await create_db_pool()

    async with db_pool.acquire() as connection:
        # إضافة مستخدم جديد
        print("Adding user...")
        await add_user(connection, 12345678, username="john_doe", full_name="John Doe")

        # جلب بيانات المستخدم
        print("Fetching user...")
        user = await get_user(connection, 12345678)
        print("User data:", user)

# تشغيل الاختبار
if __name__ == "__main__":
    asyncio.run(test_queries())

