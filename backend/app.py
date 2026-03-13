from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, send
import mysql.connector

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")

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
        "SELECT email, name, password FROM users WHERE email=%s",
        (email,)
    )

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if user and user["password"] == password:

        return jsonify({
            "message": "Login successful",
            "email": user["email"],
            "first_name": user["name"]
        })

    return jsonify({
        "message": "Invalid email or password"
    })



# -----------------------------
# POST HELP REQUEST
# -----------------------------

@app.route("/post_request", methods=["POST"])
def post_request():
    data = request.json

    title = data["title"]
    description = data["description"]
    email = data["email"]

    conn = get_db_connection()
    cursor = conn.cursor()

    sql = "INSERT INTO requests (title,description,email) VALUES (%s,%s,%s)"
    val = (title,description,email)

    cursor.execute(sql,val)
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"message":"Request posted successfully"})

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
            "email": r[3]
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

@app.route("/leaderboard", methods=["GET"])
def leaderboard():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT email, points FROM users ORDER BY points DESC LIMIT 10"
    )

    users = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(users)


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
# RUN SERVER
# -----------------------------

if __name__ == "__main__":
  socketio.run(app, debug=True)