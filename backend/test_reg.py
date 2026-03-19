import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from models.models import User, UserRole
from database import Base, get_db
from schemas.user import UserCreate
from utils.auth import get_password_hash
from urllib.parse import quote_plus
import os

async def simulate_register():
    password = quote_plus("Preethika_13#")
    url = f"mysql+aiomysql://root:{password}@localhost:3306/course_analytics_db"
    engine = create_async_engine(url)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with AsyncSessionLocal() as db:
        try:
            # Simulate the registration logic
            email = "test_user@example.com"
            name = "Test User"
            raw_password = "password123"
            role = "student"
            
            new_user = User(
                name=name,
                email=email,
                password=get_password_hash(raw_password),
                role=UserRole(role)
            )
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            print(f"Registration successful for {new_user.email}, ID: {new_user.id}")
            
            # Clean up
            from sqlalchemy import delete
            await db.execute(delete(User).where(User.id == new_user.id))
            await db.commit()
            print("Cleanup successful.")
            
        except Exception as e:
            print(f"Registration simulation failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(simulate_register())
