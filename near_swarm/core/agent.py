"""
Core Agent Module
Handles base agent functionality and NEAR integration
"""

import logging
import asyncio
from dataclasses import dataclass
from typing import Optional, Dict, Any

from near_api.providers import JsonProvider
from near_api.signer import Signer
from near_api.account import Account

from near_swarm.core.near_integration import NEARConnection

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Agent configuration."""
    near_network: str
    account_id: str
    private_key: str
    llm_provider: str
    llm_api_key: str
    node_url: Optional[str] = None
    max_retries: int = 5
    retry_delay: float = 2.0

    def __post_init__(self):
        """Validate configuration."""
        if not self.near_network:
            raise ValueError("near_network is required")
        if self.near_network not in ["mainnet", "testnet"]:
            raise ValueError("near_network must be 'mainnet' or 'testnet'")
        if not self.account_id:
            raise ValueError("account_id is required")
        if "@" in self.account_id:
            raise ValueError("Invalid account_id format")
        if not self.private_key:
            raise ValueError("private_key is required")
        if not self.llm_provider:
            raise ValueError("llm_provider is required")
        if not self.llm_api_key:
            raise ValueError("llm_api_key is required")
        if self.max_retries < 1:
            raise ValueError("max_retries must be at least 1")
        if self.retry_delay <= 0:
            raise ValueError("retry_delay must be positive")


class NEARAgent:
    """Base NEAR agent class."""

    def __init__(self, config: AgentConfig):
        """Initialize agent."""
        self.config = config
        self._running = False
        self._initialize_near_connection()

    def _initialize_near_connection(self):
        """Initialize NEAR connection."""
        self.near_connection = NEARConnection(
            network=self.config.near_network,
            account_id=self.config.account_id,
            private_key=self.config.private_key,
            node_url=self.config.node_url
        )

    async def start(self):
        """Start agent."""
        try:
            # Test connection
            await self.near_connection.check_account(self.config.account_id)
            self._running = True
            logger.info(f"Agent started successfully for {self.config.account_id}")
        except Exception as e:
            logger.error(f"Failed to start agent: {str(e)}")
            raise

    async def stop(self):
        """Stop agent."""
        self._running = False
        logger.info(f"Agent stopped for {self.config.account_id}")

    def is_running(self) -> bool:
        """Check if agent is running."""
        return self._running

    async def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an action."""
        try:
            if not self.is_running():
                raise Exception("Agent is not running")

            # Validate action
            if not action.get("type"):
                raise ValueError("Missing action type")
            if not action.get("params"):
                raise ValueError("Missing action parameters")

            # Execute action based on type
            if action["type"] == "transaction":
                return await self.near_connection.send_transaction(action["params"])
            else:
                raise ValueError(f"Unsupported action type: {action['type']}")

        except Exception as e:
            logger.error(f"Failed to execute action: {str(e)}")
            raise

    async def close(self):
        """Clean up resources."""
        await self.stop()