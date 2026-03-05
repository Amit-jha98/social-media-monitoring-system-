# utils/alert_utils.py
import logging

logger = logging.getLogger(__name__)


def format_alert_message(alert_type, description, platform=None, keyword=None):
    """Format an alert message for display or notification."""
    parts = [f"[{alert_type.upper()}] {description}"]
    if platform:
        parts.append(f"Platform: {platform}")
    if keyword:
        parts.append(f"Keyword: {keyword}")
    return ' | '.join(parts)


def classify_alert_severity(alert_type):
    """Classify the severity of an alert."""
    severity_map = {
        'keyword_match': 'medium',
        'suspicious_activity': 'high',
        'honeypot_interaction': 'critical',
    }
    return severity_map.get(alert_type, 'low')
