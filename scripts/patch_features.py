import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path='backend/.env')

def patch():
    config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", "Mohak@12"),
        "database": os.getenv("DB_NAME", "student_helper"),
        "port": int(os.getenv("DB_PORT", 3306))
    }
    
    conn = mysql.connector.connect(**config)
    cursor = conn.conn.cursor() if hasattr(conn, 'conn') else conn.cursor()
    
    print("Applying schema changes...")
    
    # Feature 1: Bounty & Escrow
    try:
        cursor.execute("ALTER TABLE requests ADD COLUMN escrowed_bounty INT DEFAULT 0")
        print("Added escrowed_bounty to requests")
    except Exception as e:
        print("escrowed_bounty likely exists:", e)
        
    # Feature 2: Expiry
    try:
        cursor.execute("ALTER TABLE requests ADD COLUMN expires_at TIMESTAMP NULL")
        print("Added expires_at to requests")
    except Exception as e:
        print("expires_at likely exists:", e)
        
    # Feature 3: Claims Table
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS claims (
                id INT AUTO_INCREMENT PRIMARY KEY,
                request_id INT,
                user_email VARCHAR(255),
                claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_claim (request_id, user_email)
            )
        """)
        print("Created claims table")
    except Exception as e:
        print("Error creating claims table:", e)
        
    conn.commit()
    cursor.close()
    conn.close()
    print("Patching complete.")

if __name__ == "__main__":
    patch()
