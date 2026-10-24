#!/usr/bin/env python3
"""Authorize a Chainlink node wallet on the Oracle contract."""

import getpass
import os

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

RPC_URL = os.environ.get("RPC_URL") or getpass.getpass("Sepolia RPC URL: ")
PRIVATE_KEY = os.environ.get("PRIVATE_KEY") or getpass.getpass(
    "Oracle owner private key: "
)

w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)
oracle = w3.eth.contract(address=ORACLE_ADDRESS, abi=ORACLE_ABI)

print(f"Oracle contract: {ORACLE_ADDRESS}")
print(f"Authorizing node wallet: {NODE_WALLET}")
print(f"Signing with: {account.address}")

max_priority = w3.to_wei(1, "gwei")
max_fee = max(w3.eth.gas_price * 2, max_priority + w3.to_wei(1, "gwei"))

tx = oracle.functions.setAuthorizedSenders([NODE_WALLET]).build_transaction(
    {
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": 300000,
        "maxFeePerGas": max_fee,
        "maxPriorityFeePerGas": max_priority,
    }
)

signed = account.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
print(f"TX sent: {tx_hash.hex()}")

receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print(f"Status: {'success' if receipt.status == 1 else 'FAILED'}")
print(f"Block: {receipt.blockNumber}")
