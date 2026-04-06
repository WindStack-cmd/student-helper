from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, send
import mysql.connector
import os
import re
from datetime import datetime, timedelta
import bcrypt
import jwt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

# FEATURE #3: Rate Limiter initialization
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# FIX #1: CORS - Restrict to specific origins instead of wildcard
ALLOWED_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:8000,http://localhost:3000,http://127.0.0.1:5501"
).split(",")
CORS(app, resources={r"/*": {"origins": ALLOWED_ORIGINS}}, supports_credentials=True)

socketio = SocketIO(app, cors_allowed_origins=ALLOWED_ORIGINS)
app.config['CORS_HEADERS'] = 'Content-Type'

# FEATURE #2: JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24

# FIX #5: Add logging helper
def log_event(event_type, message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {event_type}: {message}")

# FEATURE #1: Password Hashing - bcrypt functions
def hash_password(password):
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password, hashed_password):
    """Verify password against bcrypt hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        log_event("AUTH", f"Password verification error: {str(e)}", "ERROR")
        return False

# FEATURE #2: JWT Authentication functions
def generate_jwt_token(email, user_id=None):
    """Generate JWT access token (expires in 24 hours)"""
    payload = {
        "email": email,
        "user_id": user_id,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

def verify_jwt_token(token):
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None  # Token expired
    except jwt.InvalidTokenError:
        return None  # Invalid token

def get_token_from_request():
    """Extract JWT token from Authorization header"""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]  # Remove "Bearer " prefix
    return None

def resolve_request_email():
    """Resolve user email from JWT token first, then fallback to query string."""
    token_email = ""
    token = get_token_from_request()
    if token:
        payload = verify_jwt_token(token)
        if payload:
            token_email = str(payload.get("email") or "").strip()

    query_email = str(request.args.get("email") or "").strip()
    return token_email or query_email

def require_auth(f):
    """Decorator to require JWT authentication"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_request()
        if not token:
            log_event("AUTH", "Missing authorization token", "WARNING")
            return jsonify({"message": "Missing authorization token", "error_code": "NO_TOKEN"}), 401

        payload = verify_jwt_token(token)
        if not payload:
            log_event("AUTH", "Invalid or expired token", "WARNING")
            return jsonify({"message": "Invalid or expired token", "error_code": "INVALID_TOKEN"}), 401

        # Add email to request context
        request.user_email = payload.get("email")
        return f(*args, **kwargs)
    return decorated_function

def parse_bool_env(name, default=False):
    value = os.getenv(name, str(default)).strip().lower()
    return value in ("1", "true", "yes", "on")

# FIX #2: Use environment variables properly (no hardcoded defaults for password)
DB_PASSWORD = os.getenv("DB_PASSWORD")
if DB_PASSWORD is None:
    raise RuntimeError(
        "DB_PASSWORD must be set in backend/.env. "
        "Do not rely on a hardcoded default password."
    )

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": DB_PASSWORD,
    "database": os.getenv("DB_NAME", "student_helper"),
    "ssl_disabled": parse_bool_env("DB_SSL_DISABLED", False),
}

if os.getenv("DB_AUTH_PLUGIN"):
    DB_CONFIG["auth_plugin"] = os.getenv("DB_AUTH_PLUGIN")

if os.getenv("DB_SSL_CA"):
    DB_CONFIG["ssl_ca"] = os.getenv("DB_SSL_CA")


def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# FIX #3: Input validation helpers
def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_password(password):
    """Validate password (min 6 chars)"""
    return len(password) >= 6

def validate_title(title):
    """Validate title (min 3, max 255 chars)"""
    return 3 <= len(title) <= 255

def validate_description(description):
    """Validate description (max 5000 chars)"""
    return len(description) <= 5000

