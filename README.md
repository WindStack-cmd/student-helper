# StudentsHelper — Community Learning Platform

An interactive platform connecting students who need help with those who can provide it. Users can post help requests, offer point bounties, and build reputation by solving other students' problems — all powered by a real-time backend and a modern, responsive UI.

## ✨ Features

- **User Authentication** — Register, log in, change password, and manage your profile.
- **Bounty System** — Post help requests with a point bounty to incentivize quick, quality answers.
- **Answer & Accept** — Helpers submit answers; requesters accept the best one, automatically awarding bounty points and reputation.
- **Leaderboard** — Live rankings based on reputation and bounties completed.
- **Dashboard** — Personalized metrics (bounties cleared, ledger stake, pending jobs) with tabbed views for network, personal, and archived requests.
- **Community Chat** — Real-time messaging powered by WebSockets (Socket.IO) *(Currently disabled on Windows)*
- **Notifications** — In-app notifications when someone answers your request *(Now fully functional)*
- **User Profiles** — View your own profile or browse other users' stats.
- **Help Others Feed** — Browse and capture active bounty requests from other students.
- **Settings & Account Management** — Update profile details and purge account data.
- **Dark/Light Theme** — Toggle between themes across all pages.

## 🛡️ Security & Protection

StudentsHelper implements multiple layers of security to protect user data and ensure platform integrity:

### Backend Security
- **Bcrypt Hashing** — All user passwords are salt-hashed using `bcrypt` (12 rounds) before being stored in the database.
- **JWT Authorization** — Secure session management using JSON Web Tokens. Protected API endpoints require a valid `Authorization: Bearer <token>` header.
- **Rate Limiting** — Global and route-specific rate limiting via `Flask-Limiter` to prevent brute-force attacks and service abuse (e.g., 5 login attempts/min).
- **CORS Hardening** — Cross-Origin Resource Sharing is restricted to authorized frontend domains only.
- **Input Validation** — Strict validation for emails, passwords, and help request content to prevent malformed data and injection.
- **Environment Isolation** — Sensitive credentials (DB, JWT Secret) are managed through environment variables (`.env`).
- **Standardized Logging** — Comprehensive event logging for all critical operations (auth, data mutation, errors).

### Frontend Security
- **Authentication Guard** — Every protected page includes an initialization guard that verifies the active session. Unauthenticated users are automatically redirected to the login terminal.
- **Session Persistence** — Secure management of user identity in `localStorage` with systematic clearing upon logout or session expiry.
- **Data Privacy** — Frontend requests are scoped to the authenticated user's identity, preventing unauthorized data access.
- **Structural Purge** — A secure, multi-confirmation process for permanent account deletion, ensuring all associated data (posts, requests, notifications) is removed from the system.

## 🛠 Tech Stack

### Frontend
- **HTML5 / CSS3 / Vanilla JavaScript**
- 18 distinct pages with a shared sidebar navigation
- Centralized design system via `global.css` and `style.css`
- Modular JS (`dashboard.js`, `leaderboard.js`, `profile.js`, `sidebar.js`, `theme.js`, etc.)

### Backend
- **Python / Flask** — RESTful API server
- **Flask-CORS** — Cross-Origin Resource Sharing (Hardened)
- **Flask-SocketIO** — Real-time, bi-directional WebSocket communication *(Currently disabled on Windows)*
- **Flask-Limiter** — Request rate limiting for security
- **Bcrypt & PyJWT** — Password hashing and session tokens
- **MySQL** — Production-grade relational database
- **mysql-connector-python** — MySQL driver for Python

## 📁 Project Structure

```
.
├── backend/
│   ├── app.py                 # Main Flask application with Security Layers
│   ├── .env.example           # Template for environment variables
│   └── requirements.txt       # Python backend dependencies
├── webzip/
│   ├── index.html              # Landing page
│   ├── package.json            # Node configuration
│   ├── css/
│   │   ├── global.css          # Shared design tokens & utilities
│   │   └── style.css           # Page-specific styles
│   ├── js/
│   │   ├── script.js           # Core app logic (auth, requests, answers)
│   │   ├── dashboard.js        # Dashboard metrics & tab switching
│   │   ├── leaderboard.js      # Leaderboard rendering & rank calculation
│   │   ├── profile.js          # Profile page logic
│   │   ├── sidebar.js          # Sidebar navigation & active-page highlight
│   │   ├── theme.js            # Dark/Light theme toggle
│   │   ├── contact.js          # Contact form handling
│   │   └── request-help.js     # Help request form logic
│   └── pages/
│       ├── login.html          # Login page
│       ├── register.html       # Registration page
│       ├── dashboard.html      # Main dashboard with metrics & feed tabs
│       ├── leaderboard.html    # Rankings & user stats sidebar
│       ├── help-request.html   # Submit a new help request
│       ├── request-help.html   # Request help form
│       ├── help-others.html    # Browse & capture active bounties
│       ├── my-requests.html    # View your own requests
│       ├── view-requests.html  # Browse all open requests
│       ├── request-details.html# View a single request & its answers
│       ├── community-chat.html # Real-time chat room
│       ├── notifications.html  # Notification center
│       ├── profile.html        # Your profile page
│       ├── user-profile.html   # View another user's profile
│       ├── settings.html       # Account settings & purge
│       ├── change-password.html# Change password page
│       ├── contact.html        # Contact / feedback form
│       └── about.html          # About the platform
├── patch_db.py                 # Utility — patch/migrate the MySQL schema
├── fix_avatars.py              # Utility — repair avatar data
├── dump_schema.py              # Utility — dump current DB schema to file
├── schema.txt                  # Exported database schema snapshot
└── FIXES_APPLIED.md           # Log of applied fixes and changes

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MySQL 8.0+
- Node.js (for frontend development)

### Backend Setup
1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   - Copy `.env.example` to `.env`
   - Set your MySQL credentials and JWT secret

5. **Start the backend server:**
   ```bash
   python app.py
   ```
   Server runs on `http://127.0.0.1:5001`

