import asyncio
from sqlalchemy import text
from database import engine, init_db
from utils.auth import get_password_hash

async def seed_fix():
    print("🚀 Running Simplified User Credential Fix...")
    await init_db()
    
    async with engine.begin() as conn:
        hp_admin = get_password_hash("admin123")
        hp_faculty = get_password_hash("faculty123")
        hp_preethika = get_password_hash("preethika")

        users_to_seed = [
            ("Institutional Admin", "admin@example.com", hp_admin, "admin", "Administration"),
            ("Lead Faculty", "faculty@example.com", hp_faculty, "faculty", "General"),
            ("Preethika", "preethika.se23@bitsathy.ac.in", hp_preethika, "student", "Computer Science")
        ]

        # Truncate users first to ensure clean state for these 3 if needed, 
        # or just insert/update
        await conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        for name, email, hp, role, dept in users_to_seed:
            # Delete if exists to avoid unique constraint issues if updating role
            await conn.execute(text("DELETE FROM users WHERE email = :email"), {"email": email})
            await conn.execute(text("""
                INSERT INTO users (name, email, password, role, department) 
                VALUES (:name, :email, :hp, :role, :dept)
            """), {"name": name, "email": email, "hp": hp, "role": role, "dept": dept})
        await conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        
    print("✅ USER CREDENTIALS RESTORED.")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(seed_fix())
