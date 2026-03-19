import asyncio
from sqlalchemy import text
from database import engine, init_db

async def verify():
    await init_db()
    async with engine.connect() as conn:
        for email in ['admin@example.com', 'faculty@example.com', 'preethika.se23@bitsathy.ac.in']:
            res = await conn.execute(text("SELECT email, role FROM users WHERE email = :email"), {"email": email})
            row = res.fetchone()
            if row:
                print(f"FOUND: {row[0]} (Role: {row[1]})")
            else:
                print(f"MISSING: {email}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(verify())
