# examples/ens_reg_commit/verifiers/tx_success.py
from loguru import logger

def verify(tx_log, results_dir):
    logger.info("[Verifier: tx_success] Starting verification of transaction success.")
    if not tx_log:
        logger.error("[Verifier: tx_success] Verification failed. No transactions in log.")
        return False
    passed = True
    for tx in tx_log:
        if tx.get('writeTxException') is not None:
            logger.error(f"[Verifier: tx_success] Transaction failed: {tx['writeTxException']}")
            passed = False
        if not tx.get('writeTxResult'):
            logger.error(f"[Verifier: tx_success] No transaction result found in: {tx}")
            passed = False
    if passed:
        logger.info(f"[Verifier: tx_success] Verification passed. Transaction log: {tx_log}")
    else:
        logger.error(f"[Verifier: tx_success] Verification failed. Transaction log: {tx_log}")
    return passed