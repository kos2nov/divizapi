import os
import time
from typing import Optional, Dict, Any, List
import logging
import httpx
from jose import jwt
import uvicorn
import base64

logger = logging.getLogger("diviz.main")


from fastapi import FastAPI, HTTPException, Body, Security, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.middleware.base import BaseHTTPMiddleware
import urllib.parse

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from diviz.user import User


class CookieToHeaderMiddleware(BaseHTTPMiddleware):
    """Middleware to extract JWT token from cookies and add to Authorization header"""
    
    async def dispatch(self, request: Request, call_next):
        # Check if Authorization header is already present
        if "authorization" not in request.headers:
            # Try to get token from cookies
            access_token = request.cookies.get("access_token")
            id_token = request.cookies.get("id_token")
            
            # Prefer id_token for user info, fallback to access_token
            token = id_token or access_token
            
            if token:
                # Add Authorization header
                request.headers.__dict__["_list"].append(
                    (b"authorization", f"Bearer {token}".encode())
                )
        
        response = await call_next(request)
        return response

# Create FastAPI app instance
app = FastAPI(
    title="DiViz API",
    description="A meeting efficiency review API service",
    version="0.0.1"
)

# Add cookie-to-header middleware
app.add_middleware(CookieToHeaderMiddleware)


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
            logger.info("Verifying token: %s", token)
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



# Read Cognito config from environment (set these in your deployment environment)
COGNITO_REGION = os.getenv("COGNITO_REGION", 'us-east-2')
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID", "us-east-2_GSNdrKDXE")
COGNITO_APP_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID", "5tb6pekknkes6eair7o39b3hh7")  # optional
COGNITO_APP_CLIENT_SECRET = os.getenv("COGNITO_APP_CLIENT_SECRET", "11u11b0rsfm0h23bp3jllta5736h55ahmgvm4u7bgsglvv9r72l7")  # required for token exchange
ALLOWED_GROUPS = [g.strip() for g in os.getenv("COGNITO_ALLOWED_GROUPS", "").split(",") if g.strip()]

# Create auth helper only if minimal config provided
cognito_auth: Optional[CognitoAuth] = None
if COGNITO_REGION and COGNITO_USER_POOL_ID:
    cognito_auth = CognitoAuth(
        region=COGNITO_REGION,
        user_pool_id=COGNITO_USER_POOL_ID,
        app_client_id=COGNITO_APP_CLIENT_ID,
        allowed_groups=ALLOWED_GROUPS,
    )

security = HTTPBearer(auto_error=False)


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> Dict[str, Any]:
    # Local development mode - bypass auth
    if os.getenv("LOCAL_DEV") == "true":
        return {"sub": "local-user", "email": "dev@example.com", "cognito:username": "localdev"}
    
    if not cognito_auth:
        # Auth not configured; treat as unauthenticated environment
        raise HTTPException(status_code=501, detail="Cognito auth not configured")

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = credentials.credentials
    return await cognito_auth.verify_token(token)


@app.get("/")
async def root():
    """
    Root endpoint with basic service information.
    """
    return {
        "service": "DiViz API Service",
        "version": "0.0.1",
        "endpoints": {
            "/review/meet": "GET - google meet review",
            "/user": "GET - current user info"
        }
    }


@app.get("/user")
async def user(
    current_user: Dict[str, Any] = Security(get_current_user),
):
    # Log minimal, non-sensitive user info for debugging
    uid = current_user.get("sub") or current_user.get("cognito:username") or current_user.get("username")
    email = current_user.get("email")
    logger.info("/user accessed by uid=%s email=%s", uid, email)
    return {"current_user": current_user}


@app.get("/review/meet/{google_meet}")
async def review(
    google_meet: str,
    current_user: Dict[str, Any] = Security(get_current_user),
):
    return {"meeting_code": google_meet}


@app.get("/auth/callback")
async def auth_callback(request: Request, code: str = None, state: str = None):
    """
    Handle Cognito OAuth callback and forward cookies to web server domain
    """
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code missing")
    
    # Exchange code for tokens with Cognito
    token_endpoint = f"https://auth.diviz.knovoselov.com/oauth2/token"
    
    # Create Basic auth header with client credentials
    auth_string = f"{COGNITO_APP_CLIENT_ID}:{COGNITO_APP_CLIENT_SECRET}"
    auth_bytes = base64.b64encode(auth_string.encode()).decode()
    
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            token_endpoint,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": f"https://diviz.knovoselov.com/auth/callback"
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {auth_bytes}"
            }
        )
        
        if token_response.status_code != 200:
            logger.error("Token exchange failed: %s status:%s", token_response.text, token_response.status_code)
            raise HTTPException(status_code=400, detail="Token exchange failed")
        
        tokens = token_response.json()
    
    # Create redirect response - use localhost for local dev
    if os.getenv("LOCAL_DEV") == "true":
        web_server_url = f"http://localhost:8000/user?token={tokens.get('id_token') or tokens.get('access_token')}"
    else:
        web_server_url = "https://diviz.knovoselov.com/user"
    
    response = RedirectResponse(url=web_server_url)

    logger.info("Auth tokens:  %s", tokens)

    # Set secure cookies with tokens
    response.set_cookie(
        key="access_token",
        value=tokens.get("access_token"),
        domain=".diviz.knovoselov.com",  # Replace with your domain
        secure=True,
        httponly=True,
        samesite="lax",
        max_age=tokens.get("expires_in", 3600)
    )
    
    if tokens.get("id_token"):
        response.set_cookie(
            key="id_token", 
            value=tokens.get("id_token"),
            domain=".diviz.knovoselov.com",  # Replace with your domain
            secure=True,
            httponly=True,
            samesite="lax",
            max_age=tokens.get("expires_in", 3600)
        )
    
    return response


def main():
    """Main entry point for the application."""
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
