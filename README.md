# StudentsHelper - Community Learning Platform

StudentsHelper connects students who need help with students who can solve problems. Users can post requests with bounties, answer others, and build reputation.

## Current Status

- Backend framework: Flask (Python)
- Database: MySQL
- Auth stack: bcrypt password hashing + JWT token issuance
- Frontend: HTML/CSS/Vanilla JavaScript (multi-page app)
- Realtime chat: Socket.IO code is present, but disabled on Windows runtime

## Key Features

- User registration and login
- Bounty-based request posting
- Answer submission and answer acceptance flow
- Reputation and leaderboard stats
- Dashboard metrics
- Notifications when a request receives an answer
- Profile and account purge flows
- Shared frontend styling and sidebar navigation across pages

## Changes Implemented

This section summarizes the major changes already applied in the project.

### 1) Security hardening

- Restricted CORS from wildcard to an allowlist using CORS_ORIGINS.
- Removed hardcoded DB password fallback and now require DB_PASSWORD in environment.
- Added bcrypt password hashing and secure password verification.
- Added JWT token generation on login.
- Added helper auth utilities:
  - get_token_from_request
  - verify_jwt_token
  - require_auth decorator (available for protected routes)
- Added input validation helpers for email, password, title, and description.
- Added route-level rate limiting with Flask-Limiter.

### 2) Backend reliability and API behavior

- Added structured logging helper (log_event) and applied across endpoints.
- Added /notifications endpoint and wired notification creation when answers are posted.
- Added /get_request_details/<request_id> endpoint for request + answers details.
- Improved /get_requests with pagination and search support.
- Removed duplicate route issues noted in prior revisions.
- Standardized many API error responses with message + error_code patterns.

### 3) Database and schema improvements

- Added startup database bootstrap with CREATE DATABASE IF NOT EXISTS.
- Ensured core tables exist: users, requests, answers, posts, notifications.
- Added safe ALTER operations for legacy requests columns.
- Added performance indexes for:
  - status/created_at queries
  - user_email lookups
  - full-text search on title + description

### 4) Runtime/platform updates

- Backend runs on port 5001 to avoid Windows socket conflicts.
- Socket.IO runtime call is disabled on Windows path (HTTP API remains active).
- Environment variable loading added via python-dotenv.

### 5) Frontend refactors and integration updates

- Refactored pages to shared global.css and reusable sidebar.js patterns.
- Request help page styling improvements applied.
- Frontend API integration updated to align with backend port and notifications flow.
- Added safer response handling in key frontend pages (as documented in project notes).

## Backend API Endpoints

### Auth

- POST /register
- POST /login

### Requests and Answers

- POST /post_request
- GET /get_requests
- GET /get_request_details/<int:request_id>
- GET /get_answers/<int:request_id>
- GET /get_active_bounties
- GET /get_my_requests
- GET /get_archived_requests
- POST /post_answer
- POST /accept_answer

### Stats and Community

- GET /dashboard_metrics
- GET /leaderboard
- GET /user_stats
- GET /get_posts
- POST /create_post
- POST /accept_post

### Account and Notifications

- POST /purge_user
- POST /update_reputation
- GET /notifications

## Project Structure

- backend/
  - app.py
  - requirements.txt
  - FIXES_APPLIED.md
- webzip/
  - index.html
  - css/
  - js/
  - pages/
- patch_db.py
- fix_avatars.py
- dump_schema.py
- schema.txt
- flask_routes.txt
- commits.txt

## Quick Start

### 1) Backend setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Create backend/.env with at least:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=student_helper
JWT_SECRET=change_this_secret
CORS_ORIGINS=http://127.0.0.1:5501,http://localhost:3000,http://localhost:8000
FLASK_DEBUG=1
```

Run backend:

```bash
python app.py
```

Backend URL: http://127.0.0.1:5001

### 2) Frontend setup

```bash
cd webzip
python -m http.server 5501
```

Frontend URL: http://127.0.0.1:5501

## Tech Stack

- Backend: Flask, Flask-CORS, Flask-Limiter, bcrypt, PyJWT, python-dotenv
- Database: MySQL (mysql-connector-python)
- Frontend: HTML, CSS, Vanilla JavaScript

## Notes

- Chat websocket handler is currently disabled in backend runtime for Windows compatibility.
- The repository includes helper scripts and logs used during migration and fix phases.
