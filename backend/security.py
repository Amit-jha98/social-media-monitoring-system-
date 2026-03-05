# backend/security.py
"""Security middleware: rate limiting, security headers, input sanitization, audit logging."""
import os
import re
import logging
import bleach
from datetime import datetime, timezone
from functools import wraps

from flask import request, jsonify, g

from database.db_connection import Session

logger = logging.getLogger(__name__)

# ─── Input Sanitization ──────────────────────────────────────────────────────

# Allowed HTML tags for content display (strip everything dangerous)
ALLOWED_TAGS = ["b", "i", "em", "strong", "a", "br", "p", "ul", "li"]
ALLOWED_ATTRS = {"a": ["href", "title"]}
KEYWORD_PATTERN = re.compile(r'^[\w\s\-#@.,]+$', re.UNICODE)
MAX_KEYWORD_LENGTH = 255


def sanitize_html(text: str) -> str:
    """Remove dangerous HTML tags/attributes from text."""
    if not text:
        return ""
    return bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)


def sanitize_keyword(keyword: str) -> tuple:
    """Validate and sanitize a keyword input. Returns (clean_keyword, error_message)."""
    if not keyword or not keyword.strip():
        return None, "Keyword cannot be empty"

    keyword = keyword.strip()

    if len(keyword) > MAX_KEYWORD_LENGTH:
        return None, f"Keyword must be {MAX_KEYWORD_LENGTH} characters or less"

    if not KEYWORD_PATTERN.match(keyword):
        return None, "Keyword contains invalid characters. Only letters, numbers, spaces, #, @, -, . and , are allowed"

    return keyword, None


def sanitize_string(text: str, max_length: int = 500) -> str:
    """Basic string sanitization: strip, truncate, remove null bytes."""
    if not text:
        return ""
    text = text.strip().replace("\x00", "")
    return text[:max_length]


# ─── Audit Logging ───────────────────────────────────────────────────────────

def log_audit_event(user_id: int, action: str, details: str = None):
    """Log an audit event to the database logs table."""
    try:
        from sqlalchemy import text
        db_session = Session()
        try:
            db_session.execute(
                text("INSERT INTO logs (user_id, action, details) VALUES (:uid, :action, :details)"),
                {"uid": user_id, "action": action, "details": details or ""}
            )
            db_session.commit()
        finally:
            db_session.close()
    except Exception as e:
        logger.error("Failed to log audit event: %s", e)


# ─── Security Headers (Applied via @app.after_request) ────────────────────────

def apply_security_headers(response):
    """Add security headers to every response."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://code.jquery.com https://cdn.jsdelivr.net https://maxcdn.bootstrapcdn.com; "
        "style-src 'self' 'unsafe-inline' https://maxcdn.bootstrapcdn.com https://cdn.jsdelivr.net; "
        "img-src 'self' data: https:; "
        "font-src 'self' https://maxcdn.bootstrapcdn.com https://cdn.jsdelivr.net; "
        "connect-src 'self'"
    )
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# ─── Request Logging ──────────────────────────────────────────────────────────

def log_request():
    """Log incoming request details (called via @app.before_request)."""
    g.request_start_time = datetime.now(timezone.utc)
    # Don't log static file requests
    if not request.path.startswith("/static"):
        logger.info(
            "Request: %s %s from %s",
            request.method,
            request.path,
            request.remote_addr,
        )


def log_response(response):
    """Log response time and status."""
    if hasattr(g, "request_start_time") and not request.path.startswith("/static"):
        elapsed = (datetime.now(timezone.utc) - g.request_start_time).total_seconds()
        logger.info(
            "Response: %s %s -> %s (%.3fs)",
            request.method,
            request.path,
            response.status_code,
            elapsed,
        )
    return response


# ─── Error Handlers ───────────────────────────────────────────────────────────

def register_error_handlers(app):
    """Register centralized error handlers that don't leak internal details."""

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Bad request"}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({"error": "Authentication required"}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({"error": "Access denied"}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429

    @app.errorhandler(500)
    def internal_error(e):
        logger.exception("Internal server error")
        return jsonify({"error": "An internal error occurred"}), 500
