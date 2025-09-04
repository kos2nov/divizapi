from typing import Any, Dict, Optional
from .user import User
import logging

logger = logging.getLogger("diviz.user_repository")

class UserRepository:
    def __init__(self):
        self._users: Dict[str, User] = {}
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by their ID."""
        return self._users.get(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by their email address."""
        for user in self._users.values():
            if user.email.lower() == email.lower():
                return user
        return None
    
    def save_user(
        self, 
        user_id: str, 
        email: str, 
        username: Optional[str] = None,
        name: Optional[str] = None,
        ext_id: Optional[str] = None,
        ext_type: Optional[str] = None
    ) -> User:
        """
        Save or update a user in the repository.
        
        Args:
            user_id: The unique identifier for the user
            email: User's email address
            username: Optional username (defaults to email prefix if not provided)
            ext_id: Optional external ID from identity provider
            ext_type: Optional type of external ID (e.g., 'google')
            
        Returns:
            The created/updated User object
        """
        user = User(
            id=user_id,
            email=email,
            username=username,  
            name=name,
            ext_id=ext_id,
            ext_type=ext_type
        )
        self._users[user_id] = user
        logger.info("Saved user to repository: %s (ID: %s)", email, user_id)
        return user
    
    def delete_user(self, user_id: str) -> bool:
        """Remove a user from the repository. Returns True if user was found and removed."""
        if user_id in self._users:
            del self._users[user_id]
            logger.info("Removed user from repository: %s", user_id)
            return True
        return False

def get_or_create_user_from_claims(claims: Dict[str, Any]) -> User:
    """
    Get an existing user or create a new one from Cognito claims.
    
    Args:
        claims: Dictionary containing user claims from Cognito
        
    Returns:
        User: The existing or newly created user
        
    Raises:
        HTTPException: If required user information is missing from claims
    """
    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(status_code=404, detail="User ID not found in token")
        
    # Create new user if not found
    email = claims.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email not found in token")
        
    username = claims.get("cognito:username") or claims.get("username")
    name = claims.get("name")
    ext_id = None
    ext_type = None
    
    if identities := claims.get("identities"):
        idt = next((i for i in identities if i.get('providerName') == 'Google'), None)
        if idt:
            ext_id = idt.get('userId')
            ext_type = 'google'
            
    return user_repository.save_user(
        user_id=user_id,
        email=email,
        username=username,
        name=name,
        ext_id=ext_id,
        ext_type=ext_type
    )

# Create a singleton instance of the repository
user_repository = UserRepository()
