import time
from typing import Optional, Dict, Any, List

import httpx
from fastapi import HTTPException
from jose import jwt

# ---------------------------
# AWS Cognito Auth Utilities
# ---------------------------

class CognitoAuth:
    def __init__(
        self,
        region: str,
        user_pool_id: str,
        app_client_id: Optional[str] = None,
        allowed_groups: Optional[List[str]] = None,
    ) -> None:
        self.region = region
        self.user_pool_id = user_pool_id
        self.issuer = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"
        self.jwks_uri = f"{self.issuer}/.well-known/jwks.json"
        self.app_client_id = app_client_id
        self.allowed_groups = set(allowed_groups or [])
        self._jwks: Optional[Dict[str, Any]] = None
        self._jwks_fetched_at: float = 0.0
        self._jwks_ttl: float = 3600.0  # 1 hour cache

    async def _fetch_jwks(self) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(self.jwks_uri)
            resp.raise_for_status()
            return resp.json()

    async def _get_jwks(self) -> Dict[str, Any]:
        now = time.time()
        if not self._jwks or (now - self._jwks_fetched_at) > self._jwks_ttl:
            self._jwks = await self._fetch_jwks()
            self._jwks_fetched_at = now
        return self._jwks

    async def verify_token(self, token: str) -> Dict[str, Any]:
        # Get kid from header
        try:
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid token header")

        # Find the matching JWK
        jwks = await self._get_jwks()
        key = None
        for k in jwks.get("keys", []):
            if k.get("kid") == kid:
                key = k
                break
        if not key:
            raise HTTPException(status_code=401, detail="Public key not found")

        # Verify token
        options = {
            "verify_aud": bool(self.app_client_id),  # verify aud only if provided
            "verify_at_hash": False,
        }
        try:
            claims = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                audience=self.app_client_id if self.app_client_id else None,
                issuer=self.issuer,
                options=options,
            )
        except Exception:
            raise HTTPException(status_code=401, detail="Token verification failed")

        # Additional Cognito-specific checks
        token_use = claims.get("token_use")
        if token_use not in {"id", "access"}:
            raise HTTPException(status_code=401, detail="Invalid token use")

        if self.app_client_id:
            if token_use == "access":
                client_id = claims.get("client_id")
                if client_id != self.app_client_id:
                    raise HTTPException(status_code=401, detail="Invalid client_id")
            elif token_use == "id":
                aud = claims.get("aud")
                if aud != self.app_client_id:
                    raise HTTPException(status_code=401, detail="Invalid audience")

        # Authorization by groups if configured
        if self.allowed_groups:
            groups = set(claims.get("cognito:groups", []) or [])
            if not groups.intersection(self.allowed_groups):
                raise HTTPException(status_code=403, detail="Forbidden: insufficient group membership")

        return claims

