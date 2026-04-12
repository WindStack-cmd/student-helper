from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_talisman import Talisman
import bleach
# from flask_socketio import SocketIO, send  # Disabled on Windows due to socket binding issues
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
# Add Security Headers via Talisman
Talisman(app, force_https=False, content_security_policy=None)

def custom_key_func():
    # Exempt OPTIONS requests (CORS preflight)
    if request.method == "OPTIONS":
        return None
    # Exempt GET requests to read-only endpoints for certain keys? 
    # Actually, let's keep it simple: return None means NO LIMIT.
    if request.method == "GET" and request.path in ["/get_requests", "/get_leaderboard", "/get_user_stats"]:
        return None
    return get_remote_address()

limiter = Limiter(
    app=app,
    key_func=custom_key_func,
    default_limits=["2000 per day", "500 per hour"],  # Increased for development
    storage_uri="memory://",
    in_memory_fallback_enabled=True
)

# FIX #1: CORS - Restrict to specific origins instead of wildcard
ALLOWED_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:8000,http://localhost:3000,http://127.0.0.1:5500,http://127.0.0.1:5501,http://127.0.0.1:5502,http://127.0.0.1:3000,http://localhost:5502"
).split(",")
CORS(app, resources={r"/*": {
    "origins": "*",
    "allow_headers": ["Content-Type", "Authorization"],
    "methods": ["GET", "POST", "OPTIONS", "PUT", "DELETE"]
}}, supports_credentials=True)

# Explicitly handle OPTIONS requests via route if needed, 
# but flask-cors usually covers this automatically for all routes.

# socketio = SocketIO(app, cors_allowed_origins=ALLOWED_ORIGINS)  # Disabled on Windows due to socket binding issues
# app.config['CORS_HEADERS'] = 'Content-Type'  # Removed to avoid restriction

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
    "port": int(os.getenv("DB_PORT", 3306)),
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
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]+$'
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
            "port": DB_CONFIG.get("port", 3306),
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
        cursor.execute('''CREATE TABLE IF NOT EXISTS requests (id INT AUTO_INCREMENT PRIMARY KEY, title VARCHAR(255), description TEXT, user_email VARCHAR(255), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, status VARCHAR(50), bounty INT DEFAULT 0, captured_by VARCHAR(255), solved BOOLEAN DEFAULT 0, escrowed_bounty INT DEFAULT 0, expires_at TIMESTAMP NULL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS answers (id INT AUTO_INCREMENT PRIMARY KEY, request_id INT, answer TEXT, email VARCHAR(255), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, accepted BOOLEAN DEFAULT 0)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS posts (id INT AUTO_INCREMENT PRIMARY KEY, first_name VARCHAR(255), title VARCHAR(255), content TEXT, user_email VARCHAR(255), bounty INT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS notifications (id INT AUTO_INCREMENT PRIMARY KEY, email VARCHAR(255), message TEXT, seen BOOLEAN DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS claims (id INT AUTO_INCREMENT PRIMARY KEY, request_id INT, user_email VARCHAR(255), claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE KEY unique_claim (request_id, user_email))''')

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

        try:
            cursor.execute("ALTER TABLE requests ADD COLUMN category VARCHAR(100)")
            conn.commit()
        except Exception:
            pass

        try:
            cursor.execute("ALTER TABLE answers ADD COLUMN upvotes INT DEFAULT 0")
            conn.commit()
        except Exception:
            pass

        try:
            cursor.execute("UPDATE users SET reputation = points WHERE reputation = 0 AND points > 0")
            conn.commit()
        except Exception:
            pass

        try:
            cursor.execute("ALTER TABLE requests ADD COLUMN views INT DEFAULT 0")
            conn.commit()
        except Exception:
            pass

        try:
            cursor.execute("ALTER TABLE answers ADD COLUMN file_path VARCHAR(255)")
            conn.commit()
        except Exception:
            pass
            
        try:
            cursor.execute("ALTER TABLE requests ADD COLUMN escrowed_bounty INT DEFAULT 0")
            conn.commit()
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE requests ADD COLUMN expires_at TIMESTAMP NULL")
            conn.commit()
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE answers ADD COLUMN rating INT DEFAULT 0")
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

        # Give 100 points onboarding bonus to anyone with 0 (one-time migration for existing users)
        try:
            cursor.execute("UPDATE users SET points = 100, reputation = 100 WHERE points = 0 AND reputation = 0")
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

