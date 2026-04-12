# StudentsHelper - Community Learning Platform

StudentsHelper connects students who need help with students who can solve problems. Users can post requests with bounties, answer others, and build reputation.

## Current Status

- Backend framework: Flask (Python)
- Database: MySQL
- Auth stack: bcrypt password hashing + JWT token issuance/verification
- Frontend: HTML/CSS/Vanilla JavaScript (multi-page app)
- Realtime chat: Socket.IO code is present, but disabled on Windows runtime
- Frontend architecture: shared `global.css` + reusable `sidebar.js` across pages

## Key Features

- User registration and login with JWT persistence
- **New User Onboarding**: 100 PTS starting balance for all new accounts
- **Bounty Escrow System**: Automated point deduction on post and awarding on acceptance
- **Expiry Lifecycle Tracking**: Visual countdowns (EXPIRING SOON) and automated expiration badges
- **Node Claims**: Students can "Claim" an objective to signal they are working on it
- Answer submission and answer acceptance flow
- Optional answer file attachments (saved to backend uploads)
- Answer upvotes and community ranking
- Reputation and leaderboard stats (Ledger)
- Dashboard metrics for bounties posted, completed, and global rank
- Notifications when a request receives an answer
- Request details modal with answers + view counting
- Request filtering with pagination, search, category, and sort controls
- Profile and account purge flows
- Shared frontend styling and sidebar navigation across pages
- Theme persistence via localStorage dark mode toggle

## Changes Implemented

This section summarizes the major changes already applied in the project.

### 1) Security hardening and auth updates

- Restricted CORS from wildcard to an allowlist using CORS_ORIGINS.
- Removed hardcoded DB password fallback and now require DB_PASSWORD in environment.
- Added bcrypt password hashing and secure password verification.
- Added JWT token generation on login with token verification helpers.
- Added helper auth utilities:
  - get_token_from_request
  - verify_jwt_token
  - resolve_request_email
  - require_auth decorator (available for protected routes)
- Added input validation helpers for email, password, title, and description.
- Added route-level rate limiting with Flask-Limiter.

### 2) Backend reliability and API behavior

- Added structured logging helper (log_event) and applied across endpoints.
- Added /notifications endpoint and wired notification creation when answers are posted.
- Added /get_request_details/<request_id> endpoint for request + answers details.
- Added /upvote_answer endpoint.
- Added uploads serving route: /uploads/<filename>.
- Improved /get_requests with pagination and search support.
- Extended /get_requests with status filter, category filter, and sort options.
- Removed duplicate route issues noted in prior revisions.
- Standardized many API error responses with message + error_code patterns.

### 3) Database and schema improvements

- Added startup database bootstrap with CREATE DATABASE IF NOT EXISTS.
- Ensured core tables exist: users, requests, answers, posts, notifications.
- Added safe ALTER operations for legacy and new columns (e.g., category, views, upvotes, file_path, rating).
- Added performance indexes for:
  - status/created_at queries
  - user_email lookups
  - full-text search on title + description

### 4) Runtime/platform updates

- Backend runs on port 5001 to avoid Windows socket conflicts.
- Socket.IO runtime call is disabled on Windows path (HTTP API remains active).
- Environment variable loading added via python-dotenv.

### 5) Frontend refactors and integration updates

- Refactored all pages to shared global.css and reusable sidebar.js patterns.
- Unified navigation injection pattern across app and public pages.
- Request help page styling improvements applied.
- Frontend API integration updated to align with backend port and notifications flow.
- Notifications badge count now loads from /notifications with bearer token.
- Added theme bootstrap script with persisted dark mode preference.

### 6) Recent repository changes (summary)

- Refactor: migrated HTML pages to shared global.css and sidebar.js.
- UI: dashboard/chat/auth/core pages integrated and stabilized.
- Backend: Flask API hardening and data-flow fixes merged.
- Merge/conflict cleanup: duplicate logic and fetch-flow conflicts resolved.

### 7) Bounty Lifecycle & Security Hardening (Latest - 2026-04-12)
- **Feature: Starting Balance Migration**:
  - Implemented automatic 100 PTS / 100 Reputation credit for new users in `/register`.
  - Added a one-time database migration hook in `init_db` to credit 100 PTS to all existing users at 0 balance.
- **Feature: Expiry Intelligence**:
  - Updated dashboard cards with real-time expiry indicators.
  - Added "EXPIRING SOON" warning for requests with <24h remaining.
  - Added "EXPIRED" badge for past-due requests (automated locking).
- **Feature: Security & Ownership Integrity**:
  - **Self-Answering Block**: Implemented dual-layer block (Frontend + Backend 403 Forbidden) to prevent owners from answering their own requests.
  - **Self-Claiming Block**: Owners are restricted from claiming their own objectives.
  - **Dynamic Modal UI**: Users now see `CANNOT_RESPOND: REQUEST_OWNER` instead of the answer form on their own posts.
- **Bug Fix: SQL Reserved Word Conflict**:
  - Resolved `MySQL 8.0+` syntax error where `rank` (reserved for window functions) was used as an unquoted alias. Escaped as `` `rank` ``.
