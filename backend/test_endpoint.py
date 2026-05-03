import requests
import json
import app
import os

conn = app.get_db_connection()
cursor = conn.cursor(dictionary=True)
email = "test_purge@example.com"
cursor.execute("DELETE FROM users WHERE email = %s", (email,))
cursor.execute("INSERT INTO users (first_name, name, email, password, points, reputation) VALUES ('test', 'test', %s, 'hash', 100, 100)", (email,))
conn.commit()
user_id = cursor.lastrowid
print("Inserted user:", user_id)

token = app.generate_jwt_token(email, user_id)

try:
    res = requests.post("http://localhost:5001/purge_user", json={"email": email}, headers={"Authorization": f"Bearer {token}"})
    print(res.status_code, res.json())
except Exception as e:
    print(e)

cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
print("User after purge:", cursor.fetchone())
