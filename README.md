# ANMS — Advanced Narcotics Monitoring System (v3)

A production-hardened, full-stack web application for monitoring, detecting, and analyzing suspicious narcotics-related activity across social media platforms (Telegram, WhatsApp, Instagram, Google). The system uses **RoBERTa-based NLP** for text classification, **Fernet encryption** for data-at-rest security, **JWT authentication** with role-based access control, and a **Flask + MySQL** backend with a Bootstrap dashboard.

---

## Table of Contents

- [Features](#features)
- [Security Features](#security-features)
- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [Authentication & Authorization](#authentication--authorization)
- [API Endpoints](#api-endpoints)
- [Machine Learning Pipeline](#machine-learning-pipeline)
- [Monitoring & Logging](#monitoring--logging)
- [Security Checklist](#security-checklist)
- [Tech Stack](#tech-stack)
- [License](#license)

---

## Features

| Module | Description |
|---|---|
| **Multi-Platform Scraping** | Scrapes data from Google, Instagram, Telegram, and WhatsApp using official APIs |
| **Keyword Management** | Add, update, delete, and search keywords that drive scraping |
| **NLP Classification** | Fine-tuned RoBERTa model classifies text as suspicious or not |
| **Data Encryption** | All scraped content is encrypted at rest using Fernet symmetric encryption |
| **Honeypot Profiles** | Create and manage decoy social media profiles (admin only) |
| **Chain of Custody** | Blockchain-style evidence logging with SHA-256 hash verification |
| **JWT Authentication** | Secure token-based auth with bcrypt password hashing |
| **Role-Based Access** | Admin and user roles with route-level enforcement |
| **Rate Limiting** | Per-endpoint rate limits to prevent abuse |
| **Security Headers** | CSP, HSTS, X-Frame-Options, and more on every response |
| **Input Validation** | Marshmallow schemas for all API inputs |
| **Background Tasks** | Celery + Redis for periodic ML filtering and bulk scraping |
| **Monitoring** | Sentry error tracking, Grafana dashboards, Logstash pipeline |

---

## Security Features

ANMS v3 implements comprehensive security hardening:

| Feature | Implementation |
|---|---|
| **Authentication** | JWT tokens (PyJWT) with session cookie fallback |
| **Password Hashing** | bcrypt with automatic salt generation |
| **Rate Limiting** | Flask-Limiter: 200/hour global, 5/min login, 3/min register |
| **CSRF Protection** | Flask-WTF CSRFProtect (API routes exempted — they use JWT) |
| **Security Headers** | CSP, X-Frame-Options: DENY, HSTS, X-Content-Type-Options: nosniff |
| **XSS Prevention** | `textContent` DOM API (no `innerHTML` with user data), bleach sanitization |
| **Input Validation** | Marshmallow schemas on all endpoints |
| **CORS Restriction** | Configurable origins (no wildcard `*`) |
| **Error Handling** | Centralized handlers that never leak stack traces or internal details |
| **Audit Logging** | All critical actions logged to database `logs` table |
| **Encryption** | Fernet encryption for all scraped data at rest |
| **Session Security** | HttpOnly, SameSite=Lax, Secure (in production) cookies |
| **No Hardcoded Secrets** | All credentials loaded from environment variables |
| **Honeypot Passwords** | bcrypt-hashed, never returned in API responses |

---

## Architecture Overview

```
┌──────────────┐     ┌──────────────────────────┐     ┌──────────────────┐
│   Frontend   │────▶│  Flask API (main.py)     │────▶│  MySQL Database  │
│  (Bootstrap) │     │                          │     └──────────────────┘
└──────────────┘     │  Security Middleware:     │
                     │  ├─ JWT Auth (auth.py)    │     ┌──────────────────┐
                     │  ├─ Rate Limiter          │────▶│  Redis + Celery  │
                     │  ├─ CSRF Protection       │     └──────────────────┘
                     │  ├─ Security Headers      │
                     │  └─ Input Validation      │     ┌──────────────────┐
                     │                          │────▶│  RoBERTa Model   │
                     │  Blueprints:             │     └──────────────────┘
                     │  ├─ /keywords (auth)     │
                     │  ├─ /scraping (admin)    │
                     │  ├─ /api (admin)         │
                     │  └─ /api/auth (public)   │
                     └──────────────────────────┘
```

---

## Project Structure

```
ANMS_Project_v3/
├── main.py                        # Flask entry point (all security wired here)
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variable template
├── LICENSE                        # Apache 2.0 License
│
├── api/                           # API layer
│   ├── alerts/                    # Alert management & notifications
│   ├── blockchain/                # Chain of custody & evidence storage
│   ├── honeypot/                  # Honeypot profile CRUD (admin-only)
│   │   └── honeypot_profile_setup.py  # bcrypt password hashing, validation
│   ├── keyword_management/        # Keyword CRUD controller & service
│   │   └── keyword_controller.py  # @login_required, marshmallow validation
│   └── scraping/                  # Scraper manager + platform scrapers
│       ├── scraping_controller.py # POST-only, @admin_required, thread-safe
│       ├── scraper_manager.py     # Orchestrates async scraping
│       ├── google_scraper.py      # Google Custom Search API
│       ├── instagram_api_scraper.py # Instagram Graph API (official)
│       ├── telegram_scraper.py    # Telegram scraper
│       └── whatsapp_api_scraper.py # WhatsApp API (key in auth header)
│
├── backend/                       # Backend services & models
│   ├── auth.py                    # JWT authentication & authorization (NEW)
│   ├── security.py                # Security middleware & headers (NEW)
│   ├── validators.py              # Marshmallow input schemas (NEW)
│   ├── app.py                     # Celery worker configuration
│   ├── celery_config.py           # Celery beat schedule
│   ├── models/                    # SQLAlchemy ORM models
│   │   ├── keyword.py
│   │   ├── raw_data.py
│   │   └── user.py                # Timezone-aware, to_dict() method
│   └── services/                  # Business logic
│       ├── behavior_analysis.py
│       ├── data_analysis.py
│       ├── data_cleaner.py
│       ├── dummy_data.py
│       └── triangulation.py
│
├── config/                        # Configuration
│   ├── config.py                  # AppConfig (DEBUG=False by default)
│   ├── db_config.py               # SQLAlchemy URI (no hardcoded creds)
│   ├── blockchain_config.py
│   └── logging_config.py
│
├── database/                      # Database layer
│   ├── db_connection.py           # Engine with pool_pre_ping, context manager
│   ├── db_queries.py              # Query helpers
│   ├── elasticsearch_config.py
│   └── schema.sql                 # MySQL schema
│
├── frontend/                      # Web UI
│   ├── static/css/, js/
│   └── templates/
│       ├── login.html             # Login page (NEW)
│       ├── register.html          # Registration page (NEW)
│       ├── index.html             # Home (auth-aware navbar)
│       ├── dashboard.html         # Scraping dashboard (XSS-safe)
│       ├── honeypots.html         # Honeypot management (admin-only)
│       ├── keywords.html          # Keyword management (XSS-safe)
│       └── reports.html           # Reports
│
├── machine_learning/              # ML pipeline
│   ├── roberta_finetune.py
│   ├── filter_data.py
│   ├── inference.py
│   ├── text_classification.py
│   ├── saved_model/
│   └── training/dataset/
│
├── monitoring/
│   ├── grafana_dashboard.py
│   ├── logstash_pipeline.py
│   └── sentry_integration.py
│
└── utils/
    ├── encryption_utils.py        # Fernet encrypt/decrypt (with failure logging)
    ├── api_utils.py
    ├── alert_utils.py
    ├── key_genrator.py
    └── keyword_utils.py
```

---

## Prerequisites

- **Python** 3.9+
- **MySQL** 8.0+
- **Redis** (for Celery task queue)
- **Git**

Optional:
- **Elasticsearch** (for advanced search indexing)
- **CUDA-capable GPU** (for faster ML training/inference)

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/ANMS_Project_v3.git
cd ANMS_Project_v3
```

### 2. Create a Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

> **Note:** `torch` download may be large (~2 GB). For GPU support, install PyTorch separately via [pytorch.org](https://pytorch.org/get-started/locally/).

---

## Configuration

### 1. Create the `.env` File

```bash
cp .env.example .env
```

### 2. Fill in Required Values

```env
# Database
MYSQL_USER=root
MYSQL_PASSWORD=your_secure_password
MYSQL_HOST=localhost
MYSQL_DB=ncb_projectv3

# CRITICAL: Generate a strong secret key
# python -c "import os; print(os.urandom(32).hex())"
SECRET_KEY=your_64_char_hex_key_here

# Security
FLASK_DEBUG=False
JWT_EXPIRATION_HOURS=8
CORS_ORIGINS=http://localhost:5000

# Encryption (generate with: python utils/key_genrator.py)
ENCRYPTION_KEY=your_fernet_key_here

# API Keys (add the ones you have)
GOOGLE_API_KEY=...
INSTAGRAM_ACCESS_TOKEN=...
WHATSAPP_API_KEY=...
TELEGRAM_BOT_TOKEN=...
```

### 3. Generate an Encryption Key

```bash
python utils/key_genrator.py
```

---

## Database Setup

### 1. Create the MySQL Database and Tables

```bash
mysql -u root -p < database/schema.sql
```

This creates the `ncb_projectv3` database with all required tables:
- `users`, `keywords`, `raw_data`, `clean_data`
- `honeypots`, `platforms`, `monitored_channels`
- `logs`, `alerts`, `reports`, `suspicious_activity`

### 2. (Optional) Insert Dummy Data

```bash
python -m backend.services.dummy_data
```

---

## Running the Application

### Start the Flask Server

```bash
python main.py
```

Available at **http://localhost:5000**

### Start Celery Worker (background tasks)

```bash
celery -A backend.celery_config worker --loglevel=info
celery -A backend.celery_config beat --loglevel=info
```

### Start Redis

```bash
redis-server
```

---

## Authentication & Authorization

### Login Flow

1. Navigate to `/login` — Enter username and password
2. Server validates credentials with bcrypt and returns JWT token
3. Token is stored in `localStorage` and sent as `Authorization: Bearer <token>` header
4. Session cookie is also set as fallback for browser navigation

### Registration

1. Navigate to `/register` — Enter username, password (min 8 chars), email
2. Server validates input, hashes password with bcrypt, creates user with "user" role
3. Returns JWT token immediately (auto-login)

### Role-Based Access

| Role | Access |
|---|---|
| `user` | Dashboard, Keywords, Reports |
| `admin` | All user access + Honeypots, Start Scraping |

### Creating an Admin User

Use the MySQL console or a script:

```sql
-- First register through the UI, then promote:
UPDATE users SET role = 'admin' WHERE username = 'your_username';
```

---

## API Endpoints

All API endpoints require JWT authentication unless noted.

### Authentication (Public)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/login` | Login page |
| `GET` | `/register` | Registration page |
| `POST` | `/api/auth/login` | Authenticate, returns JWT |
| `POST` | `/api/auth/register` | Register new user |
| `POST` | `/api/auth/logout` | Clear session |
| `GET` | `/api/auth/me` | Get current user info |

### Keywords (Requires login)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/keywords/get_keywords` | Fetch all keywords |
| `POST` | `/keywords/add_keyword` | Add keyword (validated) |
| `PUT` | `/keywords/update_keyword/<id>` | Update keyword |
| `DELETE` | `/keywords/delete_keyword/<id>` | Delete keyword |

### Scraping (Admin only)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/scraping/start_scraping` | Start scraping (thread-safe) |
| `GET` | `/scraping/scraping_status` | Check if scraping is active |
| `GET` | `/scraping/stored_data?page=1&per_page=50` | Paginated stored data |

### Honeypots (Admin only)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/view_honeypot_profiles` | List profiles (no passwords) |
| `POST` | `/api/create_honeypot_profile` | Create profile (password hashed) |
| `PUT` | `/api/update_honeypot_profile` | Update profile |
| `DELETE` | `/api/delete_honeypot_profile` | Delete profile |

### Health Check (Public)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check (rate limited: 10/min) |

### Example — Authenticated API Call

```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"securepass"}' | jq -r '.token')

# Use token for subsequent requests
curl http://localhost:5000/keywords/get_keywords \
  -H "Authorization: Bearer $TOKEN"
```

---

## Machine Learning Pipeline

### 1. Fine-Tune RoBERTa

```bash
python -m machine_learning.roberta_finetune
```

### 2. Run Inference

```bash
python -m machine_learning.filter_data
```

### 3. Extract Clean Data

```bash
python -m backend.services.data_cleaner
```

---

## Monitoring & Logging

- **Sentry**: Set `SENTRY_DSN` in `.env` for automatic error tracking
- **Logging**: All logs include timestamps, levels, and module names
- **Audit Trail**: Critical actions logged to database `logs` table
- **Request Logging**: All requests/responses logged with timing

---

## Security Checklist

Before deploying to production:

- [ ] Set a strong `SECRET_KEY` in `.env` (64+ hex chars)
- [ ] Set `FLASK_DEBUG=False`
- [ ] Set `SESSION_COOKIE_SECURE=True` (requires HTTPS)
- [ ] Configure `CORS_ORIGINS` to your actual domain
- [ ] Use HTTPS (reverse proxy with nginx/caddy)
- [ ] Set up proper database credentials (not root)
- [ ] Review rate limit settings for your traffic
- [ ] Enable Sentry for error monitoring
- [ ] Ensure `.env` is in `.gitignore`
- [ ] Run `pip audit` to check for known vulnerabilities

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Flask 3.1, SQLAlchemy 2.0, Celery 5.4 |
| **Authentication** | PyJWT 2.9, bcrypt 4.2 |
| **Security** | Flask-Limiter, Flask-WTF, Flask-Talisman, bleach |
| **Validation** | Marshmallow 3.23 |
| **Database** | MySQL 8.0, Elasticsearch 8.x (optional) |
| **Frontend** | Bootstrap 4.5, Jinja2, jQuery |
| **ML/NLP** | PyTorch 2.1, HuggingFace Transformers (RoBERTa) |
| **Encryption** | cryptography (Fernet) |
| **Task Queue** | Celery + Redis |
| **Monitoring** | Sentry, Grafana, Logstash |

---

## License

This project is licensed under the **Apache License 2.0**. See [LICENSE](LICENSE) for details.