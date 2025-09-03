import logging
logger = logging.getLogger("diviz.main")
logger.setLevel(logging.INFO)

import base64
import json
import logging
import os
from typing import Any, Dict, Optional

import httpx
from fastapi import FastAPI, HTTPException, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from pydantic import BaseModel

import os
from . import user_repository
from .auth.cognito_auth import CognitoAuth

# Initialize CognitoAuth with environment variables
cognito_auth = CognitoAuth(
    region=os.getenv("COGNITO_REGION", "us-east-1"),
    user_pool_id=os.getenv("COGNITO_USER_POOL_ID", ""),
    app_client_id=os.getenv("COGNITO_APP_CLIENT_ID", "")
)

# For backward compatibility
COGNITO_APP_CLIENT_ID = cognito_auth.app_client_id
COGNITO_REGION = cognito_auth.region
COGNITO_USER_POOL_ID = cognito_auth.user_pool_id

# Create FastAPI app instance
app = FastAPI(
    title="DiViz API",
    description="A meeting efficiency review API service",
    version="0.0.1"
)

logger.info("**** Will mount static files")
from fastapi.staticfiles import StaticFiles

# Mount static Next.js export at /static if present
# Support two locations: local export and packaged in Lambda under diviz/../frontend/out
candidates = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "out")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "frontend", "out")),
]
for d in candidates:
    logger.info("Looking for static static files in %s", d)

    if os.path.isdir(d):

        app.mount("/static", StaticFiles(directory=d), name="static")
        logger.info("Mounted static files from %s", d)
        
        # Redirect /static/ to /static/index.html
        @app.get("/static/")
        async def static_root():
            return RedirectResponse(url="/static/index.html")
        
        break



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
    return {
        "service": "DiViz API Service",
        "version": "0.0.1",
        "endpoints": {
            "/api/meet": "GET - meeting review"
        }
    }

# Enforce HTTPS in production by redirecting HTTP requests and setting HSTS
if os.getenv("STAGE") == "prod":
    @app.middleware("http")
    async def enforce_https_middleware(request: Request, call_next):
        # Respect upstream protocol header from API Gateway/ALB/CloudFront
        proto = request.headers.get("x-forwarded-proto") or request.url.scheme
        if proto and proto.lower() != "https":
            # Redirect to HTTPS preserving path and query
            url = request.url.replace(scheme="https")
            return RedirectResponse(url=str(url), status_code=307)
        response = await call_next(request)
        # Add HSTS header for browsers
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        return response





@app.get("/api/user")
async def user(
    current_user: Dict[str, Any] = Security(get_current_user),
):
    # Log minimal, non-sensitive user info for debugging
    uid = current_user.get("sub") or current_user.get("cognito:username") or current_user.get("username")
    email = current_user.get("email")
    logger.info("/api/user accessed by uid=%s email=%s", uid, email)
    return {"current_user": current_user}


@app.get("/api/meet/{google_meet}")
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

    # Extract user info from ID token
    id_token = tokens.get('id_token')
    if id_token:
        try:
            # Verify the ID token using cognito_auth
            claims = await cognito_auth.verify_token(id_token)
            
            # Extract user details
            user_id = claims.get('sub')
            email = claims.get('email')
            username = claims.get('cognito:username') or claims.get('username')
            
            if user_id and email:
                # Save or update user in repository
                user = user_repository.save_user(
                    user_id=user_id,
                    email=email,
                    username=username
                )
                logger.info("User saved to repository: %s (%s)", user_id, email)
            
        except HTTPException as he:
            logger.error("Token verification failed: %s", str(he.detail))
            raise
        except Exception as e:
            logger.error("Error processing ID token: %s", str(e), exc_info=True)

    # Create redirect response - use localhost for local dev
    if os.getenv("LOCAL_DEV") == "true":
        web_server_url = f"http://localhost:8000/static/index.html#access_token={tokens.get('access_token') or ''}"
    else:
        web_server_url = f"https://diviz.knovoselov.com/static/index.html#access_token={tokens.get('access_token') or ''}"

    response = RedirectResponse(url=web_server_url)

    return response




def main():
    """Main entry point for the application."""
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
