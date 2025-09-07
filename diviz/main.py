import base64
import logging
import os
from typing import Any, Dict, Optional, List
from datetime import datetime, UTC, timedelta

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Request, Security, Depends
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request as GoogleRequest
from .user_repository import get_or_create_user_from_claims, user_repository
from .auth.cognito_auth import CognitoAuth
from .google_auth import GoogleAuth

# Configure root logger for the entire application
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Remove all existing handlers
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

# Create a simple formatter without timestamps
formatter = logging.Formatter('%(levelname)s: %(message)s')

# Create console handler and set formatter
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# Add handler to root logger
root_logger.addHandler(console_handler)

# Get logger for this module
logger = logging.getLogger(__name__)

# Create FastAPI app instance
app = FastAPI(
    title="DiViz API",
    description="A meeting efficiency review API service",
    version="0.0.1"
)

from fastapi.staticfiles import StaticFiles

# Mount static Next.js export at /static if present
# Support two locations: local export and packaged in Lambda under diviz/../frontend/out
candidates = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "out")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "frontend", "out")),
]
for d in candidates:

    if os.path.isdir(d):

        app.mount("/static", StaticFiles(directory=d), name="static")
        logger.info("Mounted static files from %s", d)
        
        # Redirect /static/ to /static/index.html
        @app.get("/static/")
        async def static_root():
            return RedirectResponse(url="/static/index.html")
        
        break

# Load environment variables from .env file if it exists
from dotenv import load_dotenv
load_dotenv(override=False)

LOCAL_DEV = os.getenv("LOCAL_DEV") == "true"
BASE_URL = "http://localhost:8000" if LOCAL_DEV else os.getenv("BASE_URL")


# Read Cognito config from environment variables
COGNITO_REGION = os.getenv("COGNITO_REGION")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_APP_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID")
COGNITO_APP_CLIENT_SECRET = os.getenv("COGNITO_APP_CLIENT_SECRET")
ALLOWED_GROUPS = [g.strip() for g in os.getenv("COGNITO_ALLOWED_GROUPS", "").split(",") if g.strip()]

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

logger.info("COGNITO_USER_POOL_ID = %s", COGNITO_USER_POOL_ID)


cognito_auth = CognitoAuth(
    region=COGNITO_REGION,
    user_pool_id=COGNITO_USER_POOL_ID,
    app_client_id=COGNITO_APP_CLIENT_ID,
    allowed_groups=ALLOWED_GROUPS,
)

security = HTTPBearer(auto_error=False)

# Initialize GoogleAuth helper
google_auth = GoogleAuth(
    base_url=BASE_URL,
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
)

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> Dict[str, Any]:
    # Local development mode - bypass auth
    if LOCAL_DEV:
        return {"sub": "local-user", "email": "dev@example.com", "cognito:username": "localdev"}

    if not cognito_auth:
        # Auth not configured; treat as unauthenticated environment
        return {"sub": "no-auth", "email": "no-auth@example.com", "cognito:username": "no-auth"}

    # Get token from Authorization header
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="No authorization token provided")
    
    token = credentials.credentials
    
    try:
        # Verify the token and get claims
        claims = await cognito_auth.verify_token(token)
        
        # Log minimal user info for debugging
        logger.info("Authenticated user: %s", claims.get('email'))
        
        return claims
    except HTTPException as he:
        logger.error("Token verification failed: %s", str(he.detail))
        raise
    except Exception as e:
        logger.error("Error verifying token: %s", str(e), exc_info=True)
        raise HTTPException(status_code=401, detail="Invalid or expired token")

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


async def get_google_credentials(
    user_claims: Dict[str, Any] = Security(get_current_user)
) -> Optional[Credentials]:
    """Get Google OAuth2 credentials for the user.
    
    Args:
        current_user: Validated user claims from the token
    
    Note: This requires GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to be set in the environment.
    """
    try:
        return google_auth.get_credentials(user_claims)
    except Exception as e:
        logger.error(f"Error creating Google credentials: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initialize Google API client")


