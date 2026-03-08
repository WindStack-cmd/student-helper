from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector

app = Flask(__name__)
CORS(app)

# MySQL connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Mohak@12",
    database="student_helper"
)

cursor = db.cursor()

@app.route("/")
def home():
    return "Student Helper Backend Running"


@app.route("/register", methods=["POST"])
def register():

    data = request.json
    name = data["name"]
    email = data["email"]
    password = data["password"]

    sql = "INSERT INTO users (name,email,password) VALUES (%s,%s,%s)"
    values = (name,email,password)

    cursor.execute(sql,values)
    db.commit()

    return jsonify({
        "message":"User registered successfully"
    })


@app.route("/login", methods=["POST"])
def login():

    data = request.json
    email = data["email"]
    password = data["password"]

    sql = "SELECT * FROM users WHERE email=%s AND password=%s"
    values = (email,password)

    cursor.execute(sql,values)
    user = cursor.fetchone()

    if user:
        return jsonify({
            "message":"Login successful"
        })

    return jsonify({
        "message":"Invalid email or password"
    })

@app.route("/post_request", methods=["POST"])
def post_request():

    data = request.json

    title = data["title"]
    description = data["description"]
    email = data["email"]

    sql = "INSERT INTO requests (title, description, user_email) VALUES (%s,%s,%s)"
    val = (title, description, email)

    cursor.execute(sql, val)
    db.commit()

    return jsonify({"message":"Request posted successfully"})

@app.route("/get_requests", methods=["GET"])
def get_requests():

    cursor.execute("SELECT * FROM requests ORDER BY created_at DESC")

    rows = cursor.fetchall()

    requests = []

    for r in rows:
        requests.append({
            "id": r[0],
            "title": r[1],
            "description": r[2],
            "email": r[3]
        })

    return jsonify(requests)

if __name__ == "__main__":
    app.run(debug=True)