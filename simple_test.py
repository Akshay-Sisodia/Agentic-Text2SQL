import os
from sqlalchemy import create_engine, text

# Hard-coded exact path with forward slashes
db_path = "C:/Users/akshaySisodia/Desktop/projects/Agentic-Text2SQL/sample_huge.db"
print(f"Database path: {db_path}")
print(f"File exists: {os.path.exists(db_path)}")

# Create SQLAlchemy engine with URI format
connection_url = f"sqlite:///{db_path}"
print(f"Connection URL: {connection_url}")

try:
    # Create engine and test connection
    engine = create_engine(connection_url, echo=True)
    
    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("Connection successful!")
        
    print("\nTEST PASSED! Use this connection string in your application:")
    print(connection_url)
    
except Exception as e:
    print(f"\nError: {e}")
    print("\nTry these alternatives:")
    print(f"1. sqlite:////{db_path}")  # Four slashes
    print(f"2. sqlite:///{db_path.replace('/', '\\')}")  # Using backslashes 