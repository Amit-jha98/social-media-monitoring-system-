# api/blockchain/evidence_storage.py
import hashlib
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class EvidenceStorage:
    """Stores and retrieves digital evidence with hash verification."""

    def __init__(self):
        self.evidence_store = {}

    def store_evidence(self, evidence_id, content, source, collected_by):
        """Store a piece of evidence with its hash."""
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        evidence = {
            'id': evidence_id,
            'content_hash': content_hash,
            'source': source,
            'collected_by': collected_by,
            'stored_at': datetime.now(timezone.utc).isoformat(),
        }
        self.evidence_store[evidence_id] = evidence
        logger.info("Evidence %s stored successfully.", evidence_id)
        return evidence

    def verify_evidence(self, evidence_id, content):
        """Verify that evidence content has not been tampered with."""
        evidence = self.evidence_store.get(evidence_id)
        if not evidence:
            return {'status': 'error', 'message': 'Evidence not found'}
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        is_valid = content_hash == evidence['content_hash']
        return {'status': 'success', 'is_valid': is_valid}

    def get_evidence(self, evidence_id):
        """Retrieve evidence metadata."""
        return self.evidence_store.get(evidence_id)