def init_db():
    try:
        db_name = DB_CONFIG["database"]
        init_config = {
            "host": DB_CONFIG["host"],
            "user": DB_CONFIG["user"],
            "password": DB_CONFIG["password"],
            "ssl_disabled": DB_CONFIG["ssl_disabled"],
        }
        if DB_CONFIG.get("auth_plugin"):
            init_config["auth_plugin"] = DB_CONFIG["auth_plugin"]
        if DB_CONFIG.get("ssl_ca"):
            init_config["ssl_ca"] = DB_CONFIG["ssl_ca"]

        conn = mysql.connector.connect(**init_config)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
        cursor.execute(f"USE `{db_name}`")
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), email VARCHAR(255) UNIQUE, password VARCHAR(255), points INT DEFAULT 0, first_name VARCHAR(255), reputation INT DEFAULT 0, bounties_completed INT DEFAULT 0)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS requests (id INT AUTO_INCREMENT PRIMARY KEY, title VARCHAR(255), description TEXT, user_email VARCHAR(255), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, status VARCHAR(50), bounty INT DEFAULT 0, captured_by VARCHAR(255), solved BOOLEAN DEFAULT 0)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS answers (id INT AUTO_INCREMENT PRIMARY KEY, request_id INT, answer TEXT, email VARCHAR(255), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, accepted BOOLEAN DEFAULT 0)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS posts (id INT AUTO_INCREMENT PRIMARY KEY, first_name VARCHAR(255), title VARCHAR(255), content TEXT, user_email VARCHAR(255), bounty INT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS notifications (id INT AUTO_INCREMENT PRIMARY KEY, email VARCHAR(255), message TEXT, seen BOOLEAN DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        # Ensure solved and captured_by columns exist on already-created tables
        try:
            cursor.execute("ALTER TABLE requests ADD COLUMN solved BOOLEAN DEFAULT 0")
            conn.commit()
        except Exception:
            pass  # Column already exists
        try:
            cursor.execute("ALTER TABLE requests ADD COLUMN captured_by VARCHAR(255)")
            conn.commit()
        except Exception:
            pass  # Column already exists
        try:
            cursor.execute("ALTER TABLE requests MODIFY COLUMN bounty INT DEFAULT 0")
            conn.commit()
        except Exception:
            pass

        # FEATURE #4: Database Performance Optimization (Indexes)
        # 1. Index for status-based filtering and date-based sorting
        try:
            cursor.execute("CREATE INDEX idx_requests_status_created ON requests(status, created_at)")
            conn.commit()
        except Exception:
            pass # Index likely already exists

        # 2. Index for user-specific queries (get_my_requests)
        try:
            cursor.execute("CREATE INDEX idx_requests_user_email ON requests(user_email)")
            conn.commit()
        except Exception:
            pass

        # 3. FULLTEXT Index for high-performance keyword search (title + description)
        try:
            cursor.execute("CREATE FULLTEXT INDEX idx_requests_fulltext_search ON requests(title, description)")
            conn.commit()
        except Exception:
            pass

        conn.commit()
        cursor.close()
        conn.close()
        log_event("DB_INIT", f"Using MySQL at {DB_CONFIG['host']} with database '{DB_CONFIG['database']}'", "INFO")
        return
    except mysql.connector.Error as err:
        log_event("DB_INIT", f"MySQL connection failed: {err}", "ERROR")
        raise RuntimeError(
            f"MySQL connection failed: {err}. "
            "Start MySQL and verify DB_HOST/DB_USER/DB_PASSWORD/DB_NAME settings."
        ) from err

init_db()

@app.route("/")
def home():
    return "Student Helper Backend Running"

@app.route("/register", methods=["POST"])
@limiter.limit("5 per minute")  # FEATURE #3: Rate limiting
def register():
    data = request.json or {}
    first_name = str(data.get("first_name") or "").strip()
    email = str(data.get("email") or "").strip().lower()  # Lowercase for consistency
    password = str(data.get("password") or "").strip()

    # FIX #3: Input validation
    if not email or not validate_email(email):
        log_event("REGISTER", f"Invalid email format: {email}", "WARNING")
        return jsonify({"message": "Invalid email format", "error_code": "INVALID_EMAIL"}), 400

    if not password or not validate_password(password):
        log_event("REGISTER", f"Password too short for {email}", "WARNING")
        return jsonify({"message": "Password must be at least 6 characters", "error_code": "WEAK_PASSWORD"}), 400

    if not first_name or len(first_name) < 2:
        log_event("REGISTER", f"Invalid name for {email}", "WARNING")
        return jsonify({"message": "Name must be at least 2 characters", "error_code": "INVALID_NAME"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if user:
            log_event("REGISTER", f"User already exists: {email}", "WARNING")
            return jsonify({"message": "User already exists", "error_code": "USER_EXISTS"}), 400

        # FEATURE #1: Hash password before storing
        hashed_password = hash_password(password)

        cursor.execute(
            "INSERT INTO users (first_name, email, password, points) VALUES (%s,%s,%s,%s)",
            (first_name, email, hashed_password, 0)
        )
        conn.commit()
        log_event("REGISTER", f"User registered successfully: {email}", "INFO")
        return jsonify({"message": "User registered successfully"}), 201
    except mysql.connector.IntegrityError as e:
        log_event("REGISTER", f"Database integrity error: {str(e)}", "ERROR")
        return jsonify({"message": "Email already registered", "error_code": "DB_INTEGRITY_ERROR"}), 400
    except Exception as e:
        log_event("REGISTER", f"Unexpected error for {email}: {str(e)}", "ERROR")
        return jsonify({"message": "Registration failed", "error_code": "INTERNAL_ERROR", "details": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/login", methods=["POST"])
@limiter.limit("5 per minute")  # FEATURE #3: Rate limiting (5 login attempts per minute)
def login():
    data = request.json or {}
    email = str(data.get("email") or "").strip().lower()  # Lowercase for consistency
    password = str(data.get("password") or "").strip()

    # FIX #3: Input validation
    if not email or not validate_email(email):
        log_event("LOGIN", f"Invalid email format attempt: {email}", "WARNING")
        return jsonify({"message": "Invalid email format", "error_code": "INVALID_EMAIL"}), 400

    if not password:
        log_event("LOGIN", f"Missing password for: {email}", "WARNING")
        return jsonify({"message": "Password is required", "error_code": "MISSING_PASSWORD"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, email, first_name, name, password FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if user and verify_password(password, user["password"]):
            # FEATURE #1: Password verified with bcrypt
            display_name = user.get("first_name")
            if not display_name:
                name_val = user.get("name") or ""
                if name_val.strip():
                    display_name = name_val.split()[0]
                else:
                    display_name = user["email"].split("@")[0]

            # FEATURE #2: Generate JWT token
            access_token = generate_jwt_token(email, user["id"])

            log_event("LOGIN", f"Login successful: {email}", "INFO")
            return jsonify({
                "message": "Login successful",
                "email": user["email"],
                "first_name": display_name,
                "access_token": access_token,
                "token_type": "Bearer",
                "expires_in": JWT_EXPIRY_HOURS * 3600
            }), 200

        log_event("LOGIN", f"Login failed (invalid credentials): {email}", "WARNING")
        return jsonify({"message": "Invalid email or password", "error_code": "INVALID_CREDENTIALS"}), 401
    except Exception as e:
        log_event("LOGIN", f"Unexpected error for {email}: {str(e)}", "ERROR")
        return jsonify({"message": "Login failed", "error_code": "INTERNAL_ERROR"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/dashboard_metrics")
def dashboard_metrics():
    try:
        email = resolve_request_email()
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

            cursor.execute("SELECT COUNT(*) FROM requests WHERE status = 'open' AND (solved = 0 OR solved IS NULL)")
            r3 = cursor.fetchone()
            if r3 and r3[0] is not None:
                pending = int(r3[0])

            log_event("DASHBOARD_METRICS", f"Metrics retrieved for {email or 'anonymous'}", "INFO")
            return jsonify({
                "bounties_cleared": bounties_cleared,
                "ledger_stake": ledger_stake,
                "pending_jobs": pending
            })
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        log_event("DASHBOARD_METRICS", f"Error retrieving metrics: {str(e)}", "ERROR")
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
            log_event("LEADERBOARD", f"Retrieved leaderboard with {len(users)} users", "INFO")
            return jsonify(users)
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        log_event("LEADERBOARD", f"Error retrieving leaderboard: {str(e)}", "ERROR")
        return jsonify([]), 500

@app.route("/post_request", methods=["POST"])
@limiter.limit("20 per minute")  # FEATURE #3: Rate limiting (20 requests per minute)
def post_request():
    try:
        data = request.json or {}
        title = str(data.get("title") or "").strip()
        description = str(data.get("description") or "").strip()
        email = str(data.get("email") or "").strip()
        try:
            bounty = int(data.get("bounty") or 0)
        except (ValueError, TypeError):
            bounty = 0

        # FIX #3: Input validation for request
        if not email or not validate_email(email):
            log_event("POST_REQUEST", f"Invalid email: {email}", "WARNING")
            return jsonify({"message": "Invalid email", "error_code": "INVALID_EMAIL"}), 400

        if not validate_title(title):
            log_event("POST_REQUEST", f"Invalid title length: {len(title)}", "WARNING")
            return jsonify({"message": "Title must be 3-255 characters", "error_code": "INVALID_TITLE"}), 400

        if not validate_description(description):
            log_event("POST_REQUEST", f"Description too long for {email}", "WARNING")
            return jsonify({"message": "Description must be 5000 characters or less", "error_code": "INVALID_DESCRIPTION"}), 400

        if bounty < 0:
            bounty = 0

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO requests (title, description, user_email, bounty, status, solved) VALUES (%s, %s, %s, %s, 'open', 0)",
                (title, description, email, bounty)
            )
            conn.commit()
            request_id = cursor.lastrowid
            log_event("POST_REQUEST", f"Request posted successfully (ID: {request_id}) by {email} with bounty {bounty}", "INFO")
            return jsonify({"message": "Request posted successfully", "request_id": request_id}), 201
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        log_event("POST_REQUEST", f"Unexpected error: {str(e)}", "ERROR")
        return jsonify({"message": "Failed to post request", "error_code": "INTERNAL_ERROR", "details": str(e)}), 500

@app.route("/get_requests", methods=["GET"])
def get_requests():
    try:
        # Get pagination and search parameters from query string
        limit = request.args.get('limit', default=20, type=int)
        offset = request.args.get('offset', default=0, type=int)
        search = request.args.get('search', default="", type=str).strip()

        # Validation
        if limit > 100:
            limit = 100
        if limit < 1:
            limit = 20
        if offset < 0:
            offset = 0

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Base conditions
            conditions = "WHERE status = 'open' AND (solved = 0 OR solved IS NULL) AND user_email IS NOT NULL AND user_email != ''"
            params = []
            
            # Add search filter if provided
            if search:
                conditions += " AND (title LIKE %s OR description LIKE %s OR user_email LIKE %s)"
                search_param = f"%{search}%"
                params.extend([search_param, search_param, search_param])

            # First, fetch total count of eligible records with search filter
            count_query = f"SELECT COUNT(*) FROM requests {conditions}"
            cursor.execute(count_query, tuple(params))
            total_count = cursor.fetchone()[0]

            # Then, fetch paginated data using parameterized query
            # Adding limit and offset to params
            data_query = f"""
                SELECT * FROM requests 
                {conditions}
                ORDER BY created_at DESC 
                LIMIT %s OFFSET %s
            """
            cursor.execute(data_query, tuple(params + [limit, offset]))
            rows = cursor.fetchall()
            
            requests_list = []
            for r in rows:
                requests_list.append({
                    "id": r[0],
                    "title": r[1],
                    "description": r[2],
                    "email": r[3],
                    "created_at": str(r[4]) if r[4] else None,
                    "status": r[5],
                    "bounty": r[6],
                    "captured_by": r[7] if len(r) > 7 else None,
                    "solved": bool(r[8]) if len(r) > 8 else False
                })
            
            log_event("GET_REQUESTS", f"Retrieved {len(requests_list)} open requests (Total: {total_count}, Limit: {limit}, Offset: {offset}, Search: '{search}')", "INFO")
            
            return jsonify({
                "data": requests_list,
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "search": search
            })
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        log_event("GET_REQUESTS", f"Error retrieving requests: {str(e)}", "ERROR")
        return jsonify({
            "data": [],
            "total": 0,
            "limit": limit if 'limit' in locals() else 20,
            "offset": offset if 'offset' in locals() else 0,
            "error": str(e)
        }), 500

@app.route("/get_request_details/<int:request_id>", methods=["GET"])
def get_request_details(request_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True) # Use dictionary for easier mapping
        try:
            # 1. Fetch Request Data
            cursor.execute("SELECT * FROM requests WHERE id = %s", (request_id,))
            request_data = cursor.fetchone()
            
            if not request_data:
                log_event("GET_DETAILS", f"Request ID {request_id} not found", "WARNING")
                return jsonify({"message": "Request not found", "error_code": "NOT_FOUND"}), 404
            
            # 2. Fetch Related Answers
            cursor.execute("SELECT * FROM answers WHERE request_id = %s ORDER BY created_at ASC", (request_id,))
            answers_list = cursor.fetchall()
            
            # Formatting for JSON
            if request_data:
                request_data['created_at'] = str(request_data['created_at']) if request_data['created_at'] else None
            
            for ans in answers_list:
                ans['created_at'] = str(ans['created_at']) if ans['created_at'] else None
            
            log_event("GET_DETAILS", f"Retrieved details for request ID {request_id} with {len(answers_list)} answers", "INFO")
            
            return jsonify({
                "request": request_data,
                "answers": answers_list
            })
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        log_event("GET_DETAILS", f"Unexpected error: {str(e)}", "ERROR")
        return jsonify({"message": "Failed to load request details", "error_code": "INTERNAL_ERROR", "details": str(e)}), 500
        
@app.route("/get_answers/<int:request_id>", methods=["GET"])
def get_answers(request_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM answers WHERE request_id = %s ORDER BY created_at ASC", (request_id,))
            answers = cursor.fetchall()
            for ans in answers:
                ans['created_at'] = str(ans['created_at']) if ans['created_at'] else None
            return jsonify(answers)
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        return jsonify([]), 500

@app.route("/accept_answer", methods=["POST"])
def accept_answer():
    try:
        data = request.json or {}
        answer_id = data.get("answer_id")
        request_id = data.get("request_id")
        email = data.get("email") # Email of the answer poster

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # 1. Update answer status
            cursor.execute("UPDATE answers SET accepted = 1 WHERE id = %s", (answer_id,))
            
            # 2. Update request status
            cursor.execute("UPDATE requests SET status = 'closed', solved = 1 WHERE id = %s", (request_id,))
            
            # 3. Reward points to the helper
            cursor.execute("UPDATE users SET points = points + 50, bounties_completed = bounties_completed + 1 WHERE email = %s", (email,))
            
            conn.commit()
            log_event("ACCEPT_ANSWER", f"Answer {answer_id} accepted for request {request_id}. Reward given to {email}", "INFO")
            return jsonify({"message": "Answer accepted and reward successfully processed!"})
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        log_event("ACCEPT_ANSWER", f"Error: {str(e)}", "ERROR")
        return jsonify({"message": "Failed to accept answer"}), 500

@app.route("/get_active_bounties", methods=["GET"])
def get_active_bounties():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM requests WHERE status = 'open' AND (solved = 0 OR solved IS NULL) AND bounty > 0 ORDER BY bounty DESC")
            rows = cursor.fetchall()
            bounties_list = []
            for r in rows:
                bounties_list.append({
                    "id": r[0],
                    "title": r[1],
                    "description": r[2],
                    "email": r[3],
                    "created_at": str(r[4]) if r[4] else None,
                    "status": r[5],
                    "bounty": r[6],
                    "captured_by": r[7] if len(r) > 7 else None,
                    "solved": bool(r[8]) if len(r) > 8 else False
                })
            log_event("GET_ACTIVE_BOUNTIES", f"Retrieved {len(bounties_list)} active bounties", "INFO")
            return jsonify(bounties_list)
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        log_event("GET_ACTIVE_BOUNTIES", f"Error: {str(e)}", "ERROR")
        return jsonify([])

@app.route("/get_my_requests", methods=["GET"])
def get_my_requests():
    try:
        email = resolve_request_email()
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
            log_event("GET_MY_REQUESTS", f"Retrieved {len(requests_list)} requests for {email}", "INFO")
            return jsonify(requests_list)
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        log_event("GET_MY_REQUESTS", f"Error: {str(e)}", "ERROR")
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
            log_event("GET_ARCHIVED_REQUESTS", f"Retrieved {len(requests_list)} archived requests", "INFO")
            return jsonify(requests_list)
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        log_event("GET_ARCHIVED_REQUESTS", f"Error: {str(e)}", "ERROR")
        return jsonify([])

@app.route("/post_answer", methods=["POST"])
@limiter.limit("30 per minute")  # FEATURE #3: Rate limiting
def post_answer():
    try:
        data = request.json or {}
        request_id = data.get("request_id")
        answer = str(data.get("answer") or "").strip()
        email = str(data.get("email") or "").strip()

        # FIX #3: Input validation
        if not request_id or not isinstance(request_id, int):
            log_event("POST_ANSWER", f"Invalid request_id: {request_id}", "WARNING")
            return jsonify({"message": "Invalid request ID", "error_code": "INVALID_REQUEST_ID"}), 400

        if not email or not validate_email(email):
            log_event("POST_ANSWER", f"Invalid email: {email}", "WARNING")
            return jsonify({"message": "Invalid email", "error_code": "INVALID_EMAIL"}), 400

        if not answer or len(answer) < 5:
            log_event("POST_ANSWER", f"Answer too short from {email}", "WARNING")
            return jsonify({"message": "Answer must be at least 5 characters", "error_code": "ANSWER_TOO_SHORT"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("INSERT INTO answers (request_id, answer, email) VALUES (%s,%s,%s)", (request_id, answer, email))
            conn.commit()
            log_event("POST_ANSWER", f"Answer posted for request {request_id} by {email}", "INFO")

            cursor.execute("SELECT user_email FROM requests WHERE id=%s", (request_id,))
            row = cursor.fetchone()
            if row:
                owner = row["user_email"]
                cursor.execute("INSERT INTO notifications (email,message) VALUES (%s,%s)", (owner,"Someone answered your request"))
                conn.commit()
                log_event("POST_ANSWER", f"Notification sent to {owner}", "INFO")

            return jsonify({"message":"Answer posted successfully"}), 201
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        log_event("POST_ANSWER", f"Unexpected error: {str(e)}", "ERROR")
        return jsonify({"message": "Failed to post answer", "error_code": "INTERNAL_ERROR"}), 500

@app.route("/get_answers/<int:request_id>", methods=["GET"])
def get_answers(request_id):
    try:
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
            log_event("GET_ANSWERS", f"Retrieved {len(answers)} answers for request {request_id}", "INFO")
            return jsonify(answers)
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        log_event("GET_ANSWERS", f"Error: {str(e)}", "ERROR")
        return jsonify([])

@app.route("/accept_answer", methods=["POST"])
@limiter.limit("30 per minute")  # FEATURE #3: Rate limiting
def accept_answer():
    try:
        data = request.json or {}
        answer_id = data.get("answer_id")
        request_id = data.get("request_id")
        helper_email = str(data.get("email") or "").strip()

        # FIX #3: Input validation
        if not answer_id or not request_id:
            log_event("ACCEPT_ANSWER", f"Missing answer_id or request_id", "WARNING")
            return jsonify({"message": "Missing answer_id or request_id", "error_code": "MISSING_PARAMS"}), 400

        if helper_email and not validate_email(helper_email):
            log_event("ACCEPT_ANSWER", f"Invalid helper email: {helper_email}", "WARNING")
            return jsonify({"message": "Invalid helper email", "error_code": "INVALID_EMAIL"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE answers SET accepted = 1 WHERE id = %s", (answer_id,))
            cursor.execute("UPDATE requests SET solved = 1, status = 'closed' WHERE id = %s", (request_id,))
            if helper_email:
                cursor.execute(
                    "UPDATE users SET points = points + 20, bounties_completed = bounties_completed + 1 WHERE email = %s",
                    (helper_email,)
                )
            conn.commit()
            log_event("ACCEPT_ANSWER", f"Answer {answer_id} accepted for request {request_id}, points awarded to {helper_email}", "INFO")
            return jsonify({"message": "Answer accepted"}), 200
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        log_event("ACCEPT_ANSWER", f"Error accepting answer: {str(e)}", "ERROR")
        return jsonify({"message": "Failed to accept answer", "error_code": "INTERNAL_ERROR"}), 500

@app.route("/purge_user", methods=["POST"])
@limiter.limit("2 per minute")  # FEATURE #3: Rate limiting (very restrictive for destructive operation)
def purge_user():
    try:
        data = request.json or {}
        email = str(data.get("email") or "").strip()

        # FIX #3: Input validation
        if not email or not validate_email(email):
            log_event("PURGE_USER", f"Invalid email format: {email}", "WARNING")
            return jsonify({"message": "Invalid email", "error_code": "INVALID_EMAIL"}), 400

        log_event("PURGE_USER", f"Starting purge for: {email}", "WARNING")

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM notifications WHERE email = %s", (email,))
            cursor.execute("DELETE FROM answers WHERE email = %s", (email,))
            cursor.execute("DELETE FROM posts WHERE user_email = %s", (email,))
            cursor.execute("DELETE FROM requests WHERE user_email = %s", (email,))
            cursor.execute("DELETE FROM users WHERE email = %s", (email,))

            conn.commit()
            log_event("PURGE_USER", f"User data purged successfully for: {email}", "WARNING")
            return jsonify({"message": "User data purged successfully"}), 200
        except Exception as e:
            conn.rollback()
            log_event("PURGE_USER", f"Error purging user {email}: {str(e)}", "ERROR")
            return jsonify({"message": "Failed to purge user data", "error_code": "DB_ERROR"}), 500
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        log_event("PURGE_USER", f"Critical error: {str(e)}", "ERROR")
        return jsonify({"message": "Server error", "error_code": "INTERNAL_ERROR"}), 500

@socketio.on("message")
def handle_message(msg):
    log_event("WEBSOCKET_MESSAGE", f"Received message: {msg[:50]}...", "INFO")
    send(msg, broadcast=True)

@app.route("/update_reputation", methods=["POST"])
def update_reputation():
    try:
        data = request.json or {}
        email = str(data.get("email") or "").strip()

        if not email or not validate_email(email):
            log_event("UPDATE_REPUTATION", f"Invalid email: {email}", "WARNING")
            return jsonify({"message": "Invalid email", "error_code": "INVALID_EMAIL"}), 400

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
            log_event("UPDATE_REPUTATION", f"Reputation updated for {email}", "INFO")
            return jsonify({"message": "Updated"})
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        log_event("UPDATE_REPUTATION", f"Error: {str(e)}", "ERROR")
        return jsonify({"message": "Failed to update reputation"}), 500

@app.route("/get_posts", methods=["GET"])
def get_posts():
    try:
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
            log_event("GET_POSTS", f"Retrieved {len(posts)} posts", "INFO")
            return jsonify(posts)
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        log_event("GET_POSTS", f"Error: {str(e)}", "ERROR")
        return jsonify([])

@app.route("/create_post", methods=["POST"])
@limiter.limit("20 per minute")  # FEATURE #3: Rate limiting
def create_post():
    try:
        data = request.json or {}
        email = str(data.get("email") or "").strip()
        content = str(data.get("content") or "").strip()
        try:
            bounty = int(data.get("bounty") or 0)
        except (ValueError, TypeError):
            bounty = 0

        if not email or not validate_email(email):
            log_event("CREATE_POST", f"Invalid email: {email}", "WARNING")
            return jsonify({"message": "Invalid email", "error_code": "INVALID_EMAIL"}), 400

        if not content or len(content) < 5:
            log_event("CREATE_POST", f"Content too short from {email}", "WARNING")
            return jsonify({"message": "Content must be at least 5 characters", "error_code": "CONTENT_TOO_SHORT"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO posts (user_email, content, bounty) VALUES (%s, %s, %s)", (email, content, bounty))
            conn.commit()
            log_event("CREATE_POST", f"Post created by {email}", "INFO")
            return jsonify({"message": "Post created"}), 201
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        log_event("CREATE_POST", f"Error: {str(e)}", "ERROR")
        return jsonify({"message": "Failed to create post", "error_code": "INTERNAL_ERROR"}), 500

@app.route("/accept_post", methods=["POST"])
@limiter.limit("30 per minute")  # FEATURE #3: Rate limiting
def accept_post():
    try:
        data = request.json or {}
        helper_email = str(data.get("email") or "").strip()
        request_id = data.get("post_id")

        if not helper_email or not validate_email(helper_email):
            log_event("ACCEPT_POST", f"Invalid email: {helper_email}", "WARNING")
            return jsonify({"message": "Invalid email", "error_code": "INVALID_EMAIL"}), 400

        if not request_id:
            log_event("ACCEPT_POST", f"Invalid request_id", "WARNING")
            return jsonify({"message": "Invalid post_id", "error_code": "INVALID_REQUEST_ID"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE requests SET status = 'captured', captured_by = %s WHERE id = %s",
                (helper_email, request_id)
            )
            conn.commit()
            log_event("ACCEPT_POST", f"Post accepted for request {request_id} by {helper_email}", "INFO")
            return jsonify({"message": "accepted"}), 200
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        log_event("ACCEPT_POST", f"Error: {str(e)}", "ERROR")
        return jsonify({"message": "Failed to capture request", "error_code": "INTERNAL_ERROR"}), 500

@app.route("/user_stats", methods=["GET"])
def user_stats():
    try:
        email = resolve_request_email()
        if not email:
            log_event("USER_STATS", "No email provided", "WARNING")
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
                log_event("USER_STATS", f"Retrieved stats for {email}", "INFO")
                return jsonify(user)
            else:
                log_event("USER_STATS", f"User not found: {email}", "WARNING")
                return jsonify({"first_name": "", "email": email, "reputation": 0, "bounties_completed": 0}), 200
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        log_event("USER_STATS", f"Error: {str(e)}", "ERROR")
        return jsonify({"first_name": "", "email": resolve_request_email(), "reputation": 0, "bounties_completed": 0}), 200

if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "0") == "1"
    socketio.run(app, debug=debug_mode, use_reloader=debug_mode)
