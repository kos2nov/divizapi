from typing import Dict, Optional
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
    
    def save_user(self, user_id: str, email: str, username: Optional[str] = None) -> User:
        """
        Save or update a user in the repository.
        Returns the created/updated user.
        """
        user = User(
            email=email,
            username=username or email.split('@')[0]  # Use part before @ as username if not provided
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

# Create a singleton instance of the repository
user_repository = UserRepository()
