import json
import logging
from web3 import Web3

def verify(output_dir: str) -> bool:
    """Verify transaction succeeded with 0.01 ETH sent to vitalik.eth (0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045)."""
    logging.basicConfig(level=logging.INFO, filename=f"{output_dir}/storycheck.log", filemode="a")
    logger = logging.getLogger(__name__)

    try:
        with open(f"{output_dir}/tx_snapshot.json", "r") as f:
            txs = json.load(f)

        if not txs:
            logger.error("No transactions found in tx_snapshot.json")
            return False

        tx = txs[-1]  # Check the last transaction
        expected_to = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        expected_value = 10000000000000000  # 0.01 ETH in wei

        if not Web3.is_address(tx.get("to")) or tx.get("to").lower() != expected_to.lower():
            logger.error(f"Invalid recipient: got {tx.get('to')}, expected {expected_to}")
            return False
        if tx.get("value") != expected_value:
            logger.error(f"Invalid value: got {tx.get('value')}, expected {expected_value}")
            return False
        logger.info("Transaction verification passed: correct recipient and value")
        return True
    except Exception as e:
        logger.error(f"Verification failed: {str(e)}")
        return False