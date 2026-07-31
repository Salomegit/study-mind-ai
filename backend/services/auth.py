"""Clerk JWT validation for protected endpoints."""

import logging
from functools import lru_cache

import jwt
from fastapi import HTTPException, Header, status
from jwt import InvalidTokenError, PyJWKClient
from jwt.exceptions import PyJWKClientError

from config import settings

logger = logging.getLogger(__name__)


@lru_cache
def get_jwks_client(issuer: str) -> PyJWKClient:
    """Cache Clerk's signing keys instead of fetching them for every request."""
    return PyJWKClient(f"{issuer}/.well-known/jwks.json")








def verify_clerk_auth(authorization: str | None = Header(None)) -> str:
    """Verify a Clerk bearer token and return its authenticated subject."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    issuer = settings.CLERK_JWT_ISSUER.rstrip("/")
    if not issuer:
        logger.error("CLERK_JWT_ISSUER is not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication is not configured.",
        )

    token = authorization.removeprefix("Bearer ").strip()
    try:
        signing_key = get_jwks_client(issuer).get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=issuer,
        )
    except (InvalidTokenError, PyJWKClientError, ValueError) as error:
        logger.warning("Rejected invalid Clerk token: %s", error)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error

    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id


# Kept for routers and integrations that use the earlier dependency name.
require_user_id = verify_clerk_auth
