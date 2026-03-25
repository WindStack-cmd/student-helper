from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, send
import sqlite3

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

socketio = SocketIO(app, cors_allowed_origins="*")
app.config['CORS_HEADERS'] = 'Content-Type'

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_db_connection(as_dict=False):
    conn = sqlite3.connect('student_helper.db')
    if as_dict:
        conn.row_factory = dict_factory
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT UNIQUE, password TEXT, points INTEGER DEFAULT 0, first_name TEXT, reputation INTEGER DEFAULT 0, bounties_completed INTEGER DEFAULT 0)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS requests (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, description TEXT, user_email TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, status TEXT, bounty INTEGER, captured_by TEXT, solved BOOLEAN DEFAULT 0)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS answers (id INTEGER PRIMARY KEY AUTOINCREMENT, request_id INTEGER, answer TEXT, email TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, accepted BOOLEAN DEFAULT 0)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY AUTOINCREMENT, first_name TEXT, title TEXT, content TEXT, user_email TEXT, bounty INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS notifications (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, message TEXT, seen BOOLEAN DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    try:
        cur.execute("ALTER TABLE requests ADD COLUMN captured_by TEXT")
    except:
        pass
        
    conn.commit()
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

    conn = get_db_connection(True)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email=?", (email,))
    user = cursor.fetchone()

    if user:
        conn.close()
        return jsonify({"message": "User already exists"})

    cursor.execute(
        "INSERT INTO users (first_name, email, password, points) VALUES (?,?,?,?)",
        (first_name, email, password, 0)
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Registration successful"})

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    conn = get_db_connection(True)
    cursor = conn.cursor()
    cursor.execute("SELECT email, first_name, password FROM users WHERE email=?", (email,))
    user = cursor.fetchone()
    conn.close()

    if user and user["password"] == password:
        return jsonify({
            "message": "Login successful",
            "email": user["email"],
            "first_name": user["first_name"]
        })

    return jsonify({"message": "Invalid email or password"})

@app.route("/dashboard_metrics")
def dashboard_metrics():
    conn = get_db_connection(True)
    cursor = conn.cursor()

    cursor.execute("SELECT SUM(points) as total_points FROM users")
    points_data = cursor.fetchone()
    points = points_data["total_points"] if points_data and points_data["total_points"] else 0

    cursor.execute("SELECT COUNT(*) as pending FROM requests")
    pending_data = cursor.fetchone()
    pending = pending_data["pending"] if pending_data else 0

    conn.close()
    return jsonify({
        "solved": 0,
        "points": points,
        "pending": pending
    })

@app.route("/leaderboard", methods=["GET"])
def leaderboard():
    try:
        conn = get_db_connection(True)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT first_name, email, reputation, bounties_completed FROM users ORDER BY reputation DESC")
            users = cursor.fetchall()
        except:
            cursor.execute("SELECT first_name, email, points as reputation, 0 as bounties_completed FROM users ORDER BY points DESC")
            users = cursor.fetchall()

        conn.close()
        return jsonify(users)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/post_request", methods=["POST"])
def post_request():
    data = request.json
    title = data.get("title")
    description = data.get("description")
    email = data.get("email")
    bounty = data.get("bounty")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO requests (title, description, user_email, bounty, status) VALUES (?,?,?,?,'open')",
        (title, description, email, bounty)
    )

    conn.commit()
    conn.close()
    return jsonify({"message": "Request posted successfully"})

@app.route("/get_requests", methods=["GET"])
def get_requests():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM requests")
    rows = cursor.fetchall()
    requests = []
    for r in rows:
        requests.append({
            "id": r[0],
            "title": r[1],
            "description": r[2],
            "email": r[3],
            "created_at": r[4],
            "status": r[5],
            "bounty": r[6]
        })
    conn.close()
    return jsonify(requests)

@app.route("/post_answer", methods=["POST"])
def post_answer():
    data = request.json
    request_id = data["request_id"]
    answer = data["answer"]
    email = data["email"]

    conn = get_db_connection(True)
    cursor = conn.cursor()

    cursor.execute("INSERT INTO answers (request_id, answer, email) VALUES (?,?,?)", (request_id, answer, email))
    conn.commit()

    cursor.execute("SELECT user_email FROM requests WHERE id=?", (request_id,))
    row = cursor.fetchone()
    if row:
        owner = row["user_email"]
        cursor.execute("INSERT INTO notifications (email,message) VALUES (?,?)", (owner,"Someone answered your request"))
        conn.commit()

    conn.close()
    return jsonify({"message":"Answer posted successfully"})
        
@app.route("/get_answers/<int:request_id>", methods=["GET"])
def get_answers(request_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM answers WHERE request_id=?", (request_id,))
    rows = cursor.fetchall()
    answers = []
    for r in rows:
        answers.append({
            "id": r[0],
            "request_id": r[1],
            "answer": r[2],
            "email": r[3]
        })
    conn.close()
    return jsonify(answers)

@app.route("/accept_answer", methods=["POST"])
def accept_answer():
    data = request.json
    answer_id = data["answer_id"]
    request_id = data["request_id"]
    email = data["email"]

    conn = get_db_connection(True)
    cursor = conn.cursor()

    cursor.execute("UPDATE answers SET accepted = TRUE WHERE id = ?", (answer_id,))
    cursor.execute("UPDATE requests SET solved = TRUE WHERE id = ?", (request_id,))
    cursor.execute("UPDATE users SET points = points + 20 WHERE email = ?", (email,))
    
    conn.commit()
    conn.close()
    return jsonify({"message": "Answer accepted"})

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

    cursor.execute("UPDATE users SET reputation = reputation + 50, bounties_completed = bounties_completed + 1 WHERE email = ?", (email,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Updated"})

@app.route("/get_posts", methods=["GET"])
def get_posts():
    conn = get_db_connection(True)
    cursor = conn.cursor()

    cursor.execute("SELECT p.*, u.first_name FROM posts p JOIN users u ON p.user_email = u.email ORDER BY p.created_at DESC")
    posts = cursor.fetchall()

    conn.close()
    return jsonify(posts)

@app.route("/create_post", methods=["POST"])
def create_post():
    data = request.json

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO posts (user_email, content, bounty) VALUES (?, ?, ?)", (data["email"], data["content"], data["bounty"]))
    conn.commit()
    conn.close()
    return jsonify({"message": "Post created"})

@app.route("/accept_post", methods=["POST"])
def accept_post():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE requests SET status = 'captured', captured_by = ? WHERE id = ?", (data["email"], data["post_id"]))

    conn.commit()
    conn.close()
    return jsonify({"message": "accepted"})

if __name__ == "__main__":
    socketio.run(app, debug=True)
