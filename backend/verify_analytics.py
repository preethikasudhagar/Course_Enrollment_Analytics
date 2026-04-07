import asyncio
import os
import sys
import json

# Ensure the parent directory is in sys.path to import local modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from database import AsyncSessionLocal
from routes.analytics import refresh_admin_vitals
from utils.cache import analytics_cache

async def verify():
    print("--- Analytics Verification ---")
    async with AsyncSessionLocal() as db:
        await refresh_admin_vitals(db)
        data = analytics_cache.get_precomputed("admin_vitals")
        
        if data:
            print("\nSUCCESS: Admin Vitals computed.")
            summary = data.get("summary", {})
            print(f"Total Enrollments: {summary.get('total_enrollments')}")
            print(f"Most Popular Course: {summary.get('most_popular_course')}")
            print(f"Utilization: {summary.get('utilization')}%")
            
            # Check Chart Data
            charts = data.get("charts", {})
            trends = charts.get("trends", [])
            print(f"Trends Months: {[t['month'] for t in trends]}")
            
            # Save to file for inspection
            with open("analytics_snapshot.json", "w") as f:
                json.dump(data, f, indent=2, default=str)
            print("\nFull snapshot saved to backend/analytics_snapshot.json")
        else:
            print("\nFAILURE: Analytics cache is still empty.")

if __name__ == "__main__":
    asyncio.run(verify())
