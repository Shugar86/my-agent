"""Web3 / Blockchain integration skill.

Requires web3.py. Install: pip install web3
"""
import os
from typing import Dict, Optional


def get_wallet_balance(address: str, network: str = "ethereum") -> Dict:
    """Get ETH/native token balance for an address.

    Networks: ethereum, polygon, arbitrum, optimism, base, bsc
    """
    try:
        from web3 import Web3
    except ImportError:
        return {"error": "web3.py not installed. Run: pip install web3"}

    rpc_urls = {
        "ethereum": os.environ.get("ETH_RPC_URL", "https://eth.llamarpc.com"),
        "polygon": os.environ.get("POLYGON_RPC_URL", "https://polygon.llamarpc.com"),
        "arbitrum": os.environ.get("ARBITRUM_RPC_URL", "https://arbitrum.llamarpc.com"),
        "optimism": os.environ.get("OPTIMISM_RPC_URL", "https://optimism.llamarpc.com"),
        "base": os.environ.get("BASE_RPC_URL", "https://base.llamarpc.com"),
        "bsc": os.environ.get("BSC_RPC_URL", "https://bsc.llamarpc.com"),
    }

    rpc_url = rpc_urls.get(network, rpc_urls["ethereum"])
    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            return {"error": f"Cannot connect to {network} RPC"}

        checksum_addr = w3.to_checksum_address(address)
        balance_wei = w3.eth.get_balance(checksum_addr)
        balance_eth = w3.from_wei(balance_wei, "ether")

        return {
            "address": checksum_addr,
            "network": network,
            "balance_eth": float(balance_eth),
            "balance_wei": balance_wei,
            "rpc_url": rpc_url,
        }
    except Exception as e:
        return {"error": f"Failed to get balance: {str(e)}"}


def get_gas_price(network: str = "ethereum") -> Dict:
    """Get current gas price on a network."""
    try:
        from web3 import Web3
    except ImportError:
        return {"error": "web3.py not installed"}

    rpc_urls = {
        "ethereum": os.environ.get("ETH_RPC_URL", "https://eth.llamarpc.com"),
        "polygon": os.environ.get("POLYGON_RPC_URL", "https://polygon.llamarpc.com"),
        "arbitrum": os.environ.get("ARBITRUM_RPC_URL", "https://arbitrum.llamarpc.com"),
        "optimism": os.environ.get("OPTIMISM_RPC_URL", "https://optimism.llamarpc.com"),
        "base": os.environ.get("BASE_RPC_URL", "https://base.llamarpc.com"),
    }
    rpc_url = rpc_urls.get(network, rpc_urls["ethereum"])
    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            return {"error": f"Cannot connect to {network} RPC"}
        gas_price = w3.eth.gas_price
        return {
            "network": network,
            "gas_price_wei": gas_price,
            "gas_price_gwei": w3.from_wei(gas_price, "gwei"),
        }
    except Exception as e:
        return {"error": str(e)}


def read_contract(contract_address: str, abi: list, function_name: str, args: list = None, network: str = "ethereum") -> Dict:
    """Read data from a smart contract (view function)."""
    try:
        from web3 import Web3
    except ImportError:
        return {"error": "web3.py not installed"}

    rpc_urls = {
        "ethereum": os.environ.get("ETH_RPC_URL", "https://eth.llamarpc.com"),
        "polygon": os.environ.get("POLYGON_RPC_URL", "https://polygon.llamarpc.com"),
        "arbitrum": os.environ.get("ARBITRUM_RPC_URL", "https://arbitrum.llamarpc.com"),
        "optimism": os.environ.get("OPTIMISM_RPC_URL", "https://optimism.llamarpc.com"),
        "base": os.environ.get("BASE_RPC_URL", "https://base.llamarpc.com"),
    }
    rpc_url = rpc_urls.get(network, rpc_urls["ethereum"])
    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            return {"error": f"Cannot connect to {network} RPC"}

        contract = w3.eth.contract(
            address=w3.to_checksum_address(contract_address),
            abi=abi,
        )
        func = getattr(contract.functions, function_name)
        result = func(*(args or [])).call()

        return {
            "contract": contract_address,
            "function": function_name,
            "args": args,
            "result": result,
            "network": network,
        }
    except Exception as e:
        return {"error": f"Contract read failed: {str(e)}"}


