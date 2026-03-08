from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

users = []

@app.route("/")
def home():
    return "Student Helper Backend Running"

@app.route("/register", methods=["POST"])
def register():

    data = request.json

    user = {
        "name": data["name"],
        "email": data["email"],
        "password": data["password"]
    }

    users.append(user)

    return jsonify({
        "message": "User registered successfully"
    })


@app.route("/login", methods=["POST"])
def login():

    data = request.json

    for user in users:
        if user["email"] == data["email"] and user["password"] == data["password"]:
            return jsonify({
                "message": "Login successful"
            })

    return jsonify({
        "message": "Invalid email or password"
    })


if __name__ == "__main__":
    app.run(debug=True)