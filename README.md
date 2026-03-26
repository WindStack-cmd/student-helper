# StudentsHelper / Community Learning Platform

An interactive platform connecting students who need help with those who can provide it. Users can post requests for help, offer bounties (points), and build reputation by solving other students' problems.

## Features

- **User Authentication:** Register and log in securely.
- **Bounty System:** Users can post help requests and offer a point bounty.
- **Answering & Reputation:** Helpers can submit answers. When an answer is accepted, the helper earns the bounty points and their reputation increases.
- **Leaderboard:** Ranks users based on their reputation and bounties completed.
- **Dashboard Metrics:** Overview of total points in the system, pending requests, and personal stats.
- **Real-time Notifications & Chat:** Built-in WebSocket connection (via Socket.IO) for real-time messages and notifications when an answer is posted.

## Tech Stack

### Frontend
- HTML5, CSS3, JavaScript (Vanilla)
- Organised into distinct pages (`index.html`, dashboard, help pages, etc.)
- Centralized styling via `global.css`

### Backend
- **Python / Flask**: Serves the RESTful API endpoints.
- **Flask-CORS**: Handles Cross-Origin Resource Sharing.
- **Flask-SocketIO**: Enables real-time, bi-directional communication.
- **SQLite**: Lightweight, file-based relational database (`student_helper.db`).

## Project Structure

```
.
├── backend/
│   ├── app.py                 # Main Flask application and API routes
│   └── student_helper.db      # SQLite database (auto-generated)
├── webzip/
│   ├── pages/                 # HTML pages (dashboard, login, forms, etc.)
│   ├── css/                   # Stylesheets including global.css
│   ├── js/                    # Client-side JavaScript logic
│   ├── index.html             # Landing page
│   └── package.json           # Node configuration (optional frontend tooling)
└── README.md
```

## Setup & Installation

### Backend Setup

1. **Prerequisites**: Ensure you have Python 3.x installed.
2. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```
3. **Install dependencies**:
   ```bash
   pip install Flask flask-cors flask-socketio
   ```
4. **Run the server**:
   ```bash
   python app.py
   ```
   The Flask server will start on `http://127.0.0.1:5000` (or another port depending on your configuration). The SQLite database will be initialized automatically on the first run.

### Frontend Setup

1. **Launch the Web App**:
   You can serve the `webzip` folder using any static file server, for example:
   ```bash
   cd webzip
   npx serve .
   # or
   python -m http.server 8000
   ```
2. **Access the application**:
   Open a browser and navigate to the address provided by the static file server (e.g., `http://localhost:8000`).

## API Endpoints Overview

- `POST /register`: Register a new user footprint.
- `POST /login`: Authenticate a user and return details.
- `GET /dashboard_metrics`: Retrieve general platform statistics.
- `GET /leaderboard`: Get the top helpers based on reputation.
- `POST /post_request`: Create a new help request with a bounty.
- `GET /get_requests`: Retrieve all help requests.
- `POST /post_answer`: Submit an answer to a specific request.
- `GET /get_answers/<request_id>`: Get all answers for a given request.
- `POST /accept_answer`: Mark an answer as accepted and transfer the bounty.
- `POST /update_reputation`: Manually boost reputation points.
- `GET /get_posts` & `POST /create_post`: Manage general community posts.
- `POST /accept_post`: Mark a request as captured/assigned to a user.

## Contributing

1. Fork the project.
2. Create your feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

## License

Distributed under the MIT License. See `package.json` for more details.
