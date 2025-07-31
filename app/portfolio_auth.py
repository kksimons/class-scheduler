# Portfolio Authentication middleware for FastAPI
# This provides secure communication between portfolio and class-scheduler backend

import hashlib
import base64
import time
from fastapi import HTTPException, Header
from typing import Optional

SALT = "portfolio-2025-scheduler-salt"
VALID_TIME_WINDOW = 5 * 60 * 1000  # 5 minutes in milliseconds


def validate_portfolio_request(
    auth_token: str, hash_value: str, timestamp_str: str
) -> dict:
    """
    Validate the authentication request from the portfolio
    """
    try:
        # Parse timestamp
        timestamp = int(timestamp_str)

        # Check if request is within valid time window
        now = int(time.time() * 1000)  # Current time in milliseconds
        if now - timestamp > VALID_TIME_WINDOW:
            return {"valid": False, "reason": "Request expired"}

        # Decode auth token
        payload = base64.b64decode(auth_token).decode("utf-8")
        parts = payload.split(":")

        if len(parts) != 2:
            return {"valid": False, "reason": "Invalid auth token format"}

        secret_key, token_timestamp = parts
        token_time = int(token_timestamp)

        # Verify timestamp matches
        if token_time != timestamp:
            return {"valid": False, "reason": "Timestamp mismatch"}

        # Recreate hash and verify
        expected_hash = hash_with_salt(payload)
        if hash_value != expected_hash:
            return {"valid": False, "reason": "Invalid hash"}

        return {"valid": True, "secret_key": secret_key}

    except Exception as e:
        return {"valid": False, "reason": f"Validation error: {str(e)}"}


def hash_with_salt(data: str) -> str:
    """
    Create hash with salt (must match frontend implementation)
    """
    return hashlib.sha256((data + SALT).encode()).hexdigest()


def verify_portfolio_auth(
    x_portfolio_auth: Optional[str] = Header(None),
    x_portfolio_hash: Optional[str] = Header(None),
    x_portfolio_timestamp: Optional[str] = Header(None),
) -> str:
    """
    FastAPI dependency to verify portfolio authentication
    Usage: Add as a dependency to protected endpoints
    """
    if not x_portfolio_auth or not x_portfolio_hash or not x_portfolio_timestamp:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "Missing authentication headers",
                "required": [
                    "X-Portfolio-Auth",
                    "X-Portfolio-Hash",
                    "X-Portfolio-Timestamp",
                ],
            },
        )

    validation = validate_portfolio_request(
        x_portfolio_auth, x_portfolio_hash, x_portfolio_timestamp
    )

    if not validation["valid"]:
        raise HTTPException(
            status_code=401,
            detail={"error": "Authentication failed", "reason": validation["reason"]},
        )

    # Return the validated secret key
    return validation["secret_key"]
