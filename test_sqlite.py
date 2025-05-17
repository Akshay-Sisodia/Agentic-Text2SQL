"""Test script to verify that the sample database connection works correctly."""

import os
import sqlite3
from sqlalchemy import create_engine, text
from app.core.database import SAMPLE_DB_PATH, get_engine

def main():
    """Test the sample database connection."""
    print(f"Sample database path: {SAMPLE_DB_PATH}")
    print(f"Database exists: {os.path.exists(SAMPLE_DB_PATH)}")
    
    # Test direct SQLite connection
    print("\nTesting direct SQLite connection:")
    try:
        conn = sqlite3.connect(SAMPLE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = cursor.fetchall()
        print(f"Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Test a query
        cursor.execute("SELECT COUNT(*) FROM products")
        count = cursor.fetchone()[0]
        print(f"Product count: {count}")
        conn.close()
        print("Direct SQLite connection successful!")
    except Exception as e:
        print(f"Error with direct connection: {str(e)}")
    
    # Test SQLAlchemy connection
    print("\nTesting SQLAlchemy connection:")
    try:
        # Get engine using the sample database URL
        engine = get_engine(f"sqlite:///{SAMPLE_DB_PATH}")
        
        # Connect and list tables
        with engine.connect() as connection:
            result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"))
            tables = result.fetchall()
            print(f"Found {len(tables)} tables via SQLAlchemy:")
            for table in tables:
                print(f"  - {table[0]}")
            
            # Test a query
            result = connection.execute(text("SELECT COUNT(*) FROM products"))
            count = result.fetchone()[0]
            print(f"Product count via SQLAlchemy: {count}")
        
        print("SQLAlchemy connection successful!")
    except Exception as e:
        print(f"Error with SQLAlchemy connection: {str(e)}")

if __name__ == "__main__":
    main() 