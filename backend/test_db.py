import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from urllib.parse import quote_plus

async def test_conn():
    password = quote_plus("Preethika_13#")
    url = f"mysql+aiomysql://root:{password}@localhost:3306/course_analytics_db"
    engine = create_async_engine(url)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("Connection successful!")
            
            # Check if tables exist
            result = await conn.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result.all()]
            print(f"Tables: {tables}")
            
    except Exception as e:
        print(f"Connection failed: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_conn())
