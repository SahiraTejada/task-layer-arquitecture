from app.config.database import engine, SessionLocal
from app.models.user import User
from app.models.task import Task
from app.models.tag import Tag
from sqlalchemy import text

def test_sqlite_connection():
    """Test SQLite database connection and basic operations"""
    
    # Test connection
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ SQLite connection successful!")
            
        # Test session
        db = SessionLocal()
        
        # Test table creation
        print("📊 Database tables:")
        result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = result.fetchall()
        for table in tables:
            print(f"  - {table[0]}")
        
        # Test basic operations
        print("\n🧪 Testing basic operations...")
        
        # Count existing records
        user_count = db.query(User).count()
        task_count = db.query(Task).count()
        tag_count = db.query(Tag).count()
        
        print(f"Users: {user_count}")
        print(f"Tasks: {task_count}")
        print(f"Tags: {tag_count}")
        
        db.close()
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_sqlite_connection()