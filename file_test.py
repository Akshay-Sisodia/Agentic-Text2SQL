import os
from sqlalchemy import create_engine, text
import traceback
import sys

# Redirect output to a file
with open('sqlite_test_results.txt', 'w') as f:
    # Test with multiple connection string formats
    db_path = "C:/Users/akshaySisodia/Desktop/projects/Agentic-Text2SQL/sample_huge.db"
    
    f.write(f"Database path: {db_path}\n")
    f.write(f"File exists: {os.path.exists(db_path)}\n")
    f.write(f"File size: {os.path.getsize(db_path) / 1024 / 1024:.2f} MB\n\n")
    
    # Test various connection URL formats
    url_formats = [
        f"sqlite:///{db_path}",                       # Three slashes
        f"sqlite:////{db_path}",                      # Four slashes
        "sqlite:///sample_huge.db",                   # Relative path
        "sqlite:///C:/Users/akshaySisodia/Desktop/projects/Agentic-Text2SQL/sample_huge.db"  # Hard-coded
    ]
    
    for i, url in enumerate(url_formats, 1):
        f.write(f"TEST {i}: {url}\n")
        try:
            # Create engine with this URL
            engine = create_engine(url)
            
            # Try to connect and execute a simple query
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                f.write("[PASS] Connection successful!\n")
                
                # Try to get table names
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' LIMIT 5"))
                tables = [row[0] for row in result.fetchall()]
                f.write(f"[PASS] Tables found: {tables}\n")
                
            f.write("[PASS] TEST PASSED\n\n")
            
        except Exception as e:
            f.write(f"[FAIL] Connection failed: {str(e)}\n")
            f.write(traceback.format_exc())
            f.write("\n")
    
    f.write("\nRECOMMENDATIONS:\n")
    f.write("1. Use the exact connection URL format that worked above\n")
    f.write("2. Make sure the file path is accessible to the application\n")
    f.write("3. If using a relative path, make sure it's relative to the application's working directory\n")

print("Test complete! Results written to 'sqlite_test_results.txt'") 