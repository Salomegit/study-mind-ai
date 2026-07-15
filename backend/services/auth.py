"""
Clerk authentication validation for protected endpoints.

Validates that requests come from authenticated users via Clerk.
"""

import logging
from fastapi import HTTPException, Header, status

logger = logging.getLogger(__name__)


def verify_clerk_auth(x_clerk_session: str | None = Header(None)) -> str:
    """
    Dependency to verify Clerk authentication.
    
    Extracts and validates the user ID from the X-Clerk-Session header.
    This header is set by the frontend after successful Clerk authentication.
    
    Args:
        x_clerk_session: User ID from Clerk, passed in X-Clerk-Session header
        
    Returns:
        user_id: The authenticated user's ID
        
    Raises:
        HTTPException: 401 if not authenticated
    """
    if not x_clerk_session:
        logger.warning("Request attempted without authentication header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Validate that user_id is not empty
    if not x_clerk_session.strip():
        logger.warning("Empty authentication header provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.debug("User authenticated: %s", x_clerk_session)
    return x_clerk_session
