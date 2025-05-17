import requests
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

print("🔧 SQLite Connection Fixer 🔧")
print("-" * 40)

# Get absolute path to database
db_path = os.path.abspath('sample_huge.db')
print(f"Database path: {db_path}")
print(f"File exists: {os.path.exists(db_path)}")
print(f"File size: {os.path.getsize(db_path) / (1024*1024):.2f} MB")

# 1. Create connection string with forward slashes
db_path_forward = db_path.replace('\\', '/')
sqlite_url = f"sqlite:///{db_path_forward}"
print(f"\nConnection URL to use: {sqlite_url}")

# 2. Update the .env file with the connection string
print("\nUpdating .env file with proper connection URL...")
env_path = os.path.join(os.getcwd(), '.env')

# Read existing .env file
env_contents = {}
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                env_contents[key] = value

# Update/add database settings
env_contents['DATABASE_URL'] = sqlite_url
env_contents['DB_TYPE'] = 'sqlite'
env_contents['DB_NAME'] = 'sample_huge'
env_contents.pop('DB_HOST', None)  # Remove if exists
env_contents.pop('DB_PORT', None)  # Remove if exists
env_contents.pop('DB_USER', None)  # Remove if exists
env_contents.pop('DB_PASSWORD', None)  # Remove if exists

# Write back to .env file
with open(env_path, 'w') as f:
    for key, value in env_contents.items():
        f.write(f"{key}={value}\n")

print("✅ .env file updated successfully!")
print("\n3. Next steps:")
print("   1. Restart your application")
print("   2. The SQLite database should now be connected automatically")
print("\nNote: If you're still having issues, directly set these values in your application:")
print(f"    - DATABASE_URL = {sqlite_url}")
print("    - DB_TYPE = sqlite")
print("    - DB_NAME = sample_huge") 