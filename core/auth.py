"""JWT Authentication for My Agent Web UI — multi‑user support.

Uses:
- python-jose for JWT creation/verification
- bcrypt directly for password hashing
- httpOnly cookies for token storage
- Persistent secret key from .env or .agent_secret file
"""

import os
import uuid
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from jose import JWTError, jwt
import bcrypt

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
_SECRET_KEY: str | None = None


def _load_or_create_secret() -> str:
    """Load secret from env, .env file, or .agent_secret file. Create if missing."""
    global _SECRET_KEY
    if _SECRET_KEY:
        return _SECRET_KEY

    # 1. Environment variable
    secret = os.environ.get("AGENT_SECRET_KEY", "").strip()
    if secret and secret.lower() not in ("change-me", "", "your-secret-key"):
        _SECRET_KEY = secret
        logger.info("JWT secret loaded from AGENT_SECRET_KEY env var")
        return _SECRET_KEY

    # 2. .agent_secret file in project root
    secret_file = Path(".agent_secret")
    if secret_file.exists():
        secret = secret_file.read_text(encoding="utf-8").strip()
        if secret:
            _SECRET_KEY = secret
            logger.info("JWT secret loaded from .agent_secret file")
            return _SECRET_KEY

    # 3. Generate and persist
    secret = os.urandom(32).hex()
    _SECRET_KEY = secret
    try:
        secret_file.write_text(secret, encoding="utf-8")
        logger.warning(
            "Generated new JWT secret and saved to .agent_secret. "
            "In production, set AGENT_SECRET_KEY env var instead."
        )
    except OSError as e:
        logger.error("Failed to write .agent_secret: %s. Using ephemeral secret.", e)
    return _SECRET_KEY


def get_secret_key() -> str:
    """Return the JWT secret key, loading/creating if necessary."""
    return _load_or_create_secret()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    if "jti" not in to_encode:
        to_encode["jti"] = uuid.uuid4().hex
    return jwt.encode(to_encode, get_secret_key(), algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, get_secret_key(), algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning("JWT decode failed: %s", e)
        return None
