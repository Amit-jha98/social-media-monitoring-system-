# config/blockchain_config.py
import os


class BlockchainConfig:
    """Configuration for blockchain-based evidence storage."""
    HASH_ALGORITHM = 'sha256'
    CHAIN_STORAGE_PATH = os.getenv('CHAIN_STORAGE_PATH', 'data/chain_of_custody.json')
    ENABLE_BLOCKCHAIN = os.getenv('ENABLE_BLOCKCHAIN', 'false').lower() == 'true'
