# examples/ens_reg_commit/verifiers/tx_success.py
from loguru import logger

def verify(tx_log, results_dir):
    if not tx_log:
        return {'passed': False, 'error': 'No transactions in log'}
    
    for tx in tx_log:
        if tx.get('writeTxException') is not None:
            logger.error(f"Transaction failed with exception: {tx['writeTxException']}")
            return {'passed': False, 'error': f"Tx failed: {tx['writeTxException']}"}
        
        result = tx.get('writeTxResult')
        if not result or not isinstance(result, str) or not result.startswith('0x') or len(result) != 66:
            logger.error(f"Invalid transaction result: {result}")
            return {'passed': False, 'error': f"Invalid tx result: {result}"}
    
    logger.info("All transactions succeeded with valid results.")
    return {'passed': True}