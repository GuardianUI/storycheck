# File: verifiers/ens_registration.py
from web3 import Web3
from loguru import logger
import json
from pathlib import Path

# ETHRegistrarController address (mainnet)
CONTROLLER_ADDRESS = '0x253553366Da8546fC250F225fe3d25d0C782303b'

# ABI snippet for commitments(bytes32)
CONTROLLER_ABI = [
    {
        'constant': True,
        'inputs': [{'name': 'commitment', 'type': 'bytes32'}],
        'name': 'commitments',
        'outputs': [{'name': '', 'type': 'uint256'}],
        'type': 'function'
    }
]

def verify(results_dir):
    # Load transaction snapshot from results directory (generated during story run)
    tx_snapshot_path = Path(results_dir) / 'tx_log_snapshot.json'
    with open(tx_snapshot_path, 'r') as f:
        tx_snapshot = json.load(f)
    # Check if snapshot has any transactions; expect at least one for ENS commit
    if not tx_snapshot:
        return {'passed': False, 'error': "No transactions found in tx_log_snapshot.json - expected at least one for ENS commitment"}
    # Assume last tx is the commitment; extract details
    tx_data = tx_snapshot[-1]
    tx_hash = tx_data.get('writeTxResult')
    if not tx_hash:
        return {'passed': False, 'error': "No transaction hash found in last snapshot entry - expected a valid hash"}
    
    params = tx_data['writeTx']['params'][0]
    user_address = params.get('from')
    if not user_address:
        return {'passed': False, 'error': "No 'from' address found in tx params - expected mock wallet address"}
    
    # Verify tx sent to correct ENS controller contract
    if params.get('to').lower() != CONTROLLER_ADDRESS.lower():
        return {'passed': False, 'error': f"Transaction not sent to ENS controller address - expected {CONTROLLER_ADDRESS}, got {params.get('to')}"}
    
    # Extract calldata and check for commit method signature
    data = params.get('data', '')
    if not data.startswith('0xf14fcbc8'):
        return {'passed': False, 'error': f"Transaction calldata does not start with commit method signature - expected '0xf14fcbc8', got '{data[:10]}' in tx {tx_hash} (full data: {data})"}
    commitment = '0x' + data[10:74]  # bytes32 after selector (64 hex chars)
    
    # Connect to local anvil fork for onchain queries
    w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
    if not w3.is_connected():
        return {'passed': False, 'error': "Failed to connect to anvil RPC"}
    
    # Confirm transaction mined successfully
    receipt = w3.eth.get_transaction_receipt(tx_hash)
    if receipt['status'] != 1:
        return {'passed': False, 'error': f"Transaction {tx_hash} did not succeed - status {receipt['status']} (expected 1), receipt details: {receipt}"}
    logger.info(f"Tx {tx_hash} succeeded.")
    
    # Query commitment timestamp from controller
    controller = w3.eth.contract(address=CONTROLLER_ADDRESS, abi=CONTROLLER_ABI)
    commit_ts = controller.functions.commitments(commitment).call()
    if commit_ts == 0:
        return {'passed': False, 'error': f"Commitment {commitment} not set in controller - expected timestamp > 0, got 0 for tx {tx_hash}"}
    
    # Verify timestamp matches tx block (commit sets to block.timestamp)
    tx_block = receipt['blockNumber']
    block_ts = w3.eth.get_block(tx_block)['timestamp']
    if commit_ts != block_ts:
        return {'passed': False, 'error': f"Commitment timestamp mismatch for {commitment} in tx {tx_hash} - expected {block_ts} (from block {tx_block}), got {commit_ts}"}
    logger.info(f"Commitment set at {commit_ts} for {commitment}")
    
    return {'passed': True, 'error': None}