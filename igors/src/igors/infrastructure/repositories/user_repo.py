"""User repository - Data access for users table."""

from typing import Dict, List, Optional
from loguru import logger


class UserRepository:
    """
    Repository for user data access.
    In production, this would use SQLAlchemy ORM with PostgreSQL.
    """

    def __init__(self):
        # In-memory storage for demonstration
        # In production, this would be a database connection
        self._users: Dict[int, dict] = {}
        self._next_id = 1

    def get_by_id(self, user_id: int) -> Optional[dict]:
        """Get user by ID."""
        return self._users.get(user_id)

    def get_by_username(self, username: str) -> Optional[dict]:
        """Get user by username."""
        for user in self._users.values():
            if user.get("username") == username:
                return user
        return None

    def get_all(self, actif_only: bool = True) -> List[dict]:
        """Get all users."""
        users = list(self._users.values())
        if actif_only:
            return [u for u in users if u.get("actif", True)]
        return users

    def create(
        self,
        username: str,
        password_hash: str,
        nom: str,
        prenom: str,
        role: str,
        email: Optional[str] = None,
    ) -> dict:
        """Create a new user."""
        # Check if username exists
        if self.get_by_username(username):
            raise ValueError(f"Username {username} already exists")

        user = {
            "id": self._next_id,
            "username": username,
            "password_hash": password_hash,
            "nom": nom.upper(),
            "prenom": prenom.capitalize(),
            "role": role,
            "email": email,
            "actif": True,
            "otp_actif": False,
            "otp_secret": None,
            "date_creation": None,  # Would be set by DB
        }

        self._users[self._next_id] = user
        self._next_id += 1

        logger.info(f"User created: {username} (ID: {user['id']})")
        return user

    def update(self, user_id: int, updates: dict) -> Optional[dict]:
        """Update user fields."""
        user = self.get_by_id(user_id)
        if not user:
            return None

        # Update allowed fields
        allowed_fields = [
            "nom",
            "prenom",
            "email",
            "role",
            "actif",
            "otp_actif",
            "otp_secret",
        ]
        for key, value in updates.items():
            if key in allowed_fields:
                user[key] = value

        logger.info(f"User updated: ID {user_id}")
        return user

    def delete(self, user_id: int) -> bool:
        """Soft delete a user."""
        user = self.get_by_id(user_id)
        if not user:
            return False

        user["actif"] = False
        logger.info(f"User soft deleted: ID {user_id}")
        return True

    def search(self, query: str, role: Optional[str] = None) -> List[dict]:
        """Search users by name or username."""
        results = []
        query_lower = query.lower()

        for user in self._users.values():
            if not user.get("actif", True):
                continue

            # Search in name and username
            full_name = f"{user.get('nom', '')} {user.get('prenom', '')}".lower()
            username = user.get("username", "").lower()

            if query_lower in full_name or query_lower in username:
                if role is None or user.get("role") == role:
                    results.append(user)

        return results

    def count(self) -> int:
        """Get total number of users."""
        return len(self._users)
