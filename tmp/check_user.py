import mysql.connector
import json

def check_user():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="123456",
            database="student_helper"
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email='nagi@gmail.com'")
        user = cursor.fetchone()
        if user:
            # Print as JSON for clarity
            print(json.dumps(user, indent=4, default=str))
        else:
            print("User not found")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_user()