def send_transaction(
    to_address: str,
    value_eth: float = 0.0,
    private_key: str = None,
    network: str = "ethereum",
    gas_limit: int = 21000,
) -> Dict:
    """Send native token (ETH/MATIC/etc) transaction.

    WARNING: Requires private key. Only use with test wallets.
    """
    try:
        from web3 import Web3
    except ImportError:
        return {"error": "web3.py not installed"}

    if not private_key:
        return {"error": "private_key is required"}

    rpc_urls = {
        "ethereum": os.environ.get("ETH_RPC_URL", "https://eth.llamarpc.com"),
        "polygon": os.environ.get("POLYGON_RPC_URL", "https://polygon.llamarpc.com"),
        "arbitrum": os.environ.get("ARBITRUM_RPC_URL", "https://arbitrum.llamarpc.com"),
        "optimism": os.environ.get("OPTIMISM_RPC_URL", "https://optimism.llamarpc.com"),
        "base": os.environ.get("BASE_RPC_URL", "https://base.llamarpc.com"),
    }
    rpc_url = rpc_urls.get(network, rpc_urls["ethereum"])
    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            return {"error": f"Cannot connect to {network} RPC"}

        account = w3.eth.account.from_key(private_key)
        nonce = w3.eth.get_transaction_count(account.address)
        gas_price = w3.eth.gas_price

        tx = {
            "nonce": nonce,
            "to": w3.to_checksum_address(to_address),
            "value": w3.to_wei(value_eth, "ether"),
            "gas": gas_limit,
            "gasPrice": gas_price,
            "chainId": w3.eth.chain_id,
        }

        signed = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)

        return {
            "tx_hash": tx_hash.hex(),
            "from": account.address,
            "to": to_address,
            "value_eth": value_eth,
            "network": network,
            "explorer_url": f"https://{'polygonscan.com' if network == 'polygon' else 'etherscan.io'}/tx/0x{tx_hash.hex()}",
        }
    except Exception as e:
        return {"error": f"Transaction failed: {str(e)}"}


def register_tools():
    from core.tool_registry import registry

    registry.register(
        name="get_wallet_balance",
        description="Get ETH/native token balance for a wallet address. Supports Ethereum, Polygon, Arbitrum, Optimism, Base, BSC.",
        parameters={
            "type": "object",
            "properties": {
                "address": {"type": "string", "description": "Wallet address (0x...)"},
                "network": {"type": "string", "default": "ethereum", "description": "Blockchain network"},
            },
            "required": ["address"],
        },
        execute_fn=lambda address="", network="ethereum": get_wallet_balance(address, network),
    )

    registry.register(
        name="get_gas_price",
        description="Get current gas price on a blockchain network.",
        parameters={
            "type": "object",
            "properties": {
                "network": {"type": "string", "default": "ethereum"},
            },
        },
        execute_fn=lambda network="ethereum": get_gas_price(network),
    )

    registry.register(
        name="read_contract",
        description="Read data from a smart contract (view function).",
        parameters={
            "type": "object",
            "properties": {
                "contract_address": {"type": "string"},
                "abi": {"type": "array", "description": "Contract ABI JSON"},
                "function_name": {"type": "string"},
                "args": {"type": "array", "default": []},
                "network": {"type": "string", "default": "ethereum"},
            },
            "required": ["contract_address", "abi", "function_name"],
        },
        execute_fn=lambda contract_address="", abi=None, function_name="", args=None, network="ethereum": read_contract(
            contract_address, abi or [], function_name, args or [], network
        ),
    )

    registry.register(
        name="send_transaction",
        description="Send native tokens (ETH/MATIC/etc). WARNING: requires private key. Use only test wallets.",
        parameters={
            "type": "object",
            "properties": {
                "to_address": {"type": "string"},
                "value_eth": {"type": "number", "default": 0.0},
                "private_key": {"type": "string", "description": "Private key (keep secret!)"},
                "network": {"type": "string", "default": "ethereum"},
                "gas_limit": {"type": "integer", "default": 21000},
            },
            "required": ["to_address", "private_key"],
        },
        execute_fn=lambda to_address="", value_eth=0.0, private_key=None, network="ethereum", gas_limit=21000: send_transaction(
            to_address, value_eth, private_key, network, gas_limit
        ),
    )


def unregister_tools():
    from core.tool_registry import registry
    for name in ["get_wallet_balance", "get_gas_price", "read_contract", "send_transaction"]:
        registry.unregister(name)
