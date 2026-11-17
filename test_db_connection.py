import asyncio
import asyncpg


async def test_connection():
    try:
        conn = await asyncpg.connect(
            host="127.0.0.1",
            port=5433,
            user="postgres",
            password="password",
            database="episode_db"
        )

        print("Connection successful!")

        result = await conn.fetchval("SELECT current_database()")
        print("Database:", result)

        await conn.close()

    except Exception as e:
        print("Connection failed:", repr(e))


asyncio.run(test_connection())