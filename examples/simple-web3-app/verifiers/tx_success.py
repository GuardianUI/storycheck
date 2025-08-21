# examples/simple-web3-app/verifiers/tx_success.py

import json
import logging
from web3 import Web3

def verify(output_dir: str) -> bool:
    """Verify the transaction success based on tx_snapshot.json."""
    tx_snapshot_path = f"{output_dir}/tx_snapshot.json"
    try:
        with open(tx_snapshot_path, "r") as f:
            tx_snapshot = json.load(f)
        if not tx_snapshot:
            logging.error("No transactions found in tx_snapshot.json")
            return False
        # Assuming the last transaction is the one we care about
        last_tx = tx_snapshot[-1]
        tx_hash = last_tx.get("writeTxResult")
        if not tx_hash:
            logging.error("No transaction hash found")
            return False
        # Connect to the local anvil RPC
        w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        if receipt is None:
            logging.error("Transaction receipt not found")
            return False
        if receipt.status != 1:
            logging.error(f"Transaction failed with status {receipt.status}")
            return False
        # Additional checks
        tx = w3.eth.get_transaction(tx_hash)
        # Check recipient
        expected_recipient = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045".lower()
        recipient = tx["to"].lower() if tx["to"] else None
        if recipient != expected_recipient:
            logging.error(f"Invalid recipient: got {recipient}, expected {expected_recipient}")
            return False
        # Check value
        expected_value = Web3.to_wei(0.01, "ether")
        if tx["value"] != expected_value:
            logging.error(f"Invalid value: got {tx['value']}, expected {expected_value}")
            return False
        logging.info("Transaction verified successfully")
        return True
    except Exception as e:
        logging.error(f"Verification failed: {str(e)}")
        return False