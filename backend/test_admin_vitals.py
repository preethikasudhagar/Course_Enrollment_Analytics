import asyncio
from database import AsyncSessionLocal
from models.models import User, UserRole
from routes.analytics import get_admin_vitals, refresh_admin_vitals
import json
import traceback

async def test():
    try:
        async with AsyncSessionLocal() as db:
            print("Refreshing vitals...")
            await refresh_admin_vitals(db)
            
            # Now fetch from cache
            from utils.cache import analytics_cache
            res = analytics_cache.get_precomputed("admin_vitals")
            with open("admin_vitals_out.json", "w") as f:
                json.dump(res, f, indent=2, default=str)
    except Exception as e:
        with open("admin_vitals_error.txt", "w") as f:
            f.write(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test())
