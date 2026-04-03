# StudentsHelper — Community Learning Platform

An interactive platform connecting students who need help with those who can provide it. Users can post help requests, offer point bounties, and build reputation by solving other students' problems — all powered by a real-time backend and a modern, responsive UI.

## ✨ Features

- **User Authentication** — Register, log in, change password, and manage your profile.
- **Bounty System** — Post help requests with a point bounty to incentivize quick, quality answers.
- **Answer & Accept** — Helpers submit answers; requesters accept the best one, automatically awarding bounty points and reputation.
- **Leaderboard** — Live rankings based on reputation and bounties completed.
- **Dashboard** — Personalized metrics (bounties cleared, ledger stake, pending jobs) with tabbed views for network, personal, and archived requests.
- **Community Chat** — Real-time messaging powered by WebSockets (Socket.IO).
- **Notifications** — In-app notifications when someone answers your request.
- **User Profiles** — View your own profile or browse other users' stats.
- **Help Others Feed** — Browse and capture active bounty requests from other students.
- **Settings & Account Management** — Update profile details and purge account data.
- **Dark/Light Theme** — Toggle between themes across all pages.

## 🛠 Tech Stack

### Frontend
- **HTML5 / CSS3 / Vanilla JavaScript**
- 18 distinct pages with a shared sidebar navigation
- Centralized design system via `global.css` and `style.css`
- Modular JS (`dashboard.js`, `leaderboard.js`, `profile.js`, `sidebar.js`, `theme.js`, etc.)

### Backend
- **Python / Flask** — RESTful API server
- **Flask-CORS** — Cross-Origin Resource Sharing
- **Flask-SocketIO** — Real-time, bi-directional WebSocket communication
- **MySQL** — Production-grade relational database for all persistent data (users, requests, answers, posts, notifications)
- **mysql-connector-python** — MySQL driver for Python

## 📁 Project Structure

```
.
├── backend/
│   ├── app.py                 # Main Flask application and API routes
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

1. **Prerequisites**: Ensure you have Python 3.x installed.
2. **Start MySQL**: Ensure a MySQL server is running and accessible.
3. **Configure database credentials** (optional): set `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`.
4. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```
5. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
6. **Run the server**:
   ```bash
   python app.py
   ```
   The Flask server will start on `http://127.0.0.1:5000`. MySQL tables are initialized automatically on the first successful connection.

### Prerequisites

- Python 3.x
- MySQL Server running locally
- Node.js / npm (optional, for serving the frontend)

### 1. Database Setup

Make sure MySQL is running and create the database (the app will auto-create it on first run, but you can also do it manually):

```sql
CREATE DATABASE IF NOT EXISTS student_helper;
```

### 2. Backend Setup

```bash
cd backend
pip install flask flask-cors flask-socketio mysql-connector-python
python app.py
```

The Flask server starts on `http://127.0.0.1:5000`. The database tables are initialized automatically on first launch.

> **Note:** Update the MySQL credentials in `app.py` → `get_db_connection()` to match your local setup.

### 3. Frontend Setup

Serve the `webzip` folder with any static file server:

```bash
cd webzip
npx serve .
# or
python -m http.server 8000
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

### Real-time
| Protocol | Event | Description |
|----------|-------|-------------|
| WebSocket | `message` | Bi-directional chat via Socket.IO |

## 🤝 Contributing

1. Fork the project.
2. Create your feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

## 📄 License

Distributed under the MIT License.
