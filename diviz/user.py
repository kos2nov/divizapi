from pydantic import BaseModel

class User(BaseModel):
    username: str | None = None
    email: str
    name: str | None = None
    groups: list[str] | None = None
    id: str | None = None # User ID
    ext_id: str | None = None # External ID from IDP provider
    ext_type: str | None = None # External ID type
    access_token: str | None = None # Access token for IDP provider
    id_token: str | None = None # ID token for IDP provider
    refresh_token: str | None = None # Refresh token for IDP provider
    expires_in: int | None = None # Expiration time for IDP provider
    token_type: str | None = None # Token type for IDP provider
    auth_state: str | None = None # OAuth state parameter for CSRF protection

    def mailto(self):
        return f"mailto:{self.username} <{self.email}>"
