# Send ETH to User-Entered ENS or Address

This user story tests connecting a wallet, entering an ENS name or address, entering an ETH amount, and sending the transaction.

## Prerequisites

1. Chain
   - Id 1
   - Block 23086523

## User Steps

1. Browse to http://localhost:5173/
1. Click Connect Wallet
1. Click on ENS name or address input
1. Type vitalik.eth
1. Click on ETH amount input
4. Type 0.01
5. Click Send ETH
6. Wait 5 seconds

## Expected Results

- Transaction succeeded with 0.01 ETH sent to vitalik.eth resolving to 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 - [verifier](verifiers/tx_success.py)