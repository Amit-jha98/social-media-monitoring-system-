# monitoring/sentry_integration.py
import os
import logging

logger = logging.getLogger(__name__)


def init_sentry():
    """Initialize Sentry error tracking."""
    sentry_dsn = os.getenv('SENTRY_DSN')
    if not sentry_dsn:
        logger.warning("SENTRY_DSN not set. Sentry integration disabled.")
        return False

    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=sentry_dsn,
            traces_sample_rate=0.1,
        )
        logger.info("Sentry initialized successfully.")
        return True
    except ImportError:
        logger.warning("sentry-sdk not installed. Sentry integration disabled.")
        return False
    except Exception as e:
        logger.error("Failed to initialize Sentry: %s", str(e))
        return False
