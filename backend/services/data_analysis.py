# backend/services/data_analysis.py
import logging
from collections import Counter

logger = logging.getLogger(__name__)


class DataAnalysis:
    """Provides analytical insights on scraped and processed data."""

    @staticmethod
    def get_platform_distribution(records):
        """Get distribution of records across platforms."""
        platforms = [r.get('platform', 'unknown') for r in records]
        return dict(Counter(platforms))

    @staticmethod
    def get_keyword_frequency(records):
        """Get frequency of keywords in records."""
        keywords = [r.get('keyword', '') for r in records]
        return dict(Counter(keywords))

    @staticmethod
    def get_timeline_data(records):
        """Group records by date for timeline visualization."""
        timeline = {}
        for record in records:
            date = str(record.get('timestamp', ''))[:10]
            timeline[date] = timeline.get(date, 0) + 1
        return dict(sorted(timeline.items()))
