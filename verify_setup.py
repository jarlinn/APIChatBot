#!/usr/bin/env python3
"""
Verification script to check database setup
Verifies that all tables exist and have the correct structure
"""

import sqlite3
import sys
import os

def verify_database():
    """Verify database setup"""
    db_path = "chatbot.db"
    
    if not os.path.exists(db_path):
        print("❌ Database file not found. Run 'alembic upgrade head' first.")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if all expected tables exist
        expected_tables = ['users', 'categories', 'questions', 'chunk_embeddings', 'alembic_version']
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        print("📊 Database verification:")
        print(f"   Database file: {db_path}")
        print(f"   Tables found: {len(existing_tables)}")
        
        missing_tables = set(expected_tables) - set(existing_tables)
        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
            return False
        
        # Check users table structure (should include 'name' field)
        cursor.execute("PRAGMA table_info(users);")
        user_columns = [row[1] for row in cursor.fetchall()]
        
        expected_user_columns = ['id', 'name', 'email', 'hashed_password', 'role', 'is_active']
        missing_columns = set(expected_user_columns) - set(user_columns)
        
        if missing_columns:
            print(f"❌ Missing columns in users table: {missing_columns}")
            return False
        
        # Check alembic version
        cursor.execute("SELECT version_num FROM alembic_version;")
        version = cursor.fetchone()
        
        print("✅ All tables exist with correct structure")
        print(f"✅ Current migration version: {version[0] if version else 'None'}")
        print("✅ Database setup is correct!")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Verifying database setup...")
    success = verify_database()
    sys.exit(0 if success else 1)
