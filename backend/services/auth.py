# backend/services/auth.py

"""
Clerk JWT verification for backend routes that need to know "whose" data
they're touching (e.g. scoping /sessions to the caller instead of every
student who has ever used this server).

No Clerk SDK needed — verifying a signature is a JWKS lookup + PyJWT,
not a whole client library.
"""

import base64
import logging

import jwt
from fastapi import HTTPException, Request

from config import settings

logger = logging.getLogger(__name__)

_jwks_client: jwt.PyJWKClient | None = None
_issuer: str | None = None


def _clerk_issuer() -> str:
    """
    Derive the Clerk Frontend API URL (== JWT issuer) from the publishable
    key: `pk_(test|live)_<base64(domain + "$")>`. The domain is public
    information — it's shipped to every browser — so decoding it here isn't
    a secret operation, just a way to avoid a second config value.
    """
    global _issuer
    if _issuer is not None:
        return _issuer

    key = settings.CLERK_PUBLISHABLE_KEY
    if not key:
        raise RuntimeError(
            "CLERK_PUBLISHABLE_KEY is not set. Copy the same value the frontend "
            "uses as NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY into backend/.env."
        )

    try:
        _, _, encoded = key.split("_", 2)
        padded = encoded + "=" * (-len(encoded) % 4)
        domain = base64.b64decode(padded).decode("utf-8").rstrip("$")
    except Exception as e:
        raise RuntimeError(f"Could not parse CLERK_PUBLISHABLE_KEY: {e}") from e

    _issuer = f"https://{domain}"
    return _issuer


def _get_jwks_client() -> jwt.PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = jwt.PyJWKClient(f"{_clerk_issuer()}/.well-known/jwks.json")
    return _jwks_client


def verify_token(token: str) -> str:
    """Verify a Clerk session JWT and return the Clerk user_id (`sub` claim)."""
    signing_key = _get_jwks_client().get_signing_key_from_jwt(token)
    payload = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        issuer=_clerk_issuer(),
        options={"require": ["exp", "iat", "sub"]},
    )
    return payload["sub"]


def _extract_bearer_token(request: Request) -> str | None:
    header = request.headers.get("authorization")
    if not header or not header.lower().startswith("bearer "):
        return None
    return header[7:].strip()


def get_optional_user_id(request: Request) -> str | None:
    """
    Best-effort auth dependency: returns the caller's Clerk user_id if a
    valid token was sent, None if no token was sent at all.

    A *present but invalid* token still raises 401 — silently downgrading
    to anonymous would let a client hide a broken/expired token instead of
    refreshing it.
    """
    token = _extract_bearer_token(request)
    if token is None:
        return None
    try:
        return verify_token(token)
    except Exception:
        logger.warning("Rejected invalid bearer token")
        raise HTTPException(status_code=401, detail="Invalid or expired auth token.")


def require_user_id(request: Request) -> str:
    """Auth-required dependency: raises 401 if no valid Clerk token is present."""
    user_id = get_optional_user_id(request)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return user_id
