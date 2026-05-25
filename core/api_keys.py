"""API Keys management with Fernet encryption.

Provides endpoints for storing and retrieving API keys securely.
Keys are encrypted at rest using Fernet (AES-128 in CBC mode).
"""
import os
import json
from pathlib import Path
from typing import Dict, Optional
from cryptography.fernet import Fernet

# Fernet key file
_FERNET_KEY_FILE = Path("data/.fernet_key")
_KEYS_FILE = Path("data/.api_keys.enc")


def _get_or_create_fernet_key() -> bytes:
    """Get existing Fernet key or create new one."""
    if _FERNET_KEY_FILE.exists():
        return _FERNET_KEY_FILE.read_bytes()
    
    key = Fernet.generate_key()
    _FERNET_KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    _FERNET_KEY_FILE.write_bytes(key)
    return key


def _get_fernet() -> Fernet:
    """Get Fernet instance."""
    return Fernet(_get_or_create_fernet_key())


def save_api_key(name: str, value: str) -> bool:
    """Save an API key encrypted."""
    try:
        fernet = _get_fernet()
        
        # Load existing keys
        keys: Dict[str, str] = {}
        if _KEYS_FILE.exists():
            encrypted = _KEYS_FILE.read_bytes()
            try:
                decrypted = fernet.decrypt(encrypted).decode()
                keys = json.loads(decrypted)
            except Exception:
                keys = {}
        
        # Update key
        keys[name] = value
        
        # Save encrypted
        encrypted = fernet.encrypt(json.dumps(keys).encode())
        _KEYS_FILE.write_bytes(encrypted)
        
        # Also set as env var for current process
        os.environ[name] = value
        
        return True
    except Exception as e:
        print(f"Error saving API key: {e}")
        return False


def get_api_key(name: str) -> Optional[str]:
    """Get an API key (decrypted)."""
    # First check env var
    env_value = os.environ.get(name)
    if env_value:
        return env_value
    
    # Then check encrypted store
    try:
        if not _KEYS_FILE.exists():
            return None
        
        fernet = _get_fernet()
        encrypted = _KEYS_FILE.read_bytes()
        decrypted = fernet.decrypt(encrypted).decode()
        keys = json.loads(decrypted)
        return keys.get(name)
    except Exception:
        return None


def list_api_keys() -> Dict[str, str]:
    """List all saved API key names (without values)."""
    try:
        if not _KEYS_FILE.exists():
            return {}
        
        fernet = _get_fernet()
        encrypted = _KEYS_FILE.read_bytes()
        decrypted = fernet.decrypt(encrypted).decode()
        keys = json.loads(decrypted)
        # Return masked values
        return {k: "*" * min(len(v), 8) for k, v in keys.items()}
    except Exception:
        return {}


def delete_api_key(name: str) -> bool:
    """Delete an API key."""
    try:
        if not _KEYS_FILE.exists():
            return False
        
        fernet = _get_fernet()
        encrypted = _KEYS_FILE.read_bytes()
        decrypted = fernet.decrypt(encrypted).decode()
        keys = json.loads(decrypted)
        
        if name in keys:
            del keys[name]
            encrypted = fernet.encrypt(json.dumps(keys).encode())
            _KEYS_FILE.write_bytes(encrypted)
            
            # Also remove from env
            if name in os.environ:
                del os.environ[name]
            
            return True
        return False
    except Exception:
        return False


def load_all_keys_to_env():
    """Load all saved keys to environment variables."""
    try:
        if not _KEYS_FILE.exists():
            return
        
        fernet = _get_fernet()
        encrypted = _KEYS_FILE.read_bytes()
        decrypted = fernet.decrypt(encrypted).decode()
        keys = json.loads(decrypted)
        
        for name, value in keys.items():
            if name not in os.environ:
                os.environ[name] = value
    except Exception:
        pass
