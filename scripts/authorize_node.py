#!/usr/bin/env python3
"""Authorize a Chainlink node wallet on the Oracle contract."""

import os
import sys

from web3 import Web3

# Oracle contract (Chainlink Operator)
ORACLE_ADDRESS = "0xc3e350a4Bc67c8e20e031121fF8fCc680809A9a3"
NODE_WALLET = "0x4CdFeF07E957C6268C41E178E29a3aC85ED17f20"

# Minimal ABI for setAuthorizedSenders
ORACLE_ABI = [
    {
        "inputs": [{"name": "_senders", "type": "address[]"}],
        "name": "setAuthorizedSenders",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]

RPC_URL = os.environ.get(
    "RPC_URL", "https://sepolia.infura.io/v3/6cd4a2c5b42f4422a1e0ad5de0ef0722"
)
PRIVATE_KEY = os.environ.get("PRIVATE_KEY")

if not PRIVATE_KEY:
    print("Set PRIVATE_KEY env var to the oracle owner's private key")
    print("Usage: PRIVATE_KEY=0x... python scripts/authorize_node.py")
    sys.exit(1)

w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)
oracle = w3.eth.contract(address=ORACLE_ADDRESS, abi=ORACLE_ABI)

print(f"Oracle contract: {ORACLE_ADDRESS}")
print(f"Authorizing node wallet: {NODE_WALLET}")
print(f"Signing with: {account.address}")

tx = oracle.functions.setAuthorizedSenders([NODE_WALLET]).build_transaction(
    {
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": 100000,
        "maxFeePerGas": w3.eth.gas_price * 2,
        "maxPriorityFeePerGas": w3.to_wei(1, "gwei"),
    }
)

signed = account.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
print(f"TX sent: {tx_hash.hex()}")

receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print(f"Status: {'success' if receipt.status == 1 else 'FAILED'}")
print(f"Block: {receipt.blockNumber}")