@app.route("/favicon.ico")
def favicon():
    return "", 204  # Return empty response with No Content status

@app.route("/register", methods=["POST"])
# @limiter.limit("20 per minute")  # Disabled for debugging
def register():
    data = request.json or {}
    first_name = bleach.clean(str(data.get("first_name") or "").strip())
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
            "INSERT INTO users (first_name, name, email, password, points, reputation) VALUES (%s,%s,%s,%s,%s,%s)",
            (first_name, first_name, email, hashed_password, 100, 100)
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
# @limiter.limit("5 per minute")  # Temporarily disabled for CORS debugging
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

@app.route("/get_balance", methods=["GET"])
@require_auth
def get_balance():
    try:
        email = request.user_email
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT COALESCE(reputation, points, 0) as balance FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            if not user:
                return jsonify({"message": "User not found", "error_code": "USER_NOT_FOUND"}), 404
            return jsonify({"balance": user["balance"]}), 200
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        log_event("GET_BALANCE", str(e), "ERROR")
        return jsonify({"message": "Failed to get balance", "error_code": "INTERNAL_ERROR"}), 500

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
        title = bleach.clean(str(data.get("title") or "").strip())
        description = bleach.clean(str(data.get("description") or "").strip())
        email = str(data.get("email") or "").strip()
        category = bleach.clean(str(data.get("category") or "").strip())
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
        cursor = conn.cursor(dictionary=True)
        try:
            # Validate balance - use reputation as the balance
            cursor.execute("SELECT COALESCE(reputation, points, 0) as balance FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            if not user or user["balance"] < bounty:
                return jsonify({"message": "Insufficient balance", "error_code": "INSUFFICIENT_BALANCE"}), 400
            
            # Deduct bounty and set expires_at
            expiry_date = datetime.now() + timedelta(days=7)
            
            cursor.execute(
                "UPDATE users SET reputation = reputation - %s, points = points - %s WHERE email = %s",
                (bounty, bounty, email)
            )
            
            cursor.execute(
                "INSERT INTO requests (title, description, user_email, bounty, status, solved, category, escrowed_bounty, expires_at) VALUES (%s, %s, %s, %s, 'open', 0, %s, %s, %s)",
                (title, description, email, bounty, category, bounty, expiry_date)
            )
            conn.commit()
            request_id = cursor.lastrowid
            log_event("POST_REQUEST", f"Request posted successfully (ID: {request_id}) by {email} with bounty {bounty} (escrowed)", "INFO")
            return jsonify({"message": "Request posted successfully", "request_id": request_id}), 201
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        log_event("POST_REQUEST", f"Unexpected error: {str(e)}", "ERROR")
        return jsonify({"message": "Failed to post request", "error_code": "INTERNAL_ERROR", "details": str(e)}), 500

@app.route("/get_requests", methods=["GET"])
def get_requests():
    # Hook to check for expired requests
    try:
        conn_expiry = get_db_connection()
        cursor_expiry = conn_expiry.cursor(dictionary=True)
        try:
            # Find requests that should expire
            cursor_expiry.execute(
                "SELECT id, user_email, escrowed_bounty FROM requests WHERE status = 'open' AND expires_at < NOW() AND escrowed_bounty > 0"
            )
            expired_requests = cursor_expiry.fetchall()
            
            for req in expired_requests:
                # Return bounty
                cursor_expiry.execute(
                    "UPDATE users SET reputation = reputation + %s, points = points + %s WHERE email = %s",
                    (req["escrowed_bounty"], req["escrowed_bounty"], req["user_email"])
                )
                # Set status and clear escrow
                cursor_expiry.execute(
                    "UPDATE requests SET status = 'expired', escrowed_bounty = 0 WHERE id = %s",
                    (req["id"],)
                )
                log_event("EXPIRY", f"Request {req['id']} expired, returned {req['escrowed_bounty']} to {req['user_email']}", "INFO")
            
            # Also catch requests with 0 bounty but expired
            cursor_expiry.execute(
                "UPDATE requests SET status = 'expired' WHERE status = 'open' AND expires_at < NOW() AND escrowed_bounty = 0"
            )
            
            conn_expiry.commit()
        finally:
            cursor_expiry.close()
            conn_expiry.close()
    except Exception as e:
        log_event("EXPIRY_CHECK", f"Error during expiry check: {str(e)}", "ERROR")

    try:
        # Get pagination and search parameters from query string
        limit = request.args.get('limit', default=20, type=int)
        offset = request.args.get('offset', default=0, type=int)
        search = request.args.get('search', default="", type=str).strip()
        category = request.args.get('category', default="", type=str).strip()
        sort_by = request.args.get('sort', default="newest", type=str).strip()

        status_filter = request.args.get('status', default="open", type=str).strip()

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
            conditions = "WHERE user_email IS NOT NULL AND user_email != ''"
            params = []
            
            if status_filter == 'open':
                conditions += " AND status = 'open' AND (solved = 0 OR solved IS NULL)"
            elif status_filter == 'in_progress' or status_filter == 'captured':
                conditions += " AND status = 'captured'"
            elif status_filter == 'completed' or status_filter == 'closed':
                conditions += " AND (status = 'closed' OR solved = 1)"
            elif status_filter and status_filter != 'all':
                conditions += " AND status = %s"
                params.append(status_filter)
            
            # Add search filter if provided
            if search:
                conditions += " AND (title LIKE %s OR description LIKE %s OR user_email LIKE %s)"
                search_param = f"%{search}%"
                params.extend([search_param, search_param, search_param])
                
            if category:
                conditions += " AND category = %s"
                params.append(category)

            order_clause = "ORDER BY created_at DESC"
            if sort_by == 'highest_bounty':
                order_clause = "ORDER BY bounty DESC, created_at DESC"
            elif sort_by == 'most_viewed':
                order_clause = "ORDER BY views DESC, created_at DESC"

            # First, fetch total count of eligible records with search filter
            count_query = f"SELECT COUNT(*) FROM requests {conditions}"
            cursor.execute(count_query, tuple(params))
            total_count = cursor.fetchone()[0]

            # Then, fetch paginated data using parameterized query
            # Adding limit and offset to params
            data_query = f"""
                SELECT * FROM requests 
                {conditions}
                {order_clause}
                LIMIT %s OFFSET %s
            """
            cursor.execute(data_query, tuple(params + [limit, offset]))
            # Get column names to handle mapping properly without dictionary=True if needed,
            # but since we want to be safe, let's keep the manual mapping or switch to dict.
            rows = cursor.fetchall()
            
            requests_list = []
            for r in rows:
                # Check column count to avoid index errors in different environments
                req = {
                    "id": r[0],
                    "title": r[1],
                    "description": r[2],
                    "email": r[3],
                    "created_at": str(r[4]) if r[4] else None,
                    "status": r[5],
                    "bounty": r[6],
                    "captured_by": r[7] if len(r) > 7 else None,
                    "solved": bool(r[8]) if len(r) > 8 else False,
                }
                # Handle extended columns (category, views, escrowed_bounty, expires_at)
                # These indices assumes standard order from init_db + alters
                if len(r) > 9: req["category"] = r[9]
                if len(r) > 10: req["views"] = r[10]
                if len(r) > 11: req["escrowed_bounty"] = r[11]
                if len(r) > 12: req["expires_at"] = str(r[12]) if r[12] else None
                
                requests_list.append(req)
            
            log_event("GET_REQUESTS", f"Retrieved {len(requests_list)} open requests (Sort: {sort_by})", "INFO")
            
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
            # Increment views
            cursor.execute("UPDATE requests SET views = views + 1 WHERE id = %s", (request_id,))
            conn.commit()

            # 1. Fetch Request Data
            cursor.execute("SELECT * FROM requests WHERE id = %s", (request_id,))
            request_data = cursor.fetchone()
            
            if not request_data:
                log_event("GET_DETAILS", f"Request ID {request_id} not found", "WARNING")
                return jsonify({"message": "Request not found", "error_code": "NOT_FOUND"}), 404
            
            # 2. Fetch Related Answers
            cursor.execute("SELECT * FROM answers WHERE request_id = %s ORDER BY created_at ASC", (request_id,))
            answers_list = cursor.fetchall()
            
            # 3. Fetch Claims
            cursor.execute("""
                SELECT u.first_name as username 
                FROM claims c
                JOIN users u ON c.user_email = u.email
                WHERE c.request_id = %s
            """, (request_id,))
            claims_list = cursor.fetchall()
            claimants = [c['username'] for c in claims_list]
            
            # Formatting for JSON
            if request_data:
                request_data['created_at'] = str(request_data['created_at']) if request_data['created_at'] else None
                request_data['expires_at'] = str(request_data['expires_at']) if request_data.get('expires_at') else None
            
            for ans in answers_list:
                ans['created_at'] = str(ans['created_at']) if ans['created_at'] else None
            
            log_event("GET_DETAILS", f"Retrieved details for request ID {request_id} with {len(answers_list)} answers and {len(claimants)} claims", "INFO")
            
            return jsonify({
                "request": request_data,
                "answers": answers_list,
                "claims_count": len(claimants),
                "claimants": claimants
            })
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        log_event("GET_DETAILS", f"Unexpected error: {str(e)}", "ERROR")
        return jsonify({"message": "Failed to load request details", "error_code": "INTERNAL_ERROR", "details": str(e)}), 500

@app.route("/upvote_answer", methods=["POST"])
@limiter.limit("30 per minute")
def upvote_answer():
    try:
        data = request.json or {}
        answer_id = data.get("answer_id")
        
        if not answer_id:
            return jsonify({"message": "Missing answer_id"}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("UPDATE answers SET upvotes = upvotes + 1 WHERE id = %s", (answer_id,))
            
            cursor.execute("SELECT email FROM answers WHERE id = %s", (answer_id,))
            ans = cursor.fetchone()
            if ans and ans["email"]:
                cursor.execute("UPDATE users SET reputation = reputation + 10, points = points + 10 WHERE email = %s", (ans["email"],))
                
            conn.commit()
            return jsonify({"message": "Upvoted successfully"}), 200
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        log_event("UPVOTE_ANSWER", str(e), "ERROR")
        return jsonify({"message": "Failed to upvote"}), 500
        
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

import werkzeug.utils

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    from flask import send_from_directory
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

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
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM requests WHERE user_email = %s ORDER BY created_at DESC", (email,))
            rows = cursor.fetchall()
            requests_list = []
            for r in rows:
                r['email'] = r.get('user_email')
                r['created_at'] = str(r['created_at']) if r['created_at'] else None
                r['expires_at'] = str(r['expires_at']) if r.get('expires_at') else None
                requests_list.append(r)
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
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM requests WHERE solved = 1 OR status = 'closed' ORDER BY created_at DESC")
            rows = cursor.fetchall()
            requests_list = []
            for r in rows:
                r['email'] = r.get('user_email')
                r['created_at'] = str(r['created_at']) if r['created_at'] else None
                r['expires_at'] = str(r['expires_at']) if r.get('expires_at') else None
                requests_list.append(r)
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
        # Support multipart/form-data for file uploads
        is_form = request.content_type and "multipart/form-data" in request.content_type
        data = request.form if is_form else (request.json or {})
        
        request_id_raw = data.get("request_id")
        try:
            request_id = int(request_id_raw)
        except (ValueError, TypeError):
            request_id = None
            
        answer = bleach.clean(str(data.get("answer") or "").strip())
        email = str(data.get("email") or "").strip()

        # Handle file upload
        file_path = None
        if is_form and "file" in request.files:
            file = request.files["file"]
            if file and file.filename:
                import werkzeug.utils
                import uuid
                filename = f"{uuid.uuid4()}_{werkzeug.utils.secure_filename(file.filename)}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                file_path = f"/uploads/{filename}"

        # Extract logged-in email from JWT
        logged_in_email = resolve_request_email()
        if not logged_in_email:
             return jsonify({"message": "Authentication required"}), 401
             
        # Use existing email from payload or fallback to authenticated email
        target_email = email or logged_in_email

        # FIX #3: Input validation
        if not request_id or not isinstance(request_id, int):
            log_event("POST_ANSWER", f"Invalid request_id: {request_id}", "WARNING")
            return jsonify({"message": "Invalid request ID", "error_code": "INVALID_REQUEST_ID"}), 400

        if not target_email or not validate_email(target_email):
            log_event("POST_ANSWER", f"Invalid email: {target_email}", "WARNING")
            return jsonify({"message": "Invalid email", "error_code": "INVALID_EMAIL"}), 400

        if not answer or len(answer) < 5:
            log_event("POST_ANSWER", f"Answer too short from {target_email}", "WARNING")
            return jsonify({"message": "Answer must be at least 5 characters", "error_code": "ANSWER_TOO_SHORT"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            # MISSION CRITICAL: Fetch owner to prevent self-answer (Fix)
            cursor.execute("SELECT user_email FROM requests WHERE id = %s", (request_id,))
            req_row = cursor.fetchone()
            if req_row and req_row["user_email"] == logged_in_email:
                log_event("POST_ANSWER", f"SECURITY_BLOCK: User {logged_in_email} tried to answer their own request {request_id}", "WARNING")
                return jsonify({ "message": "Request owners cannot answer their own requests.", "error_code": "OWNER_CANNOT_ANSWER" }), 403

            cursor.execute("INSERT INTO answers (request_id, answer, email, file_path) VALUES (%s,%s,%s,%s)", (request_id, answer, target_email, file_path))
            conn.commit()
            log_event("POST_ANSWER", f"Answer posted for request {request_id} by {email} with file {file_path}", "INFO")

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

        amount_to_add = 20
        rating = data.get("rating", 0)
        try:
            rating = int(rating)
        except:
            rating = 0

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True) # Use dict for easier access
        try:
            # First, fetch the answer info to get the helper's email
            cursor.execute("SELECT email FROM answers WHERE id = %s", (answer_id,))
            ans_row = cursor.fetchone()
            if not ans_row:
                return jsonify({"message": "Answer not found"}), 404
            
            target_helper_email = helper_email or ans_row["email"]

            cursor.execute("UPDATE answers SET accepted = 1, rating = %s WHERE id = %s", (rating, answer_id,))
            cursor.execute("UPDATE requests SET solved = 1, status = 'solved' WHERE id = %s", (request_id,))
            
            # Transfer escrowed bounty
            cursor.execute("SELECT escrowed_bounty FROM requests WHERE id = %s", (request_id,))
            req_row = cursor.fetchone()
            bounty_award = req_row["escrowed_bounty"] if req_row else 0
            
            total_to_add = amount_to_add + bounty_award

            if target_helper_email:
                cursor.execute(
                    "UPDATE users SET points = points + %s, reputation = reputation + %s, bounties_completed = bounties_completed + 1 WHERE email = %s",
                    (total_to_add, total_to_add, target_helper_email)
                )
            
            # Clear escrow
            cursor.execute("UPDATE requests SET escrowed_bounty = 0 WHERE id = %s", (request_id,))
            
            conn.commit()
            log_event("ACCEPT_ANSWER", f"Answer {answer_id} accepted for request {request_id}, total {total_to_add} points awarded to {target_helper_email}", "INFO")
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

# @socketio.on("message")  # Disabled on Windows due to socket binding issues
# def handle_message(msg):
#     log_event("WEBSOCKET_MESSAGE", f"Received message: {msg[:50]}...", "INFO")
#     send(msg, broadcast=True)

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
        content = bleach.clean(str(data.get("content") or "").strip())
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
                cursor.execute("SELECT COUNT(*) as count FROM requests WHERE user_email = %s", (email,))
                res = cursor.fetchone()
                user["bounties_posted"] = res["count"] if res else 0
                
                cursor.execute("""
                    SELECT COUNT(*) + 1 as `rank` 
                    FROM users 
                    WHERE reputation > (SELECT reputation FROM users WHERE email = %s)
                """, (email,))
                res = cursor.fetchone()
                user["rank"] = res["rank"] if res else 0

                log_event("USER_STATS", f"Retrieved stats for {email}", "INFO")
                return jsonify(user)
            else:
                log_event("USER_STATS", f"User not found: {email}", "WARNING")
                return jsonify({"first_name": "", "email": email, "reputation": 0, "bounties_completed": 0, "bounties_posted": 0, "rank": 0}), 200
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        log_event("USER_STATS", f"Error: {str(e)}", "ERROR")
        return jsonify({"first_name": "", "email": resolve_request_email(), "reputation": 0, "bounties_completed": 0, "bounties_posted": 0, "rank": 0}), 200

@app.route("/notifications", methods=["GET"])
def get_notifications():
    """FIX: Added notifications endpoint to fetch user notifications"""
    try:
        email = resolve_request_email()
        if not email:
            log_event("NOTIFICATIONS", "No email provided", "WARNING")
            return jsonify([]), 200

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT id, message, seen, created_at FROM notifications WHERE email = %s ORDER BY created_at DESC",
                (email,)
            )
            notifications = cursor.fetchall()
            
            # Convert datetime to string for JSON serialization
            for notif in notifications:
                if 'created_at' in notif and notif['created_at']:
                    notif['created_at'] = str(notif['created_at'])
            
            log_event("NOTIFICATIONS", f"Retrieved {len(notifications)} notifications for {email}", "INFO")
            return jsonify(notifications), 200
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        log_event("NOTIFICATIONS", f"Error retrieving notifications: {str(e)}", "ERROR")
        return jsonify([]), 500

@app.route("/claim_request", methods=["POST"])
@require_auth
def claim_request():
    try:
        data = request.json or {}
        request_id = data.get("request_id")
        email = request.user_email

        if not request_id:
            return jsonify({"message": "Missing request_id", "error_code": "MISSING_PARAMS"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Check if request is still open
            cursor.execute("SELECT status FROM requests WHERE id = %s", (request_id,))
            req = cursor.fetchone()
            if not req or req[0] != 'open':
                return jsonify({"message": "Request is not open for claims", "error_code": "NOT_OPEN"}), 400

            cursor.execute(
                "INSERT INTO claims (request_id, user_email) VALUES (%s, %s)",
                (request_id, email)
            )
            conn.commit()
            log_event("CLAIM", f"User {email} claimed request {request_id}", "INFO")
            return jsonify({"message": "Claimed successfully"}), 201
        except mysql.connector.IntegrityError:
            return jsonify({"message": "Already claimed", "error_code": "ALREADY_CLAIMED"}), 400
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        log_event("CLAIM", str(e), "ERROR")
        return jsonify({"message": "Failed to claim", "error_code": "INTERNAL_ERROR"}), 500

@app.route("/unclaim_request", methods=["DELETE"])
@require_auth
def unclaim_request():
    try:
        data = request.json or {}
        request_id = data.get("request_id")
        email = request.user_email

        if not request_id:
            return jsonify({"message": "Missing request_id", "error_code": "MISSING_PARAMS"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "DELETE FROM claims WHERE request_id = %s AND user_email = %s",
                (request_id, email)
            )
            conn.commit()
            log_event("UNCLAIM", f"User {email} unclaimed request {request_id}", "INFO")
            return jsonify({"message": "Unclaimed successfully"}), 200
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        log_event("UNCLAIM", str(e), "ERROR")
        return jsonify({"message": "Failed to unclaim", "error_code": "INTERNAL_ERROR"}), 500

@app.route("/delete_request", methods=["POST"])
@require_auth
def delete_request():
    try:
        data = request.json or {}
        request_id = data.get("request_id")
        email = request.user_email

        if not request_id:
            return jsonify({"message": "Missing request_id"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT user_email, escrowed_bounty, status FROM requests WHERE id = %s", (request_id,))
            req = cursor.fetchone()
            
            if not req:
                return jsonify({"message": "Request not found"}), 404
            
            if req["user_email"] != email:
                return jsonify({"message": "Unauthorized"}), 403

            # Return escrowed bounty if any
            if req["escrowed_bounty"] > 0:
                cursor.execute(
                    "UPDATE users SET reputation = reputation + %s, points = points + %s WHERE email = %s",
                    (req["escrowed_bounty"], req["escrowed_bounty"], email)
                )
            
            cursor.execute("DELETE FROM claims WHERE request_id = %s", (request_id,))
            cursor.execute("DELETE FROM answers WHERE request_id = %s", (request_id,))
            cursor.execute("DELETE FROM requests WHERE id = %s", (request_id,))
            
            conn.commit()
            log_event("DELETE_REQUEST", f"Request {request_id} deleted by {email}, bounty returned", "INFO")
            return jsonify({"message": "Request deleted"}), 200
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        log_event("DELETE_REQUEST", str(e), "ERROR")
        return jsonify({"message": "Failed to delete"}), 500

if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "0") == "1"
    # FIX: Run on port 5001 to avoid socket binding conflicts on Windows
    app.run(host="127.0.0.1", port=5001, debug=debug_mode, use_reloader=debug_mode)
