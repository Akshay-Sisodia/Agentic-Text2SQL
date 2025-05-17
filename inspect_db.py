import sqlite3
import os

# Path to the sample database
DB_PATH = "sample_huge.db"

def inspect_database():
    """Print the schema and sample data from the database"""
    if not os.path.exists(DB_PATH):
        print(f"Database file {DB_PATH} does not exist.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print(f"Found {len(tables)} tables in the database:")
    for i, table in enumerate(tables):
        table_name = table[0]
        print(f"\n{i+1}. Table: {table_name}")
        
        # Get table schema
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        print("Schema:")
        for col in columns:
            print(f"   {col[1]} ({col[2]})")
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        print(f"Row count: {row_count}")
        
        # Show sample data (5 rows)
        if row_count > 0:
            print("Sample data:")
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
            rows = cursor.fetchall()
            for row in rows:
                print(f"   {row}")
    
    conn.close()

if __name__ == "__main__":
    inspect_database() 