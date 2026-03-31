import jwt
import httpx
from functools import lru_cache
from fastapi import Request, HTTPException


CLERK_JWKS_URL = None
_jwks_client = None


def init_jwks(frontend_api: str):
    global CLERK_JWKS_URL, _jwks_client
    if frontend_api.startswith("https://"):
        CLERK_JWKS_URL = f"{frontend_api}/.well-known/jwks.json"
    else:
        CLERK_JWKS_URL = f"https://{frontend_api}/.well-known/jwks.json"
    _jwks_client = jwt.PyJWKClient(CLERK_JWKS_URL)


def get_current_user(request: Request) -> str | None:
    """Extract user_id from Clerk session token. Returns None if not authenticated."""
    token = request.cookies.get("__session") or _get_bearer_token(request)
    if not token:
        return None
    try:
        signing_key = _jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return payload.get("sub")
    except (jwt.exceptions.PyJWTError, Exception):
        return None


def require_auth(request: Request) -> str:
    """Require authentication. Raises 401 if not authenticated."""
    user_id = get_current_user(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user_id


def _get_bearer_token(request: Request) -> str | None:
    auth = request.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        return auth[7:]
    return None
