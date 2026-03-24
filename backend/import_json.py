import json
import os
from sqlalchemy import insert
from models.models import Base

async def import_data(db):
    try:
        seed_path = os.path.join(os.path.dirname(__file__), "seed_data.json")
        if not os.path.exists(seed_path):
            print(f"Seed file not found at {seed_path}")
            return
            
        with open(seed_path, "r") as f:
            data = json.load(f)
            
        print("Starting cloud data import from JSON...")
        
        for table in Base.metadata.sorted_tables:
            table_name = table.name
            if table_name in data and data[table_name]:
                rows = data[table_name]
                print(f"Importing {len(rows)} records into {table_name}...")
                
                from sqlalchemy.dialects.mysql import insert as mysql_insert
                for row in rows:
                    try:
                        insert_stmt = mysql_insert(table).values(**row)
                        on_dup_stmt = insert_stmt.on_duplicate_key_update(**row)
                        await db.execute(on_dup_stmt)
                    except Exception as ins_err:
                        print(f"Skipping a row in {table_name}: {ins_err}")
                
        await db.commit()
        print("Legacy Data successfully restored!")
        
        # Rename so it doesn't run twice
        os.rename(seed_path, seed_path + ".applied")
    except Exception as e:
        print(f"Import failed completely: {e}")
        await db.rollback()
