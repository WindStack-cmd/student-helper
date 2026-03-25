from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, send
import mysql.connector


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

socketio = SocketIO(app, cors_allowed_origins="*")
app.config['CORS_HEADERS'] = 'Content-Type'

# -----------------------------
# DATABASE CONNECTION FUNCTION
# -----------------------------

def get_db_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="Mohak@12",
        database="student_helper",
        ssl_disabled=True
    )

# -----------------------------
# HOME ROUTE
# -----------------------------

@app.route("/")
def home():
    return "Student Helper Backend Running"

# -----------------------------
# REGISTER USER
# -----------------------------
@app.route("/register", methods=["POST"])
def register():

    data = request.json

    first_name = data.get("first_name")
    email = data.get("email")
    password = data.get("password")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # check if user already exists
    cursor.execute(
        "SELECT * FROM users WHERE email=%s",
        (email,)
    )

    user = cursor.fetchone()

    if user:
        return jsonify({"message": "User already exists"})

    # insert user
    cursor.execute(
        "INSERT INTO users (first_name, email, password, points) VALUES (%s,%s,%s,%s)",
        (first_name, email, password, 0)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"message": "Registration successful"})

#-----------------------------
# LOGIN USER
#-----------------------------

@app.route("/login", methods=["POST"])
def login():

    data = request.json

    email = data.get("email")
    password = data.get("password")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT email, first_name, password FROM users WHERE email=%s",
        (email,)
    )

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if user and user["password"] == password:

        return jsonify({
            "message": "Login successful",
            "email": user["email"],
            "first_name": user["first_name"]
        })

    return jsonify({
        "message": "Invalid email or password"
    })
 

#-----------------------------
# DASHBOARD METRICS
#-----------------------------

@app.route("/dashboard_metrics")
def dashboard_metrics():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # total points from users table
    cursor.execute("SELECT SUM(points) as total_points FROM users")
    points_data = cursor.fetchone()

    points = points_data["total_points"] if points_data["total_points"] else 0

    # total requests
    cursor.execute("SELECT COUNT(*) as pending FROM requests")
    pending_data = cursor.fetchone()

    pending = pending_data["pending"] if pending_data else 0

    cursor.close()
    conn.close()

    return jsonify({
        "solved": 0,
        "points": points,
        "pending": pending
    })

#-----------------------------
# LEADERBOARD   
#-----------------------------

@app.route("/leaderboard", methods=["GET"])
def leaderboard():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT first_name, email, reputation, bounties_completed
                FROM users
                ORDER BY reputation DESC
            """)
            users = cursor.fetchall()
        except mysql.connector.Error:
            cursor.execute("""
                SELECT first_name, email, points as reputation, 0 as bounties_completed
                FROM users
                ORDER BY points DESC
            """)
            users = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify(users)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------------
# POST REQUEST
# -----------------------------

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
        "INSERT INTO requests (title, description, user_email, bounty, status) VALUES (%s,%s,%s,%s,'open')",
        (title, description, email, bounty)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"message": "Request posted successfully"})

# -----------------------------
# GET ALL REQUESTS
# -----------------------------

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

    cursor.close()
    conn.close()
    return jsonify(requests)

# -----------------------------
# POST ANSWER
# -----------------------------

@app.route("/post_answer", methods=["POST"])
def post_answer():

    data = request.json

    request_id = data["request_id"]
    answer = data["answer"]
    email = data["email"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # insert answer
    sql = "INSERT INTO answers (request_id, answer, email) VALUES (%s,%s,%s)"
    val = (request_id, answer, email)

    cursor.execute(sql,val)
    conn.commit()

    # ------------------------------
    # FIND REQUEST OWNER
    # ------------------------------

    cursor.execute(
        "SELECT email FROM requests WHERE id=%s",
        (request_id,)
    )

    owner = cursor.fetchone()["email"]

    # ------------------------------
    # CREATE NOTIFICATION
    # ------------------------------

    cursor.execute(
        "INSERT INTO notifications (email,message) VALUES (%s,%s)",
        (owner,"Someone answered your request")
    )

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"message":"Answer posted successfully"})
        
# -----------------------------
# GET ANSWERS
# -----------------------------

@app.route("/get_answers/<int:request_id>", methods=["GET"])
def get_answers(request_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    sql = "SELECT * FROM answers WHERE request_id=%s"
    val = (request_id,)

    cursor.execute(sql,val)

    rows = cursor.fetchall()

    answers = []

    for r in rows:
        answers.append({
            "id": r[0],
            "request_id": r[1],
            "answer": r[2],
            "email": r[3]
        })

    cursor.close()
    conn.close()

    return jsonify(answers)


# -----------------------------
# ACCEPT ANSWER
#-----------------------------

@app.route("/accept_answer", methods=["POST"])
def accept_answer():

    data = request.json
    answer_id = data["answer_id"]
    request_id = data["request_id"]
    email = data["email"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # mark answer accepted
    cursor.execute(
        "UPDATE answers SET accepted = TRUE WHERE id = %s",
        (answer_id,)
    )

    # mark request solved
    cursor.execute(
        "UPDATE requests SET solved = TRUE WHERE id = %s",
        (request_id,)
    )

    # give points to helper
    cursor.execute(
        "UPDATE users SET points = points + 20 WHERE email = %s",
        (email,)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"message": "Answer accepted"})

@socketio.on("message")
def handle_message(msg):

    print("Message:", msg)

    send(msg, broadcast=True)

# -----------------------------
# UPDATE REPUTATION 
#-----------------------------

@app.route("/update_reputation", methods=["POST"])
def update_reputation():
    data = request.json
    email = data.get("email")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET reputation = reputation + 50,
            bounties_completed = bounties_completed + 1
        WHERE email = %s
    """, (email,))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Updated"})

# -----------------------------
# GET ALL POSTS
#-----------------------------

@app.route("/get_posts", methods=["GET"])
def get_posts():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT p.*, u.first_name 
        FROM posts p
        JOIN users u ON p.user_email = u.email
        ORDER BY p.created_at DESC
    """)

    posts = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(posts)

# -----------------------------
# CREATE POST
#-----------------------------

@app.route("/create_post", methods=["POST"])
def create_post():
    data = request.json

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO posts (user_email, content, bounty)
        VALUES (%s, %s, %s)
    """, (
        data["email"],
        data["content"],
        data["bounty"]
    ))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Post created"})

# -----------------------------
# ACCEPT POST
#-----------------------------

@app.route("/accept_post", methods=["POST"])
def accept_post():
    data = request.json

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("ALTER TABLE requests ADD COLUMN captured_by VARCHAR(255)")
    except mysql.connector.Error:
        pass

    cursor.execute("""
        UPDATE requests
        SET status = 'captured', captured_by = %s
        WHERE id = %s
    """, (data["email"], data["post_id"]))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "accepted"})

# -----------------------------
# RUN SERVER
# -----------------------------

if __name__ == "__main__":
    socketio.run(app, debug=True)
