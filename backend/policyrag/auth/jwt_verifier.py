import logging
from typing import Optional

import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from policyrag.config import settings

logger = logging.getLogger(__name__)

_bearer_scheme = HTTPBearer(auto_error=False)

# Cached JWKS client — initialized lazily
_jwks_client: Optional[PyJWKClient] = None


def _get_jwks_client() -> Optional[PyJWKClient]:
    """Lazily create a PyJWKClient for the Supabase JWKS endpoint."""
    global _jwks_client
    if _jwks_client is None and settings.SUPABASE_URL:
        jwks_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
        _jwks_client = PyJWKClient(jwks_url, cache_keys=True, lifespan=3600)
    return _jwks_client


def _detect_algorithm(token: str) -> str:
    """Peek at the token header to determine the signing algorithm."""
    try:
        header = jwt.get_unverified_header(token)
        return header.get("alg", "HS256")
    except Exception:
        return "HS256"


def verify_supabase_jwt(token: str) -> dict:
    """Decode and verify a Supabase JWT token.

    Supports both HS256 (legacy) and ES256 (newer Supabase projects).
    """
    if not settings.SUPABASE_JWT_SECRET and not settings.SUPABASE_URL:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Neither SUPABASE_JWT_SECRET nor SUPABASE_URL configured",
        )

    alg = _detect_algorithm(token)

    try:
        if alg.startswith("ES") or alg.startswith("RS"):
            # Asymmetric — use JWKS public key
            jwks_client = _get_jwks_client()
            if not jwks_client:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="SUPABASE_URL required for asymmetric JWT verification",
                )
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=[alg],
                audience="authenticated",
            )
        else:
            # Symmetric (HS256) — use shared secret
            if not settings.SUPABASE_JWT_SECRET:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="SUPABASE_JWT_SECRET required for HS256 verification",
                )
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=[alg],
                audience="authenticated",
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError as e:
        logger.error("JWT decode failed (alg=%s): %s", alg, e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
        )


_ANONYMOUS_USER = {
    "user_id": "00000000-0000-0000-0000-000000000000",
    "email": "anonymous@local",
    "role": "authenticated",
}


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> dict:
    """FastAPI dependency that extracts and verifies the current user from JWT.

    When neither SUPABASE_JWT_SECRET nor SUPABASE_URL is configured, auth is
    bypassed and an anonymous user is returned — useful for local dev.
    """
    if not settings.SUPABASE_JWT_SECRET and not settings.SUPABASE_URL:
        logger.debug("Auth disabled — using anonymous user")
        return _ANONYMOUS_USER

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_supabase_jwt(credentials.credentials)

    return {
        "user_id": payload.get("sub"),
        "email": payload.get("email"),
        "role": payload.get("role", "authenticated"),
    }
