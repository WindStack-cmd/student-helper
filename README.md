# StudentsHelper — Community Learning Platform

[![Status](https://img.shields.io/badge/Status-Production--Ready-success)](#)
[![Security](https://img.shields.io/badge/Security-Hardened-blue)](#)
[![Auth](https://img.shields.io/badge/Auth-JWT%20%2B%20OAuth-blueviolet)](#)
[![License](https://img.shields.io/badge/License-MIT-green)](#)

StudentsHelper is a full-stack community platform that facilitates **peer-to-peer academic assistance**. Students who need help post bounty-backed requests; expert students claim and solve them, earning reputation and points through a secure escrow system.

**Tech Stack:** Flask (Python), MySQL, Vanilla JS, HTML/CSS. Auth via JWT, bcrypt, and OAuth.

---

## 📸 Screenshots

<details>
<summary><strong>Click to expand screenshots</strong></summary>

- **Landing Page:** Entry point with bold typography and dark interface.
  ![Landing Page](docs/screenshots/landing-page.png)
- **About Page:** Core platform values.
  ![About Page](docs/screenshots/about-page.png)
- **Registration:** Dual-mode onboarding (Seek/Distribute Data).
  ![Registration Page](docs/screenshots/register-page.png)
- **Dashboard:** Full workspace view with network metrics.
  ![Dashboard](docs/screenshots/dashboard-page.png)
</details>

---

## 🏗️ Architecture & Core Flow

- **Frontend:** Multi-page Glassmorphic UI (Vanilla JS). Root directory is `/frontend`.
- **Backend:** Stateless Flask REST API with structured logging & CORS security.
- **Database:** MySQL 8.0+ with relational integrity.
- **Lifecycle Flow:** 
  1. **Register** (Email/OAuth) → **Verify** (24h TTL)
  2. **Post Request** → Bounty points placed in **Escrow**
  3. Community **Claims** and **Solves** objective
  4. Owner **Accepts** → Bounty payout + Reputation earned (Unanswered expire in 7 days).

---

## ✨ Key Features

- **Security & Auth:** JWT sessions (24h), bcrypt (12 rounds), Rate Limiting, server-side Input Validation. Google & GitHub OAuth integration.
- **Economy & Bounties:** Secure escrow logic, automated payouts, 7-day expiry refund, and a referral program (10% commission).
- **Requests System:** Categorized requests, claim/unclaim logic, file attachments, upvotes, and view counters.
- **UI / UX:** 
  - Glassmorphic dark mode (saved in `localStorage`).
  - Command Palette (`Ctrl+K`).
  - Dashboard with "Share Request", enhanced Empty States, and Chart.js metrics.
  - Dynamic shared sidebar updates & Real-time notification engine.

---

## 🚦 Quick Start

### 1. Backend Setup
```bash
git clone https://github.com/your-username/student-helper.git
cd student-helper/backend
python -m venv .venv

# Activate venv: 
# `.venv\Scripts\activate` (Windows)
# `source .venv/bin/activate` (macOS/Linux)

pip install -r requirements.txt
cp .env.example .env
```
> **Team Collaboration Tip:** Teammates should maintain their own personal `.env` files with local database credentials to avoid collaboration conflicts. 

Start the API:
```bash
python app.py # Server available at http://127.0.0.1:5001
```

### 2. Frontend Setup
Open the project in VS Code and click **"Go Live"** via the Live Server extension.
> **Note:** Ensure your Live Server settings (`.vscode/settings.json`) point the root to the `/frontend` directory (default port: 5504).

---

<details>
<summary><h2>⚙️ Environment Variables (<code>backend/.env</code>)</h2></summary>

| Variable | Required | Description |
|----------|----------|-------------|
| `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | ✅ | MySQL database credentials |
| `JWT_SECRET`, `FLASK_SECRET_KEY` | ✅ | Secure keys for JWT and sessions |
| `MAIL_SERVER`, `MAIL_USERNAME`, `MAIL_PASSWORD` | ✅ | SMTP credentials for email engine |
| `MAIL_DEFAULT_SENDER` | ✅ | Default sender address |
| `GOOGLE_CLIENT_ID`, `GITHUB_CLIENT_ID` (and Secrets) | — | OAuth Application Secrets |
| `CORS_ORIGINS`, `FRONTEND_URL` | — | Whitelisted domains for CORS / Emails |

</details>

<details>
<summary><h2>📡 API Reference Summary</h2></summary>

- **Authentication:** `/register`, `/login`, `/auth/google`, `/auth/github`, `/verify_email`, `/resend_verification`
- **Requests Lifecycle:** `/post_request`, `/get_requests`, `/get_request_details/<id>`, `/get_my_requests`, `/delete_request`
- **Answers & Economy:** `/post_answer`, `/accept_answer`, `/upvote_answer`, `/claim_request`, `/unclaim_request`
- **Users & Dashboard:** `/user_stats`, `/get_balance`, `/dashboard_metrics`, `/leaderboard`
</details>

<details>
<summary><h2>📋 Recent Updates (Changelog)</h2></summary>

- **Frontend Directory Refactor:** Consolidated project root by moving `index.html` into `frontend/` and appropriately routing all assets. Fixed Favicon 404s and broken image links.
- **UX Enhancements:** Added a quick "Share Request" feature in the dashboard modal, implemented visual feedback for Empty State UI components, and improved dynamic sidebar updates.
- **Backend Stability:** Resolved critical MySQL connection issues ensuring stable API-DB communication. Structured environment variables to optimize team collaboration.
- **Previous Features (v2.6+):** Dynamic leaderboard auto-refresh, referral card UI, functional network filters, robust database cleanup of legacy users, command palette, and strict CORS security.
</details>

---

## 📝 License
This project is open-source under the MIT License. Please attribute the original author when using this blueprint.
