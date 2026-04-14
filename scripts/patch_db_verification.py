import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME", "student_helper"),
    "port": int(os.getenv("DB_PORT", 3306)),
}

def patch_db():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("Applying database changes for Email Verification System...")
        
        alter_statements = [
            "ALTER TABLE users ADD COLUMN is_verified TINYINT(1) DEFAULT 0",
            "ALTER TABLE users ADD COLUMN verification_token VARCHAR(64) DEFAULT NULL",
            "ALTER TABLE users ADD COLUMN token_expires_at DATETIME DEFAULT NULL",
            "ALTER TABLE users ADD COLUMN created_unverified_at DATETIME DEFAULT NULL"
        ]
        
        for statement in alter_statements:
            try:
                cursor.execute(statement)
                print(f"Executed: {statement}")
            except mysql.connector.Error as err:
                if err.errno == 1060: # Column already exists
                    print(f"Column already exists: {statement.split('ADD COLUMN')[1].strip().split()[0]}")
                else:
                    print(f"Error executing {statement}: {err}")
        
        conn.commit()
        cursor.close()
        conn.close()
        print("Database patch completed successfully.")
        
    except mysql.connector.Error as err:
        print(f"Connection error: {err}")

if __name__ == "__main__":
    patch_db()
