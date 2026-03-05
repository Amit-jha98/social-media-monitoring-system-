"""Scraping controller with authentication, thread safety, and pagination."""
import logging
import threading

from flask import Blueprint, jsonify, request
from database.db_queries import get_decrypted_data
from .scraper_manager import ScraperManager
from backend.auth import login_required, admin_required
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
scraping_blueprint = Blueprint('scraping', __name__)

# Thread-safe scraping control
_scraping_lock = threading.Lock()
_scraping_active = False


@scraping_blueprint.route('/start_scraping', methods=['POST'])
@admin_required
def start_scraping():
    """Start scraping (POST only, admin only, thread-safe)."""
    global _scraping_active
    if not _scraping_lock.acquire(blocking=False):
        return jsonify({"error": "Scraping is already in progress"}), 429

    try:
        if _scraping_active:
            _scraping_lock.release()
            return jsonify({"error": "Scraping is already running"}), 429

        _scraping_active = True
        batch_size = min(max(request.json.get("batch_size", 100) if request.is_json else 100, 1), 500)
        scraper_manager = ScraperManager(batch_size=batch_size)

        def _run_scraping():
            global _scraping_active
            try:
                scraper_manager.scrape_all_platforms()
                logger.info("Scraping completed successfully")
            except Exception as e:
                logger.exception("Scraping error")
            finally:
                _scraping_active = False

        thread = threading.Thread(target=_run_scraping, daemon=True)
        thread.start()
        _scraping_lock.release()

        return jsonify({
            "message": "Scraping started. Running in background.",
            "status": "started",
            "batch_size": batch_size,
        }), 200
    except Exception as e:
        _scraping_active = False
        if _scraping_lock.locked():
            _scraping_lock.release()
        logger.exception("Error starting scraping")
        return jsonify({"error": "Failed to start scraping"}), 500


@scraping_blueprint.route('/scraping_status', methods=['GET'])
@login_required
def scraping_status():
    """Check if scraping is currently running."""
    return jsonify({"active": _scraping_active}), 200


@scraping_blueprint.route('/stored_data', methods=['GET'])
@login_required
def get_stored_data():
    """Fetch stored data with pagination."""
    try:
        page = max(int(request.args.get("page", 1)), 1)
        per_page = min(max(int(request.args.get("per_page", 50)), 1), 200)

        data = get_decrypted_data()

        # Paginate in-memory
        total = len(data)
        start = (page - 1) * per_page
        end = start + per_page
        page_data = data[start:end]
        pages = max(1, (total + per_page - 1) // per_page)

        return jsonify({
            "data": page_data,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": pages,
            }
        }), 200
    except Exception as e:
        logger.exception("Error fetching stored data")
        return jsonify({"error": "Failed to fetch data"}), 500
