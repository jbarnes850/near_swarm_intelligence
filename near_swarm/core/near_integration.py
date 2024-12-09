"""
NEAR Protocol Integration Module
Handles core NEAR blockchain interactions
"""

import json
import logging
from typing import Optional, Dict, Any

import requests
from near_api.providers import JsonProvider
from near_api.signer import Signer, KeyPair
from near_api.account import Account

logger = logging.getLogger(__name__)


class NEARConnectionError(Exception):
    """Custom exception for NEAR connection errors."""
    pass


class NEARConnection:
    """Handles NEAR Protocol connection and interactions."""

    def __init__(
        self,
        network: str,
        account_id: str,
        private_key: str,
        node_url: Optional[str] = None
    ):
        """Initialize NEAR connection."""
        try:
            self.network = network
            self.account_id = account_id

            # Initialize provider based on network or custom node URL
            if node_url:
                logger.info(f"Using custom RPC endpoint: {node_url}")
                self.node_url = node_url
            elif network == "mainnet":
                self.node_url = "https://rpc.mainnet.near.org"
            else:
                self.node_url = "https://rpc.testnet.near.org"

            # Test connection with a status check
            try:
                status_request = {
                    "jsonrpc": "2.0",
                    "id": "dontcare",
                    "method": "status",
                    "params": []
                }
                response = requests.post(self.node_url, json=status_request)
                response.raise_for_status()
                logger.info("RPC connection test successful")
            except Exception as e:
                logger.error(f"RPC connection test failed: {str(e)}")
                raise

            # Initialize provider
            self.provider = JsonProvider(self.node_url)

            # Initialize key pair and signer
            if private_key.startswith("ed25519:"):
                private_key = private_key[8:]  # Remove ed25519: prefix
            key_pair = KeyPair(private_key)  # Use constructor directly
            self.signer = Signer(account_id, key_pair)

            # Initialize account with proper parameters
            account_request = {
                "jsonrpc": "2.0",
                "id": "dontcare",
                "method": "query",
                "params": {
                    "request_type": "view_account",
                    "finality": "final",
                    "account_id": account_id
                }
            }

            try:
                response = requests.post(self.node_url, json=account_request)
                response.raise_for_status()
                account_data = response.json()
                logger.info(f"Account data retrieved: {json.dumps(account_data, indent=2)}")
            except Exception as e:
                logger.error(f"Failed to retrieve account data: {str(e)}")
                raise

            self.account = Account(
                self.provider,
                self.signer,
                self.account_id
            )
            logger.info(f"Successfully initialized NEAR connection for {account_id}")

        except Exception as e:
            logger.error(f"Failed to initialize NEAR connection: {str(e)}")
            raise NEARConnectionError(f"NEAR connection failed: {str(e)}")

    async def check_account(self, account_id: str) -> bool:
        """Check if an account exists."""
        try:
            account_data = self.provider.get_account(account_id)
            return bool(account_data)
        except Exception:
            return False

    async def get_account_balance(self) -> Dict[str, Any]:
        """Get account balance."""
        try:
            account_data = self.provider.get_account(self.account_id)
            return {
                "total": account_data["amount"],
                "staked": account_data["locked"],
                "available": str(int(account_data["amount"]) - int(account_data["locked"]))
            }
        except Exception as e:
            logger.error(f"Failed to get account balance: {str(e)}")
            raise

    async def send_transaction(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Send a transaction to the NEAR network."""
        try:
            # Validate transaction
            if not transaction.get("receiver_id"):
                raise ValueError("Missing receiver_id in transaction")
            if not transaction.get("actions"):
                raise ValueError("Missing actions in transaction")

            # Send transaction
            result = await self.account.sign_and_send_transaction(
                transaction["receiver_id"],
                transaction["actions"]
            )
            return result
        except Exception as e:
            logger.error(f"Failed to send transaction: {str(e)}")
            raise