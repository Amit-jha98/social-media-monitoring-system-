# backend/services/behavior_analysis.py
import logging

logger = logging.getLogger(__name__)


class BehaviorAnalysis:
    """Analyzes user behavior patterns to detect suspicious activity."""

    @staticmethod
    def analyze_posting_frequency(user_posts):
        """Analyze posting frequency for anomalies."""
        if not user_posts:
            return {'risk_level': 'low', 'message': 'No posts to analyze'}

        # TODO: Implement statistical analysis of posting patterns
        logger.info("Analyzing posting frequency for %d posts", len(user_posts))
        return {'risk_level': 'medium', 'post_count': len(user_posts)}

    @staticmethod
    def analyze_keyword_usage(posts, suspicious_keywords):
        """Check how frequently suspicious keywords appear in posts."""
        matches = 0
        for post in posts:
            content = post.get('content', '').lower()
            for keyword in suspicious_keywords:
                if keyword.lower() in content:
                    matches += 1
                    break

        if matches > len(posts) * 0.5:
            risk_level = 'high'
        elif matches > 0:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        return {'risk_level': risk_level, 'matches': matches, 'total_posts': len(posts)}
