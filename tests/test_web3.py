"""Tests for Web3 skill."""
import pytest


class TestWeb3Skill:
    """Tests for skills/web3/skill.py."""

    def test_get_wallet_balance_no_web3(self):
        """Returns error if web3.py not installed."""
        from skills.web3.skill import get_wallet_balance
        with patch.dict('sys.modules', {'web3': None}):
            # Force reimport to catch ImportError path
            import importlib
            import skills.web3.skill as web3_skill
            importlib.reload(web3_skill)
            result = web3_skill.get_wallet_balance("0x1234567890123456789012345678901234567890")
            assert "error" in result
            assert "web3.py not installed" in result["error"]

    def test_get_wallet_balance_bad_address(self):
        """Returns error for invalid address."""
        from skills.web3.skill import get_wallet_balance
        # If web3 installed, will fail on checksum; if not, returns error about web3
        result = get_wallet_balance("not-an-address")
        assert "error" in result

    def test_get_gas_price_structure(self):
        """Gas price returns dict with error or data."""
        from skills.web3.skill import get_gas_price
        result = get_gas_price("ethereum")
        assert isinstance(result, dict)
        assert "error" in result or "gas_price_wei" in result

    def test_read_contract_missing_params(self):
        """Returns error when missing required params."""
        from skills.web3.skill import read_contract
        result = read_contract("0x123", [], "balanceOf")
        # Either web3 missing error or address error
        assert "error" in result

    def test_send_transaction_no_key(self):
        """Returns error when no private key or web3 missing."""
        from skills.web3.skill import send_transaction
        result = send_transaction("0x123")
        assert "error" in result
        # Either web3 missing or private key missing
        error_lower = result["error"].lower()
        assert "private_key" in error_lower or "web3.py not installed" in error_lower


class TestWeb3Registry:
    """Tests for tool registration."""

    def test_register_tools(self):
        """Web3 tools can be registered."""
        from core.tool_registry import registry
        from skills.web3.skill import register_tools, unregister_tools
        register_tools()
        assert registry.has("get_wallet_balance")
        assert registry.has("get_gas_price")
        assert registry.has("read_contract")
        assert registry.has("send_transaction")
        unregister_tools()

    def test_unregister_tools(self):
        """Web3 tools can be unregistered."""
        from core.tool_registry import registry
        from skills.web3.skill import register_tools, unregister_tools
        register_tools()
        unregister_tools()
        assert not registry.has("get_wallet_balance")
        assert not registry.has("send_transaction")


# Patch helper
try:
    from unittest.mock import patch
except ImportError:
    pass