- **Bug Fix: Bounty Awarding Flow**:
  - Resolved 500 error on `/accept_answer` by fixing `UnboundLocalError` related to helper email retrieval.
  - Standardized status update from `closed` to `solved` for better UI badge targeting.
  - Fixed "Bounties Posted" metric returning 0 by correcting the backend aggregation query.
- **UI/UX Refinement**:
  - Improved "Accept Answer" button visibility (Owner-only).
  - Awarded bounties now show as `ACCEPTED_SOLUTION` in the modal.

### 8) Bug Fixes & Stability Improvements (Latest - 2026-04-12)

#### CORS Preflight & Rate Limiting
- **Issue**: "Response to preflight request doesn't pass access control check: It does not have HTTP ok status"
- **Solution**:
  - Created custom rate limiter key function that exempts OPTIONS requests
  - Added explicit `@app.before_request` handler for OPTIONS method returning 200 status
  - Enhanced CORS config to explicitly include all HTTP methods
  - **Files**: `backend/app.py` (lines 19-50)

#### 429 Too Many Requests Errors
- **Issue**: Read-only GET endpoints (dashboard, help-others, community-chat) hitting rate limits
- **Solution**:
  - Increased default rate limits: 500/hour, 2000/day (from 50/hour, 200/day)
  - Custom key function exempts: OPTIONS requests, `/get_requests`, `/get_leaderboard`, `/get_user_stats`
  - Removed redundant endpoint-specific rate limit decorators
  - **Files**: `backend/app.py` (lines 19-50, 485-486), `webzip/js/dashboard.js` (lines 30-36), `webzip/pages/help-others.html` (lines 737-745)

#### Leaderboard Null Reference Error
- **Issue**: "Cannot read properties of null (reading 'substring')" on leaderboard load
- **Root Cause**: Backend returned user data with null `first_name` values
- **Solution**: Added null checks with fallback chain: `u.first_name || u.name || u.email?.split('@')[0] || "User"`
- **Files**: `webzip/pages/community-chat.html` (lines 1070-1082)

#### Missing Favicon
- **Issue**: 404 error for favicon requests
- **Solution**: Added `/favicon.ico` route returning 204 No Content
- **Files**: `backend/app.py` (lines 266-268)

#### Request Posting - Missing Auth Headers
- **Issue**: `getAuthHeaders is not defined` error in request-help.js
- **Root Cause**: script.js (containing getAuthHeaders) was not included in request-help.html
- **Solution**:
  - Added `<script src="../js/script.js"></script>` to request-help.html
  - Simplified request-help.js to extract email from localStorage directly
  - Now sends proper JSON body: `{ title, description, email, bounty }`
- **Files**: `webzip/pages/request-help.html` (line 598), `webzip/js/request-help.js` (lines 1-67)

#### Duplicate Request Creation
- **Issue**: Submitting one request created multiple entries in database
- **Root Cause**: Multiple fetch calls or form resubmission
- **Solution**: Simplified form submission with single fetch call and proper error handling
- **Files**: `webzip/js/request-help.js`

## Backend API Endpoints

### System

- GET /
- GET /favicon.ico
- GET /uploads/<filename>

### Auth

- POST /register
- POST /login

### Requests and Answers

- POST /post_request
- GET /get_requests
- GET /get_request_details/<int:request_id>
- GET /get_answers/<int:request_id>
- POST /upvote_answer
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
  - .env.example
  - .gitignore
  - app.py
  - requirements.txt
  - FIXES_APPLIED.md
  - uploads/
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
DB_SSL_DISABLED=1
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

## Current Stable Features ✅

- User registration with bcrypt password hashing
- JWT-based authentication & login
- **Starting Balance**: 100 PTS onboarding credit
- **Bounty Escrow**: Points are held in escrow and awarded automatically to the solver
- **Request Claiming System**: Students can signal active work on an objective
- **Request Status Lifecycle**: Open → Expiring Soon → Solved/Expired
- Post help requests with bounty amounts
- Hunt Mode - browse and filter active requests
- Search, filter, and sort requests (by title, status, bounty, date)
- Leaderboard with user rankings (Ledger)
- Dashboard with real-time metrics (Posted, Completed, Rank)
- User profiles with reputation tracking (Identity)
- Notifications system
- Clean, modern dark-theme UI

## Known Limitations & Next Priority Features

### Critical for SaaS (Next Sprint):
1. **Email Verification** - Verify email on signup to prevent spam/abuse
2. **Pro Stripe Integration** - Platform fee deduction on bounty payouts
3. **Advanced Filtering** - Filter by "Claimed vs Unclaimed"

### Medium Priority:
5. Request categories/tags (Math, Code, Essay, etc)
6. User reputation system (earn points for answers)
7. Answer rating/quality system
8. Request sorting options (newest, highest bounty, most viewed)

## Notes

- Chat websocket handler is currently disabled in backend runtime for Windows compatibility.
- The repository includes helper scripts and logs used during migration and fix phases.
- A local `backend/student_helper.db` file exists in the repo, but the active backend runtime in `backend/app.py` uses MySQL.
