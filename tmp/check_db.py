import mysql.connector
import os

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "123456",
    "database": "student_helper",
    "ssl_disabled": True,
}

def check_user():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email='nagi@gmail.com'")
        user = cursor.fetchone()
        if user:
            print(f"User found: {user}")
        else:
            print("User NOT found")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_user()
