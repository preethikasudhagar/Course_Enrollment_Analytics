import json
import os
from sqlalchemy import text
from models.models import Base

async def import_data(db):
    try:
        if not os.path.exists("seed_data.json"):
            return
            
        with open("seed_data.json", "r") as f:
            data = json.load(f)
            
        print("Starting cloud data import from JSON...")
        tables = [t.name for t in Base.metadata.sorted_tables]
        
        for table_name in tables:
            if table_name in data and data[table_name]:
                rows = data[table_name]
                print(f"Importing {len(rows)} records into {table_name}...")
                
                # Get columns ensuring we ignore any that don't exist
                keys = list(rows[0].keys())
                cols = ", ".join([f"`{k}`" for k in keys])
                vals = ", ".join([f":{k}" for k in keys])
                stmt = text(f"INSERT IGNORE INTO {table_name} ({cols}) VALUES ({vals})")
                
                for row in rows:
                    await db.execute(stmt, row)
                    
        await db.commit()
        print("Legacy Data successfully restored!")
        
        # Rename so it doesn't run twice
        os.rename("seed_data.json", "seed_data_applied.json")
    except Exception as e:
        print(f"Import failed: {e}")
        await db.rollback()
