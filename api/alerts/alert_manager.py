# api/alerts/alert_manager.py
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class AlertManager:
    """Manages alert creation, retrieval, and resolution."""

    def __init__(self):
        self.alerts = []

    def create_alert(self, alert_type, description, related_user=None, channel_id=None, platform_id=None):
        """Create a new alert."""
        alert = {
            'id': len(self.alerts) + 1,
            'alert_type': alert_type,
            'description': description,
            'related_user': related_user,
            'channel_id': channel_id,
            'platform_id': platform_id,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'is_resolved': False,
            'resolved_at': None
        }
        self.alerts.append(alert)
        logger.info("Alert created: %s", alert_type)
        return {'status': 'success', 'alert': alert}

    def get_alerts(self, resolved=None):
        """Get alerts, optionally filtered by resolution status."""
        if resolved is not None:
            return [a for a in self.alerts if a['is_resolved'] == resolved]
        return self.alerts

    def resolve_alert(self, alert_id):
        """Mark an alert as resolved."""
        for alert in self.alerts:
            if alert['id'] == alert_id:
                alert['is_resolved'] = True
                alert['resolved_at'] = datetime.now(timezone.utc).isoformat()
                logger.info("Alert %d resolved.", alert_id)
                return {'status': 'success', 'message': f'Alert {alert_id} resolved'}
        return {'status': 'error', 'message': f'Alert {alert_id} not found'}