### Frontend Setup
1. **Navigate to webzip directory:**
   ```bash
   cd webzip
   ```

2. **Start a local HTTP server:**
   ```bash
   # Using Python
   python -m http.server 5501

   # Or using Node.js
   npx http-server -p 5501
   ```

3. **Open in browser:**
   Visit `http://127.0.0.1:5501`

### Database Setup
- Run `patch_db.py` to initialize/update the database schema
- Use `dump_schema.py` to export current schema
├── flask_routes.txt            # Exported route listing
└── README.md
```

## 🗄 Database Schema (MySQL)

| Table           | Key Columns |
|-----------------|-------------|
| **users**       | `id`, `first_name`, `email`, `password`, `points`, `reputation`, `bounties_completed` |
| **requests**    | `id`, `title`, `description`, `user_email`, `bounty`, `status`, `captured_by`, `solved`, `created_at` |
| **answers**     | `id`, `request_id`, `answer`, `email`, `accepted`, `created_at` |
| **posts**       | `id`, `first_name`, `title`, `content`, `user_email`, `bounty`, `created_at` |
| **notifications** | `id`, `email`, `message`, `seen`, `created_at` |

## 🚀 Setup & Installation

1. **Prerequisites**: Ensure you have Python 3.x and MySQL installed.
2. **Setup Environment**:
   - Create a `.env` file in the `backend/` directory.
   - Define: `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, and `JWT_SECRET`.
3. **Start MySQL**: Ensure your local MySQL server is running.
4. **Install Backend Dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
5. **Initialize & Run**:
   ```bash
   python app.py
   ```
```

Open `http://localhost:8000` (or the port shown) in your browser.

## 📡 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/register` | Register a new user |
| `POST` | `/login` | Authenticate and return user details |

### Dashboard & Stats
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/dashboard_metrics?email=` | Personalized dashboard stats |
| `GET` | `/leaderboard` | Top users ranked by reputation |
| `GET` | `/user_stats?email=` | Individual user stats |

### Requests
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/post_request` | Create a new help request with bounty |
| `GET` | `/get_requests` | All open, unsolved requests |
| `GET` | `/get_active_bounties` | Open requests with bounty > 0 |
| `GET` | `/get_my_requests?email=` | Requests posted by a specific user |
| `GET` | `/get_archived_requests` | Solved / closed requests |

### Answers
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/post_answer` | Submit an answer to a request |
| `GET` | `/get_answers/<request_id>` | Get all answers for a request |
| `POST` | `/accept_answer` | Accept an answer — awards bounty & reputation |

### Community & Posts
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/get_posts` | List all community posts |
| `POST` | `/create_post` | Create a new community post |
| `POST` | `/accept_post` | Capture / assign a request to a helper |

### Account Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/update_reputation` | Manually boost a user's reputation |
| `POST` | `/purge_user` | Delete all data associated with a user account |

### Notifications
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/notifications` | Get user notifications (requires JWT auth) |

### Real-time
| Protocol | Event | Description |
|----------|-------|-------------|
| WebSocket | `message` | Bi-directional chat via Socket.IO *(Currently disabled on Windows)* |

## 🔄 Recent Updates & Fixes

### v1.1.0 - April 2026
- **🔔 New Notifications System**
  - Added `/notifications` API endpoint for fetching user notifications
  - Fixed CORS error on notification button in dashboard
  - Notifications are user-specific and JWT-authenticated
  - Displays "Someone answered your request" notifications

- **🔧 Backend Stability Improvements**
  - Changed backend port from 5000 to 5001 to avoid Windows socket binding conflicts
  - Temporarily disabled Flask-SocketIO for Windows compatibility (WebSocket chat disabled)
  - Removed duplicate route definitions (`/get_answers`, `/accept_answer`)
  - Improved error handling and logging

- **🎨 Frontend API Updates**
  - Updated all API endpoints to use port 5001
  - Enhanced notification loading with better error handling
  - Added null-safety checks for API responses

- **🛡️ Security Enhancements**
  - Improved input validation for notification requests
  - Enhanced JWT token verification for notification access
  - Better CORS configuration for cross-origin requests

### Technical Notes
- **Backend Port**: Now runs on `http://127.0.0.1:5001` (changed from 5000)
- **WebSocket Status**: Disabled on Windows due to socket binding issues
- **Database**: No schema changes required for notifications (uses existing `notifications` table)
- **CORS**: Properly configured for `http://127.0.0.1:5501` frontend origin

## 🤝 Contributing

1. Fork the project.
2. Create your feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

## 📄 License

Distributed under the MIT License.
