import os
import sqlite3
from sqlalchemy import create_engine, text
import traceback

# Get the absolute path to the database
db_path = os.path.abspath('sample_huge.db')
print("\n1. DATABASE PATH CHECK")
print(f"Absolute path: {db_path}")
print(f"File exists: {os.path.exists(db_path)}")
print(f"File size: {os.path.getsize(db_path) / (1024*1024):.2f} MB")

# Test direct SQLite connection
print("\n2. DIRECT SQLITE CONNECTION TEST")
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 5")
    tables = cursor.fetchall()
    print("Connection successful!")
    print(f"Tables found: {[t[0] for t in tables]}")
    conn.close()
except Exception as e:
    print(f"Direct SQLite connection failed: {str(e)}")
    traceback.print_exc()

# Test SQLAlchemy connection with standard URL format
print("\n3. SQLALCHEMY CONNECTION TEST")
# Convert Windows backslashes to forward slashes
db_path_forward = db_path.replace('\\', '/')
sqlite_url = f"sqlite:///{db_path_forward}"
print(f"Using SQLAlchemy URL: {sqlite_url}")

try:
    engine = create_engine(sqlite_url)
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print("SQLAlchemy connection successful!")
        
        # Try to query tables
        result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table' LIMIT 5"))
        tables = result.fetchall()
        print(f"Tables found: {[t[0] for t in tables]}")
except Exception as e:
    print(f"SQLAlchemy connection failed: {str(e)}")
    traceback.print_exc()

# Test alternative SQLite URL format with 4 slashes for absolute Windows paths
print("\n4. ALTERNATIVE SQLALCHEMY URL FORMAT TEST")
sqlite_url_alt = f"sqlite:////{db_path_forward}"
print(f"Using alternative URL: {sqlite_url_alt}")

try:
    engine = create_engine(sqlite_url_alt)
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print("Alternative SQLAlchemy connection successful!")
except Exception as e:
    print(f"Alternative connection failed: {str(e)}")
    traceback.print_exc()

# Generate recommendations
print("\n5. RECOMMENDED CONNECTION SETTINGS")
print(f"✅ For your database at: {db_path}")
print("Try these connection URLs in your application:")
print(f"Option 1: sqlite:///{db_path_forward}")
print(f"Option 2: sqlite:////{db_path_forward}")
print("Option 3: sqlite:///C:/Users/akshaySisodia/Desktop/projects/Agentic-Text2SQL/sample_huge.db") 