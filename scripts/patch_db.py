import mysql.connector

def patch():
    c = mysql.connector.connect(host='127.0.0.1', user='root', password='Mohak@12', database='student_helper')
    cur = c.cursor()
    # Safely try adding user_email and created_at
    try:
        cur.execute("ALTER TABLE posts ADD COLUMN user_email VARCHAR(100)")
    except Exception as e:
        print("user_email exists or error:", e)

    try:
        cur.execute("ALTER TABLE posts ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    except Exception as e:
        print("created_at exists or error:", e)

    try:
        cur.execute("UPDATE posts SET user_email = 'system@node' WHERE user_email IS NULL")
    except Exception as e:
        print("update error:", e)

    c.commit()
    print("Patched successfully")

if __name__ == "__main__":
    patch()
