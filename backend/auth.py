# backend/auth.py
"""Authentication and authorization module using JWT tokens."""
import os
import logging
import functools
from datetime import datetime, timezone, timedelta

import jwt
import bcrypt
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template

from database.db_connection import Session
from backend.models.user import User

logger = logging.getLogger(__name__)

auth_blueprint = Blueprint('auth', __name__)

JWT_SECRET = os.environ.get("SECRET_KEY", "change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "8"))


# ─── Password Hashing ────────────────────────────────────────────────────────

def hash_password(plain_password: str) -> str:
    """Hash a password with bcrypt."""
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


# ─── JWT Token Helpers ────────────────────────────────────────────────────────

def create_token(user_id: int, username: str, role: str) -> str:
    """Create a signed JWT token."""
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token. Raises on invalid/expired tokens."""
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


# ─── Decorators ───────────────────────────────────────────────────────────────

def login_required(f):
    """Decorator that requires a valid JWT token in Authorization header or session."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Check Authorization header first
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]

        # Fall back to session cookie for browser-based access
        if not token:
            token = session.get("jwt_token")

        if not token:
            # For API requests, return JSON
            if request.is_json or request.headers.get("Accept") == "application/json":
                return jsonify({"error": "Authentication required"}), 401
            # For browser requests, redirect to login
            return redirect(url_for("auth.login_page"))

        try:
            payload = decode_token(token)
            request.current_user = payload
        except jwt.ExpiredSignatureError:
            logger.warning("Expired token attempt from %s", request.remote_addr)
            return jsonify({"error": "Token expired. Please log in again."}), 401
        except jwt.InvalidTokenError:
            logger.warning("Invalid token attempt from %s", request.remote_addr)
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Decorator that requires admin role."""
    @functools.wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if request.current_user.get("role") != "admin":
            return jsonify({"error": "Admin privileges required"}), 403
        return f(*args, **kwargs)
    return decorated


# ─── Auth Routes ──────────────────────────────────────────────────────────────

@auth_blueprint.route("/login", methods=["GET"])
def login_page():
    """Serve the login page."""
    return render_template("login.html")


@auth_blueprint.route("/register", methods=["GET"])
def register_page():
    """Serve the registration page."""
    return render_template("register.html")


@auth_blueprint.route("/api/auth/register", methods=["POST"])
def register():
    """Register a new user."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    username = (data.get("username") or "").strip()
    password = data.get("password", "")
    email = (data.get("email") or "").strip()

    # Input validation
    if not username or len(username) < 3 or len(username) > 50:
        return jsonify({"error": "Username must be 3-50 characters"}), 400
    if not password or len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400
    if email and ("@" not in email or len(email) > 100):
        return jsonify({"error": "Invalid email address"}), 400

    db_session = Session()
    try:
        # Check for existing user
        existing = db_session.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing:
            return jsonify({"error": "Username or email already exists"}), 409

        new_user = User(
            username=username,
            password_hash=hash_password(password),
            email=email or None,
            role="user",
        )
        db_session.add(new_user)
        db_session.commit()

        logger.info("New user registered: %s", username)
        token = create_token(new_user.id, new_user.username, new_user.role)
        return jsonify({
            "success": True,
            "message": "Registration successful",
            "token": token,
            "user": {"id": new_user.id, "username": new_user.username, "role": new_user.role}
        }), 201
    except Exception as e:
        db_session.rollback()
        logger.exception("Registration error")
        return jsonify({"error": "Registration failed. Please try again."}), 500
    finally:
        db_session.close()


@auth_blueprint.route("/api/auth/login", methods=["POST"])
def login():
    """Authenticate user and return JWT token."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    username = (data.get("username") or "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    db_session = Session()
    try:
        user = db_session.query(User).filter(User.username == username).first()
        if not user or not verify_password(password, user.password_hash):
            logger.warning("Failed login attempt for user: %s from %s", username, request.remote_addr)
            return jsonify({"error": "Invalid username or password"}), 401

        token = create_token(user.id, user.username, user.role)

        # Set session cookie for browser-based access
        session["jwt_token"] = token
        session["user_id"] = user.id
        session["username"] = user.username
        session["role"] = user.role

        logger.info("User logged in: %s", username)
        return jsonify({
            "success": True,
            "token": token,
            "user": {"id": user.id, "username": user.username, "role": user.role}
        }), 200
    except Exception as e:
        logger.exception("Login error")
        return jsonify({"error": "Login failed. Please try again."}), 500
    finally:
        db_session.close()


@auth_blueprint.route("/api/auth/logout", methods=["POST"])
def logout():
    """Clear session and log out."""
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully"}), 200


@auth_blueprint.route("/api/auth/me", methods=["GET"])
@login_required
def get_current_user():
    """Return the currently authenticated user's info."""
    return jsonify({
        "id": request.current_user["sub"],
        "username": request.current_user["username"],
        "role": request.current_user["role"],
    }), 200
