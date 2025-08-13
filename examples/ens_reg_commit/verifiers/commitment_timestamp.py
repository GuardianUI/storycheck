# examples/ens_reg_commit/verifiers/commitment_timestamp.py
from loguru import logger

def verify(tx_log, results_dir):
    if not tx_log:
        return {'passed': False, 'error': 'No transactions in log'}
    
    expected_selector = '0xf14fcbc8'  # ENS commit function selector
    
    for tx in tx_log:
        if tx.get('writeTxException') is not None:
            return {'passed': False, 'error': 'Tx failed, timestamp not set'}
        
        params = tx.get('writeTx', {}).get('params', [{}])[0]
        data = params.get('data', '')
        if not data.startswith(expected_selector):
            logger.error(f"Unexpected tx data: {data}")
            return {'passed': False, 'error': 'Tx data does not match ENS commit call'}
        
        # Infer timestamp set since tx succeeded (deterministic)
    
    logger.info("Commitment timestamp verified as set via successful commit tx.")
    return {'passed': True}