@app.get("/api/meet/{meeting_code}")
async def get_google_meet_info(
    meeting_code: str,
    google_creds: Credentials = Depends(get_google_credentials)
):
    """Get Google Meet information using the user's OIDC token.
    
    Args:
        meeting_code: The Google Meet meeting code to look up
        google_creds: Google credentials
    """
    try:
        logger.info("Google credentials: %s", google_creds)

        # Build the Calendar API service with the Google credentials
        service = build('calendar', 'v3', credentials=google_creds)
        
        # Try to get the event by ID first
        # Uncomment the following block to disable ID-based event lookup
        # This is useful if the ID is a conference ID rather than a Google event ID
        #try:
        #    event = service.events().get(
        #        calendarId='primary',
        #        eventId=meeting_id,
        #    ).execute()
        #except Exception as e:
        #    logger.error(f"Error getting event by ID: {str(e)}, type: {type(e)}")
        #    pass  # Continue with conference ID search
            # If event not found by ID, try to search by conference ID
        
        maxTime = datetime.now(UTC).isoformat() + 'Z'  # 'Z' indicates UTC time
        minTime = (datetime.now(UTC) - timedelta(days=7)).isoformat() + 'Z'  # 'Z' indicates UTC time
        events_result = service.events().list(
            calendarId='primary',
            q=meeting_code,
            timeMin=minTime,
            timeMax=maxTime,
            maxResults=1,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        if not events:
            raise HTTPException(status_code=404, detail="Meeting not found")

        event = events[0]
        
        # Extract meeting details
        conference_data = event.get('conferenceData', {})
        video_entry = next(
            (ep for ep in conference_data.get('entryPoints', []) 
             if ep.get('entryPointType') == 'video'), 
            {}
        )
        
        attendees = [
            attendee.get('email', attendee.get('displayName', 'Unknown'))
            for attendee in event.get('attendees', [])
            if not attendee.get('self', False)  # Exclude the organizer
        ]
        
        return {
            'event_id': event.get('id', ''),
            'title': event.get('summary', 'No title'),
            'description': event.get('description', ''),
            'start_time': event.get('start', {}).get('dateTime'),
            'end_time': event.get('end', {}).get('dateTime'),
            'meet_link': video_entry.get('uri', ''),
            'meeting_code': video_entry.get('meetingCode', ''),
            'attendees': attendees,
            'organizer': event.get('organizer', {}).get('email', 'Unknown')
        }
        
    except Exception as e:
        logger.error("Error fetching Google Meet info: %s", e, exc_info=True)
        raise HTTPException(status_code=503, detail=f"Failed to fetch meeting information: {str(e)}")

@app.get("/api/user")
async def user(
    current_user: Dict[str, Any] = Security(get_current_user),
):
    """Get or create user from Cognito claims."""
    user = get_or_create_user_from_claims(current_user)
    logger.info("User accessed: %s", user.email)
    return user


@app.get("/auth/callback")
async def auth_callback(code: str):
    """
    Handle Cognito OAuth callback and forward id token to SPA
    """

    # Exchange code for tokens with Cognito
    token_endpoint = f"https://auth.diviz.knovoselov.com/oauth2/token"

    # Create Basic auth header with client credentials
    auth_string = f"{COGNITO_APP_CLIENT_ID}:{COGNITO_APP_CLIENT_SECRET}"
    auth_bytes = base64.b64encode(auth_string.encode()).decode()
    callback_url = f"{BASE_URL}/auth/callback"
    logger.info("Auth Callback URL: %s, code: %s, CLIENT_ID: %s, CLIENT_SECRET: %s", callback_url, code, COGNITO_APP_CLIENT_ID, COGNITO_APP_CLIENT_SECRET)
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            token_endpoint,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": callback_url
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {auth_bytes}"
            }
        )

        if token_response.status_code != 200:
            logger.error("Token exchange failed: %s status: %s", token_response.text, token_response.status_code)
            raise HTTPException(status_code=400, detail=f"Token exchange failed {token_response.text} status:{token_response.status_code}")

        tokens = token_response.json()
        logger.info("access_token: %s", tokens.get('access_token'))
        logger.info("refresh_token: %s", tokens.get('refresh_token'))
    

    id_token = tokens.get('id_token')
    if not id_token:
        logger.error("No ID token in response from Cognito")
        raise HTTPException(status_code=400, detail="No ID token received")

    try:
        #TODO refactor verify_token and get_or_create_user_from_claims to create user in one step
        # Verify the ID token using cognito_auth
        claims = await cognito_auth.verify_token(id_token)
        
        # Get or create user from claims
        user = get_or_create_user_from_claims(claims)
        user.access_token = tokens.get('access_token')
        user.refresh_token = tokens.get('refresh_token')
        user.id_token = id_token
        user.expires_in = tokens.get('expires_in')
        user.token_type = tokens.get('token_type')
        user_repository.save_user(user)

        logger.info("User processed in auth callback: %s", user.email)
        
    except HTTPException as he:
        logger.error("Token verification failed: %s", str(he.detail))
        raise
    except Exception as e:
        logger.error("Error processing ID token: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process ID token")

    # Build redirect URL with ID token
    redirect_url = f"{BASE_URL}/static/index.html#id_token={id_token}"
    return RedirectResponse(url=redirect_url)


@app.get("/api/google/connect")
def connect_google(user_claims: Dict[str, Any] = Security(get_current_user)):
    """Initiate Google OAuth flow by returning the authorization URL."""
    # Ensure a user object exists in the repository
    user = get_or_create_user_from_claims(user_claims)
    user_repository.save_user(user)
    authorization_url = google_auth.create_authorization_url(user)
    return {"authorization_url": authorization_url}


@app.get("/api/google/callback")
def google_callback(request: Request, user_claims: Dict[str, Any] = Security(get_current_user)):
    """Handle Google OAuth callback and store tokens linked to Cognito user."""
    return google_auth.handle_callback(request, user_claims)


# Google OAuth helper functions moved to diviz/google_auth.py


def main():
    """Main entry point for the application."""
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
