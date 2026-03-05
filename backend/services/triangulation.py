# backend/services/triangulation.py
import logging

logger = logging.getLogger(__name__)


class Triangulation:
    """Cross-references data across platforms to identify linked accounts or activities."""

    @staticmethod
    def find_cross_platform_matches(records):
        """Find users or content appearing on multiple platforms."""
        user_platforms = {}
        for record in records:
            user = record.get('user_name') or record.get('channel_name')
            platform = record.get('platform')
            if user:
                user_platforms.setdefault(user, set()).add(platform)

        # Users found on multiple platforms
        matches = {user: list(platforms) for user, platforms in user_platforms.items() if len(platforms) > 1}
        logger.info("Found %d cross-platform matches", len(matches))
        return matches

    @staticmethod
    def correlate_by_keyword(records):
        """Group records by keyword to find related activity across platforms."""
        keyword_groups = {}
        for record in records:
            keyword = record.get('keyword', '')
            keyword_groups.setdefault(keyword, []).append({
                'platform': record.get('platform'),
                'user': record.get('user_name') or record.get('channel_name'),
                'timestamp': record.get('timestamp'),
            })
        return keyword_groups
