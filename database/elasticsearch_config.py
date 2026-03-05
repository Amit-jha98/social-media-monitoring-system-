# database/elasticsearch_config.py
import os
import logging

logger = logging.getLogger(__name__)

# Elasticsearch configuration
ELASTICSEARCH_HOST = os.getenv("ELASTICSEARCH_HOST", "localhost")
ELASTICSEARCH_PORT = int(os.getenv("ELASTICSEARCH_PORT", "9200"))
ELASTICSEARCH_INDEX = os.getenv("ELASTICSEARCH_INDEX", "anms_data")


def get_elasticsearch_client():
    """Create and return an Elasticsearch client."""
    try:
        from elasticsearch import Elasticsearch
        es = Elasticsearch(
            hosts=[{"host": ELASTICSEARCH_HOST, "port": ELASTICSEARCH_PORT}]
        )
        if es.ping():
            logger.info("Connected to Elasticsearch at %s:%s", ELASTICSEARCH_HOST, ELASTICSEARCH_PORT)
            return es
        else:
            logger.warning("Elasticsearch is not reachable at %s:%s", ELASTICSEARCH_HOST, ELASTICSEARCH_PORT)
            return None
    except ImportError:
        logger.warning("elasticsearch package not installed. Elasticsearch integration disabled.")
        return None
    except Exception as e:
        logger.error("Failed to connect to Elasticsearch: %s", str(e))
        return None
