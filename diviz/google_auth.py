import os
import logging
from typing import Any, Dict, Optional

import requests
from fastapi import HTTPException, Request
from authlib.integrations.httpx_client import OAuth2Client
from google.oauth2.credentials import Credentials

from .user_repository import user_repository

logger = logging.getLogger("diviz.google_auth")


class GoogleAuth:
    """Encapsulates Google OAuth logic and credential management."""

    AUTHORIZATION_BASE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    SCOPES = [
        "openid",
        "email",
        "profile",
        "https://www.googleapis.com/auth/calendar.readonly",
        "https://www.googleapis.com/auth/meetings.space.created",
    ]

    def __init__(
        self,
        base_url: str,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ) -> None:
        self.client_id = client_id or os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("GOOGLE_CLIENT_SECRET")
        self.base_url = base_url

        if not self.client_id or not self.client_secret:
            logger.warning("Google OAuth client ID/secret not configured.")

    def create_authorization_url(self, user) -> str:
        """Create the Google OAuth authorization URL and persist state on the user."""
        if not self.client_id or not self.client_secret:
            raise HTTPException(status_code=500, detail="Google OAuth not configured")
        if not self.base_url:
            raise HTTPException(status_code=500, detail="BASE_URL not configured")
        redirect_uri = f"{self.base_url}/static/index.html#google_callback"

        google = OAuth2Client(self.client_id, redirect_uri=redirect_uri)
        authorization_url, state = google.create_authorization_url(
            self.AUTHORIZATION_BASE_URL,
            access_type="offline",
            scope=self.SCOPES,
            prompt="consent",
        )
        logger.info("Authorization state: %s", state)
        # Persist OAuth state to the in-memory user store
        user.auth_state = state
        user_repository.save_user(user)
        return authorization_url

    def handle_callback(self, request: Request, user_claims: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the OAuth callback, exchange code for tokens, and save them."""
        if not self.client_id or not self.client_secret:
            raise HTTPException(status_code=500, detail="Google OAuth not configured")
        if not self.base_url:
            raise HTTPException(status_code=500, detail="BASE_URL not configured")
        redirect_uri = f"{self.base_url}/static/index.html#google_callback"

        google = OAuth2Client(self.client_id, redirect_uri=redirect_uri)
        tokens = google.fetch_token(
            self.TOKEN_URL,
            client_secret=self.client_secret,
            authorization_response=str(request.url),
        )
        user_id = user_claims.get("sub")
        self.save_tokens(user_id, tokens)
        return {"message": "Google account linked!"}

    def save_tokens(self, user_id: str, tokens: Dict[str, Any]) -> None:
        """Persist Google OAuth tokens to the user repository."""
        user = user_repository.get_user(user_id)
        if not user:
            logger.error("User not found: %s", user_id)
            raise HTTPException(status_code=404, detail="User not found")

        user.access_token = tokens.get("access_token")
        user.refresh_token = tokens.get("refresh_token")
        user.id_token = tokens.get("id_token")
        user.expires_in = tokens.get("expires_in")
        user.token_type = tokens.get("token_type")

        user_repository.save_user(user)
        logger.info("Updated Google tokens for user: %s", user_id)

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh Google access token using the stored refresh token."""
        if not refresh_token:
            raise ValueError("Missing refresh_token — cannot refresh access token.")

        if not self.client_id or not self.client_secret:
            raise HTTPException(status_code=500, detail="Google OAuth not configured")

        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }

        resp = requests.post(self.TOKEN_URL, data=payload)
        if resp.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to refresh Google token: {resp.status_code} {resp.text}",
            )

        new_tokens = resp.json()
        # Preserve refresh token; Google may not always return it
        new_tokens["refresh_token"] = refresh_token
        return new_tokens

    def get_credentials(self, user_claims: Dict[str, Any]) -> Credentials:
        """Build google.oauth2.credentials.Credentials for the current user."""
        if not self.client_id or not self.client_secret:
            logger.error("Google OAuth2 client ID or secret not configured")
            raise HTTPException(status_code=500, detail="Server configuration error")

        user_id = user_claims.get("sub")
        if not user_id:
            logger.error("User ID not found in token")
            raise HTTPException(status_code=404, detail="User ID not found in token")

        user = user_repository.get_user(user_id)
        if not user:
            logger.error("User not found: %s", user_id)
            raise HTTPException(status_code=404, detail="User not found")

        if not user.access_token and user.refresh_token:
            # Attempt refresh if we have a refresh token but no access token
            tokens = self.refresh_access_token(user.refresh_token)
            self.save_tokens(user_id, tokens)

        # Construct Credentials; googleapiclient can refresh as needed during API calls
        return Credentials(
            token=user.access_token,
            refresh_token=user.refresh_token,
            id_token=user.id_token,
            token_uri=self.TOKEN_URL,
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=self.SCOPES,
        )
