"""
ANMS - Advanced Narcotics Monitoring System
Main application entry point with comprehensive security.
"""
import os
import logging
from datetime import timedelta

from flask import Flask, render_template, session
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

load_dotenv()

from config.config import AppConfig
from backend.auth import auth_blueprint, login_required, admin_required
from backend.security import (
    apply_security_headers,
    log_request,
    log_response,
    register_error_handlers,
)
from api.keyword_management.keyword_controller import keyword_blueprint
from api.scraping.scraping_controller import scraping_blueprint
from api.honeypot.honeypot_profile_setup import honeypot_blueprint

# ─── Logging ──────────────────────────────────────────────────────────────────

log_level = logging.DEBUG if AppConfig.DEBUG else logging.INFO
logging.basicConfig(
    level=log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ─── Flask App ────────────────────────────────────────────────────────────────

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "templates"),
    static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "static"),
)
app.config.from_object(AppConfig)

# Session cookie security
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)
if not AppConfig.DEBUG:
    app.config["SESSION_COOKIE_SECURE"] = True

# ─── Rate Limiting ────────────────────────────────────────────────────────────

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per hour", "50 per minute"],
    storage_uri="memory://",
)

# ─── CSRF Protection ─────────────────────────────────────────────────────────

csrf = CSRFProtect(app)
# Exempt API blueprints (they use JWT auth instead)
csrf.exempt(keyword_blueprint)
csrf.exempt(scraping_blueprint)
csrf.exempt(honeypot_blueprint)
csrf.exempt(auth_blueprint)

# ─── CORS ─────────────────────────────────────────────────────────────────────

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5000").split(",")
CORS(app, origins=cors_origins, supports_credentials=True)

# ─── Security Middleware ──────────────────────────────────────────────────────

app.before_request(log_request)
app.after_request(apply_security_headers)
app.after_request(log_response)
register_error_handlers(app)

# ─── Register Blueprints ─────────────────────────────────────────────────────

app.register_blueprint(auth_blueprint)
app.register_blueprint(keyword_blueprint, url_prefix="/keywords")
app.register_blueprint(scraping_blueprint, url_prefix="/scraping")
app.register_blueprint(honeypot_blueprint, url_prefix="/api")


# ─── Page Routes (Protected) ─────────────────────────────────────────────────

@app.route("/", methods=["GET"])
@login_required
def index():
    return render_template("index.html")


@app.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    return render_template("dashboard.html")


@app.route("/honeypots", methods=["GET"])
@admin_required
def honeypots():
    return render_template("honeypots.html")


@app.route("/keywords", methods=["GET"])
@login_required
def keywords():
    return render_template("keywords.html")


@app.route("/reports", methods=["GET"])
@login_required
def reports():
    return render_template("reports.html")


# ─── Health Check (Public) ────────────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
@limiter.limit("10 per minute")
def health_check():
    return {"status": "healthy", "version": "3.0"}, 200


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    debug_mode = AppConfig.DEBUG
    if debug_mode:
        logger.warning("Running in DEBUG mode. DO NOT use in production!")
    else:
        logger.info("Starting ANMS in production mode.")

    logger.info("ANMS v3.0 starting on http://localhost:5000")
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=debug_mode,
    )

