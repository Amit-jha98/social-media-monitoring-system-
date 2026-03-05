# api/blockchain/chain_of_custody.py
import hashlib
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ChainOfCustody:
    """Maintains a tamper-evident chain of custody for digital evidence."""

    def __init__(self):
        self.chain = []

    def add_entry(self, evidence_id, action, performed_by, details=None):
        """Add a new entry to the chain of custody."""
        entry = {
            'evidence_id': evidence_id,
            'action': action,
            'performed_by': performed_by,
            'details': details or '',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'previous_hash': self.chain[-1]['hash'] if self.chain else '0' * 64,
        }
        entry['hash'] = self._compute_hash(entry)
        self.chain.append(entry)
        logger.info("Chain of custody entry added for evidence %s", evidence_id)
        return entry

    @staticmethod
    def _compute_hash(entry):
        """Compute SHA-256 hash of an entry."""
        entry_string = json.dumps({k: v for k, v in entry.items() if k != 'hash'}, sort_keys=True)
        return hashlib.sha256(entry_string.encode()).hexdigest()

    def verify_chain(self):
        """Verify the integrity of the chain."""
        for i in range(1, len(self.chain)):
            if self.chain[i]['previous_hash'] != self.chain[i - 1]['hash']:
                logger.error("Chain integrity broken at entry %d", i)
                return False
        logger.info("Chain of custody integrity verified.")
        return True
