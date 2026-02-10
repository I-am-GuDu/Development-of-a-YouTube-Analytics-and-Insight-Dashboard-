#!/usr/bin/env python3
"""
Test database connection and basic functionality
"""
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from data_storage.database import DatabaseManager
    
    print("Testing database connection...")
    db_manager = DatabaseManager()
    
    if db_manager.test_connection():
        print("✅ Database connection successful!")
        
        # Test if tables exist
        from sqlalchemy import text
        with db_manager.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result]
            print(f"📊 Found tables: {tables}")
            
            if 'videos' in tables:
                # Check if there's any data
                result = conn.execute(text("SELECT COUNT(*) FROM videos"))
                count = result.scalar()
                print(f"📹 Videos in database: {count}")
                
                if count > 0:
                    # Show sample data
                    result = conn.execute(text("""
                        SELECT channel_id, COUNT(*) as video_count 
                        FROM videos 
                        GROUP BY channel_id 
                        LIMIT 5
                    """))
                    channels = result.fetchall()
                    print("📺 Channels with data:")
                    for channel_id, video_count in channels:
                        print(f"  - {channel_id}: {video_count} videos")
            else:
                print("⚠️  No 'videos' table found. You may need to initialize the schema.")
                
    else:
        print("❌ Database connection failed!")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()