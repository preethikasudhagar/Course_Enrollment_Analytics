import sys
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Default local database
LOCAL_URL = "mysql+aiomysql://root:Preethika_13%23@localhost:3306/course_analytics_db"

async def migrate_data(remote_url: str):
    print("Connecting to local database...")
    local_engine = create_async_engine(LOCAL_URL, echo=False)
    
    # Ensure aiomysql is used for remote
    if remote_url.startswith("mysql://"):
        remote_url = remote_url.replace("mysql://", "mysql+aiomysql://", 1)
    elif remote_url.startswith("mysql+pymysql://"):
        remote_url = remote_url.replace("mysql+pymysql://", "mysql+aiomysql://", 1)
        
    print("Connecting to remote database...")
    # Add support for SSL if it's Aiven/Railway
    connect_args = {}
    if "aivencloud.com" in remote_url or "railway.app" in remote_url:
        import ssl
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        connect_args["ssl"] = ssl_ctx
        if "?ssl-mode=" in remote_url:
            remote_url = remote_url.split("?ssl-mode=")[0]
        elif "&ssl-mode=" in remote_url:
            remote_url = remote_url.split("&ssl-mode=")[0]
    
    remote_engine = create_async_engine(remote_url, connect_args=connect_args, echo=False)
    
    tables = [
        "users", "courses", "enrollments", "notifications", "waitlist", 
        "system_settings", "system_activities", "otp_records", "suggestions",
        "faculty_performance", "analytics"
    ]
    
    try:
        async with local_engine.connect() as local_conn:
            async with remote_engine.begin() as remote_conn:
                # Disable foreign key checks for the transaction
                await remote_conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
                
                for table in tables:
                    try:
                        # fetch all
                        rows = await local_conn.execute(text(f"SELECT * FROM {table}"))
                        data = rows.fetchall()
                        if not data:
                            print(f"[{table}] is empty locally, skipping.")
                            continue
                            
                        keys = list(rows.keys())
                        print(f"[{table}] migrating {len(data)} rows...")
                        
                        # Clear existing data in remote table
                        await remote_conn.execute(text(f"DELETE FROM {table}"))
                        
                        # Insert records
                        cols_str = ", ".join(f"`{k}`" for k in keys)
                        vals_str = ", ".join(f":{k}" for k in keys)
                        insert_query = text(f"INSERT INTO {table} ({cols_str}) VALUES ({vals_str})")
                        
                        for row in data:
                            params = {k: v for k, v in zip(keys, row)}
                            await remote_conn.execute(insert_query, params)
                            
                        print(f"[{table}] successful.")
                    except Exception as e:
                        print(f"Error migrating {table}: {e}")
                        
                await remote_conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))
        print("\nAll done! Data migrated successfully.")
    except Exception as e:
        print("Migration failed:", e)
    finally:
        await local_engine.dispose()
        await remote_engine.dispose()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python migrate.py <REMOTE_DATABASE_URL>")
        sys.exit(1)
        
    asyncio.run(migrate_data(sys.argv[1]))
