import mysql.connector
import json

def get_all_nagi():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="123456",
            database="student_helper"
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT email, first_name, name FROM users WHERE email LIKE '%nagi%'")
        users = cursor.fetchall()
        print(f"DEBUG: {users}")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_all_nagi()
