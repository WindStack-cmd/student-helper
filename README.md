# StudentsHelper — Peer-to-Peer Student Bounty Network

![Live](https://img.shields.io/badge/Live-https%3A%2F%2Fstudent--helper.pages.dev-brightgreen)
![Built with Flask](https://img.shields.io/badge/Built%20with-Flask-000000)
![MySQL](https://img.shields.io/badge/Database-MySQL-005C84)
![Cloudflare Pages](https://img.shields.io/badge/Deployment-Cloudflare%20Pages-F38020)
![Railway](https://img.shields.io/badge/Backend-Railway-7B2FF7)
![JavaScript](https://img.shields.io/badge/Language-JavaScript-F7DF1E)

StudentsHelper is a peer-to-peer student bounty network built for academic collaboration at scale. Students post problems with bounties, other students claim and solve them, and contributors earn points, reputation, and rank. The platform combines secure authentication, email verification, escrow-backed payouts, and a fast network feed to keep the workflow trustworthy and easy to use. It is designed to feel like a modern product while solving a real student pain point.

Live demo: https://student-helper.pages.dev

---


## 1. 🎯 Project Banner / Title

StudentsHelper — Connect. Solve. Earn. A bounty-driven network for student collaboration.


## 2. 🏷️ Badges

This project uses the following stack and deployment channels:

- Live: https://student-helper.pages.dev
- Built with Flask
- MySQL database
- Cloudflare Pages frontend
- Railway backend deployment
- JavaScript frontend logic

## 3. 🧾 Overview

StudentsHelper is a full-stack platform where students can post academic requests as bounty-backed tasks. Other students can claim those tasks, submit solutions, and earn points and reputation when their work is accepted. The app supports secure authentication, email verification, referrals, and ranked leaderboards so participation stays motivated and measurable. It is a practical example of turning a student community into an incentive-based help network.

## 4. 🚀 Live Demo

[Try it now →](https://student-helper.pages.dev)

## 5. ✨ Key Features

- Bounty posting system with secure escrow and refund logic
- Google and GitHub OAuth login
- JWT authentication and protected API routes
- Email verification for new accounts and OAuth users
- Leaderboard and reputation-based ranking
- Real-time network feed for open requests
- Claim system for active problem solving
- Referral system with commission rewards

## 6. 🧰 Tech Stack

| Frontend | Backend | Database | Deployment |
|---|---|---|---|
| Vanilla JavaScript, HTML, CSS | Flask (Python) | MySQL | Cloudflare Pages + Railway |

## 7. 📸 Screenshots

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

## 8. 🛠️ Getting Started

### Clone and install

```bash
git clone https://github.com/your-username/student-helper.git
cd student-helper/backend
python -m venv .venv
```

### Activate the virtual environment

```bash
# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Configure environment variables

```bash
copy .env.example .env
```

Edit `backend/.env` with your database, JWT, mail, and OAuth settings.

### Run the backend

```bash
python app.py
```

The API will run at `http://127.0.0.1:5001` by default.

### Run the frontend

Open the `frontend` folder with Live Server or serve it locally from your preferred static host.

## 9. ⚙️ Environment Variables

| Variable | Required | Description |
|---|---:|---|
| DB_HOST | ✅ | MySQL host |
| DB_USER | ✅ | MySQL username |
| DB_PASSWORD | ✅ | MySQL password |
| DB_NAME | ✅ | MySQL database name |
| DB_PORT | ✅ | MySQL port |
| JWT_SECRET | ✅ | Secret used to sign JWT tokens |
| FLASK_SECRET_KEY | ✅ | Flask session secret |
| MAIL_SERVER | ✅ | SMTP server hostname |
| MAIL_PORT | ✅ | SMTP server port |
| MAIL_USE_TLS | ✅ | Enable TLS for mail |
| MAIL_USERNAME | ✅ | SMTP username |
| MAIL_PASSWORD | ✅ | SMTP password or app password |
| MAIL_DEFAULT_SENDER | ✅ | Default sender address |
| GOOGLE_CLIENT_ID | ✅ | Google OAuth client ID |
| GOOGLE_CLIENT_SECRET | ✅ | Google OAuth client secret |
| GITHUB_CLIENT_ID | ✅ | GitHub OAuth client ID |
| GITHUB_CLIENT_SECRET | ✅ | GitHub OAuth client secret |
| CORS_ORIGINS | ✅ | Comma-separated allowed origins |
| FRONTEND_URL | ✅ | Public frontend URL used in redirects and emails |
| FLASK_DEBUG | Optional | Development debug flag |
| DB_SSL_DISABLED | Optional | Disable SSL for local MySQL setups |

## 10. 📡 API Endpoints

| Area | Method | Endpoint | Auth |
|---|---:|---|---|
| Auth | POST | /register | No |
| Auth | POST | /login | No |
| Auth | GET | /auth/google | No |
| Auth | GET | /auth/google/callback | No |
| Auth | GET | /auth/github | No |
| Auth | GET | /auth/github/callback | No |
| Requests | GET | /get_requests | No |
| Requests | GET | /get_request_details/:id | No |
| Requests | POST | /post_request | JWT |
| Requests | GET | /get_my_requests | JWT |
| Requests | DELETE | /requests/:id | JWT |
| Requests | GET | /get_active_bounties | No |
| Answers | POST | /post_answer | JWT |
| Answers | GET | /get_answers/:id | No |
| Answers | POST | /accept_answer | JWT |
| Answers | POST | /upvote_answer | No |
| Users | GET | /me | JWT |
| Users | GET | /user_stats | No |
| Users | GET | /leaderboard | No |
| Users | GET | /dashboard_metrics | No |

## 11. 🚢 Deployment

- Frontend is deployed on [Cloudflare Pages](https://student-helper.pages.dev)
- Backend is deployed on Railway at https://student-helper-production-f3b2.up.railway.app
- Database is MySQL hosted on Railway with persistent volume storage

## 12. 👤 Author

- Name: Pratik Yadav
- Email: pratikyadav0104@gmail.com

---

If you want, I can also add a short project summary at the top of the README or convert the deployment section into a table.
