import os
import subprocess
import time
import zipfile
import sys

ZIP_FILE = "project_data.zip"
DB_CONTAINER = "opensource_daily_report_mysql"
DB_USER = "root"
DB_PASS = "changeme-StrongPass123"
DB_NAME = "github_daily_report"
DUMP_FILE = "db_dump.sql"

def run_command(command):
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    return True

def main():
    if not os.path.exists(ZIP_FILE):
        print(f"Error: {ZIP_FILE} not found.")
        return

    print(f"Unzipping {ZIP_FILE}...")
    with zipfile.ZipFile(ZIP_FILE, 'r') as zip_ref:
        zip_ref.extractall(".")
    print("Unzip complete.")

    if not os.path.exists(DUMP_FILE):
        print(f"Error: {DUMP_FILE} not found after unzip.")
        return

    print("Waiting for MySQL container to be ready...")
    # Simple check if container is running
    if not run_command(f"docker ps | grep {DB_CONTAINER}"):
        print("MySQL container is not running. Please start it with 'docker-compose up -d'.")
        return

    print("Importing database...")
    
    # Read the dump file
    try:
        with open(DUMP_FILE, 'r') as f:
            sql_content = f.read()
    except Exception as e:
        print(f"Failed to read {DUMP_FILE}: {e}")
        return

    # Use docker exec to import
    cmd = [
        "docker", "exec", "-i", DB_CONTAINER, 
        "mysql", "-u", DB_USER, f"-p{DB_PASS}", DB_NAME
    ]
    
    print(f"Executing database import...")
    result = subprocess.run(cmd, input=sql_content, text=True, capture_output=True)
    
    if result.returncode == 0:
        print("Database import successful.")
    else:
        print(f"Database import failed: {result.stderr}")

    print("Initialization complete.")
    print("You can now delete db_dump.sql if you wish.")

if __name__ == "__main__":
    main()
