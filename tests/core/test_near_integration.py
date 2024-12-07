"""
Core NEAR Protocol Integration Tests
Tests essential functionality for interacting with NEAR Protocol
"""

import pytest
from unittest.mock import Mock, patch
import os
from dotenv import load_dotenv

from near_swarm.core.near_integration import NEARConnection


@pytest.fixture
def mock_near_provider():
    """Create a mock NEAR provider."""
    with patch('near_api.providers.JsonProvider') as mock_provider:
        mock_provider.return_value.get_account = Mock(return_value={
            "amount": "100000000000000000000000000",
            "locked": "0",
            "code_hash": "11111111111111111111111111111111",
        })
        yield mock_provider


@pytest.mark.asyncio
async def test_connection_initialization():
    """Test basic NEAR connection initialization with testnet."""
    connection = NEARConnection(
        network="testnet",
        account_id="test.testnet",
        private_key="ed25519:3D4YudUQRE39Lc4JHghuB5WM8kbgDDa34mnrEP5DdTApVH81af3e7MvFronz1F2u9wsnS4jx4nX4UNqm8M2n8acG"
    )
    assert connection.network == "testnet"
    assert connection.node_url == "https://rpc.testnet.near.org"


@pytest.mark.asyncio
async def test_env_configuration():
    """Test that environment configuration is valid."""
    load_dotenv()
    
    account_id = os.getenv("NEAR_ACCOUNT_ID")
    private_key = os.getenv("NEAR_PRIVATE_KEY")
    
    assert account_id, "NEAR_ACCOUNT_ID not found in .env"
    assert private_key, "NEAR_PRIVATE_KEY not found in .env"
    assert account_id.endswith(".testnet"), "Account ID must be a testnet account"
    assert private_key.startswith("ed25519:"), "Private key must be in ed25519 format" 