from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, send
import mysql.connector

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

socketio = SocketIO(app, cors_allowed_origins="*")
app.config['CORS_HEADERS'] = 'Content-Type'

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Mohak@12",
        database="student_helper",
        ssl_disabled=True
    )

def init_db():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Mohak@12",
        ssl_disabled=True
    )
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS student_helper")
    cursor.execute("USE student_helper")
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), email VARCHAR(255) UNIQUE, password VARCHAR(255), points INT DEFAULT 0, first_name VARCHAR(255), reputation INT DEFAULT 0, bounties_completed INT DEFAULT 0)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS requests (id INT AUTO_INCREMENT PRIMARY KEY, title VARCHAR(255), description TEXT, user_email VARCHAR(255), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, status VARCHAR(50), bounty INT, captured_by VARCHAR(255), solved BOOLEAN DEFAULT 0)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS answers (id INT AUTO_INCREMENT PRIMARY KEY, request_id INT, answer TEXT, email VARCHAR(255), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, accepted BOOLEAN DEFAULT 0)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS posts (id INT AUTO_INCREMENT PRIMARY KEY, first_name VARCHAR(255), title VARCHAR(255), content TEXT, user_email VARCHAR(255), bounty INT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS notifications (id INT AUTO_INCREMENT PRIMARY KEY, email VARCHAR(255), message TEXT, seen BOOLEAN DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    cursor.close()
    conn.close()

init_db()

@app.route("/")
def home():
    return "Student Helper Backend Running"

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    first_name = data.get("first_name")
    email = data.get("email")
    password = data.get("password")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if user:
            return jsonify({"message": "User already exists"})

        cursor.execute(
            "INSERT INTO users (first_name, email, password, points) VALUES (%s,%s,%s,%s)",
            (first_name, email, password, 0)
        )
        conn.commit()
        return jsonify({"message": "Registration successful"})
    finally:
        cursor.close()
        conn.close()

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT email, first_name, password FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if user and user["password"] == password:
            return jsonify({
                "message": "Login successful",
                "email": user["email"],
                "first_name": user["first_name"]
            })

        return jsonify({"message": "Invalid email or password"})
    finally:
        cursor.close()
        conn.close()

@app.route("/dashboard_metrics")
def dashboard_metrics():
    try:
        email = request.args.get("email")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            bounties_cleared = 0
            ledger_stake = 0
            pending = 0
            
            if email:
                cursor.execute("SELECT COUNT(*) FROM requests WHERE solved = 1 AND user_email = %s", (email,))
                r1 = cursor.fetchone()
                if r1 and r1[0] is not None:
                    bounties_cleared = int(r1[0])
                    
                cursor.execute("SELECT COALESCE(reputation, points, 0) FROM users WHERE email = %s", (email,))
                r2 = cursor.fetchone()
                if r2 and r2[0] is not None:
                    ledger_stake = int(r2[0])

            cursor.execute("SELECT COUNT(*) FROM requests WHERE status = 'open' AND solved = 0")
            r3 = cursor.fetchone()
            if r3 and r3[0] is not None:
                pending = int(r3[0])

            return jsonify({
                "bounties_cleared": bounties_cleared,
                "ledger_stake": ledger_stake,
                "pending_jobs": pending
            })
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        print("Dashboard Metrics Error:", e)
        return jsonify({"bounties_cleared": 0, "ledger_stake": 0, "pending_jobs": 0}), 200

@app.route("/leaderboard", methods=["GET"])
def leaderboard():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT first_name, email, 
                       COALESCE(reputation, points, 0) as reputation,
                       COALESCE(bounties_completed, 0) as bounties_completed
                FROM users
                ORDER BY COALESCE(reputation, points, 0) DESC
            """)
            users = cursor.fetchall()
            return jsonify(users)
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        return jsonify([]), 200

@app.route("/post_request", methods=["POST"])
def post_request():
    data = request.json
    title = data.get("title")
    description = data.get("description")
    email = data.get("email")
    bounty = data.get("bounty")

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO requests (title, description, user_email, bounty, status) VALUES (%s,%s,%s,%s,'open')",
            (title, description, email, bounty)
        )

        conn.commit()
        return jsonify({"message": "Request posted successfully"})
    finally:
        cursor.close()
        conn.close()

@app.route("/get_requests", methods=["GET"])
def get_requests():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM requests WHERE status = 'open' AND solved = 0 AND user_email IS NOT NULL AND user_email != '' ORDER BY created_at DESC")
            rows = cursor.fetchall()
            requests_list = []
            for r in rows:
                requests_list.append({
                    "id": r[0],
                    "title": r[1],
                    "description": r[2],
                    "email": r[3],
                    "created_at": r[4],
                    "status": r[5],
                    "bounty": r[6],
                    "captured_by": r[7] if len(r) > 7 else None,
                    "solved": bool(r[8]) if len(r) > 8 else False
                })
            return jsonify(requests_list)
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        print("Get Requests Error:", e)
        return jsonify([])

@app.route("/get_my_requests", methods=["GET"])
def get_my_requests():
    try:
        email = request.args.get("email")
        if not email:
            return jsonify([])
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM requests WHERE user_email = %s ORDER BY created_at DESC", (email,))
            rows = cursor.fetchall()
            requests_list = []
            for r in rows:
                requests_list.append({
                    "id": r[0],
                    "title": r[1],
                    "description": r[2],
                    "email": r[3],
                    "created_at": r[4],
                    "status": r[5],
                    "bounty": r[6],
                    "captured_by": r[7] if len(r) > 7 else None,
                    "solved": bool(r[8]) if len(r) > 8 else False
                })
            return jsonify(requests_list)
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        print("Get My Requests Error:", e)
        return jsonify([])

@app.route("/get_archived_requests", methods=["GET"])
def get_archived_requests():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM requests WHERE solved = 1 OR status = 'closed' ORDER BY created_at DESC")
            rows = cursor.fetchall()
            requests_list = []
            for r in rows:
                requests_list.append({
                    "id": r[0],
                    "title": r[1],
                    "description": r[2],
                    "email": r[3],
                    "created_at": r[4],
                    "status": r[5],
                    "bounty": r[6],
                    "captured_by": r[7] if len(r) > 7 else None,
                    "solved": bool(r[8]) if len(r) > 8 else False
                })
            return jsonify(requests_list)
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        print("Get Archived Requests Error:", e)
        return jsonify([])

@app.route("/post_answer", methods=["POST"])
def post_answer():
    data = request.json
    request_id = data["request_id"]
    answer = data["answer"]
    email = data["email"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("INSERT INTO answers (request_id, answer, email) VALUES (%s,%s,%s)", (request_id, answer, email))
        conn.commit()

        cursor.execute("SELECT user_email FROM requests WHERE id=%s", (request_id,))
        row = cursor.fetchone()
        if row:
            owner = row["user_email"]
            cursor.execute("INSERT INTO notifications (email,message) VALUES (%s,%s)", (owner,"Someone answered your request"))
            conn.commit()

        return jsonify({"message":"Answer posted successfully"})
    finally:
        cursor.close()
        conn.close()

@app.route("/get_answers/<int:request_id>", methods=["GET"])
def get_answers(request_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM answers WHERE request_id=%s", (request_id,))
        rows = cursor.fetchall()
        answers = []
        for r in rows:
            answers.append({
                "id": r[0],
                "request_id": r[1],
                "answer": r[2],
                "email": r[3]
            })
        return jsonify(answers)
    finally:
        cursor.close()
        conn.close()

@app.route("/accept_answer", methods=["POST"])
def accept_answer():
    data = request.json
    answer_id = data["answer_id"]
    request_id = data["request_id"]
    email = data["email"]

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE answers SET accepted = TRUE WHERE id = %s", (answer_id,))
        cursor.execute("UPDATE requests SET solved = TRUE WHERE id = %s", (request_id,))
        cursor.execute("UPDATE users SET points = points + 20 WHERE email = %s", (email,))
        
        conn.commit()
        return jsonify({"message": "Answer accepted"})
    finally:
        cursor.close()
        conn.close()

@socketio.on("message")
def handle_message(msg):
    print("Message:", msg)
    send(msg, broadcast=True)

@app.route("/update_reputation", methods=["POST"])
def update_reputation():
    data = request.json
    email = data.get("email")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE users
            SET reputation = reputation + 50,
                bounties_completed = bounties_completed + 1
            WHERE email = %s
        """, (email,))
        conn.commit()
        return jsonify({"message": "Updated"})
    finally:
        cursor.close()
        conn.close()

@app.route("/get_posts", methods=["GET"])
def get_posts():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT p.*, u.first_name 
            FROM posts p
            JOIN users u ON p.user_email = u.email
            ORDER BY p.created_at DESC
        """)
        posts = cursor.fetchall()
        for post in posts:
            if 'created_at' in post and post['created_at']:
                post['created_at'] = str(post['created_at'])
        return jsonify(posts)
    finally:
        cursor.close()
        conn.close()

@app.route("/create_post", methods=["POST"])
def create_post():
    data = request.json

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO posts (user_email, content, bounty) VALUES (%s, %s, %s)", (data["email"], data["content"], data["bounty"]))
        conn.commit()
        return jsonify({"message": "Post created"})
    finally:
        cursor.close()
        conn.close()

@app.route("/accept_post", methods=["POST"])
def accept_post():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE requests SET status = 'captured', captured_by = %s WHERE id = %s", (data["email"], data["post_id"]))

        conn.commit()
        return jsonify({"message": "accepted"})
    finally:
        cursor.close()
        conn.close()

@app.route("/user_stats", methods=["GET"])
def user_stats():
    try:
        email = request.args.get("email")
        if not email:
            return jsonify({"first_name": "", "email": "", "reputation": 0, "bounties_completed": 0}), 200
            
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT first_name, email, 
                       COALESCE(reputation, points, 0) as reputation,
                       COALESCE(bounties_completed, 0) as bounties_completed
                FROM users
                WHERE email = %s
            """, (email,))
            user = cursor.fetchone()
            
            if user:
                return jsonify(user)
            else:
                return jsonify({"first_name": "", "email": email, "reputation": 0, "bounties_completed": 0}), 200
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        return jsonify({"first_name": "", "email": request.args.get("email") or "", "reputation": 0, "bounties_completed": 0}), 200

if __name__ == "__main__":
    socketio.run(app, debug=True)
