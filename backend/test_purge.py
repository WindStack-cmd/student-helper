import app
conn = app.get_db_connection()
cursor = conn.cursor(dictionary=True)
email_to_purge = "124mohak6041@sjcem.edu.in"

cursor.execute("UPDATE requests SET status = 'open', captured_by = NULL WHERE captured_by = %s", (email_to_purge,))
print(f"uncaptured: {cursor.rowcount}")

cursor.execute("DELETE FROM claims WHERE request_id IN (SELECT id FROM requests WHERE user_email = %s)", (email_to_purge,))
print(f"claims on my requests: {cursor.rowcount}")

cursor.execute("DELETE FROM answers WHERE request_id IN (SELECT id FROM requests WHERE user_email = %s)", (email_to_purge,))
print(f"answers on my requests: {cursor.rowcount}")

cursor.execute("DELETE FROM answers WHERE email = %s", (email_to_purge,))
print(f"my answers: {cursor.rowcount}")

cursor.execute("DELETE FROM claims WHERE user_email = %s", (email_to_purge,))
print(f"my claims: {cursor.rowcount}")

cursor.execute("DELETE FROM requests WHERE user_email = %s", (email_to_purge,))
print(f"requests: {cursor.rowcount}")

cursor.execute("DELETE FROM posts WHERE user_email = %s", (email_to_purge,))
print(f"posts: {cursor.rowcount}")

cursor.execute("DELETE FROM notifications WHERE email = %s", (email_to_purge,))
print(f"notifications: {cursor.rowcount}")

cursor.execute("DELETE FROM users WHERE email = %s", (email_to_purge,))
print(f"users: {cursor.rowcount}")

conn.commit()
cursor.close()
conn.close()
