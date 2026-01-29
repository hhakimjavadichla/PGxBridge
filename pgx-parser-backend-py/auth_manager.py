"""
Authentication Manager - Handle user authentication and authorization.

This module provides user management, password hashing, and JWT token handling.
"""

import json
import logging
import secrets
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from enum import Enum
import hashlib
import hmac
import base64

logger = logging.getLogger(__name__)


class UserRole(str, Enum):
    """User roles for authorization."""
    ADMIN = "admin"
    USER = "user"


class AuthManager:
    """
    Manages user authentication and authorization.
    
    Stores users in a JSON file with hashed passwords.
    Uses simple token-based authentication.
    """
    
    _instance = None
    TOKEN_EXPIRY_HOURS = 24
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super(AuthManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize auth manager."""
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._users_file = self._get_users_file_path()
            self._tokens_file = self._get_tokens_file_path()
            self._secret_key = self._get_or_create_secret_key()
            self._ensure_users_file()
            self._active_tokens = self._load_tokens()
    
    def _get_users_file_path(self) -> Path:
        """Get path to users storage file."""
        backend_dir = Path(__file__).parent
        project_root = backend_dir.parent
        auth_dir = project_root / "auth"
        auth_dir.mkdir(exist_ok=True)
        return auth_dir / "users.json"
    
    def _get_tokens_file_path(self) -> Path:
        """Get path to tokens storage file."""
        backend_dir = Path(__file__).parent
        project_root = backend_dir.parent
        auth_dir = project_root / "auth"
        auth_dir.mkdir(exist_ok=True)
        return auth_dir / "tokens.json"
    
    def _get_secret_file_path(self) -> Path:
        """Get path to secret key file."""
        backend_dir = Path(__file__).parent
        project_root = backend_dir.parent
        auth_dir = project_root / "auth"
        auth_dir.mkdir(exist_ok=True)
        return auth_dir / ".secret_key"
    
    def _get_or_create_secret_key(self) -> str:
        """Get or create a secret key for token signing."""
        secret_file = self._get_secret_file_path()
        if secret_file.exists():
            return secret_file.read_text().strip()
        else:
            secret_key = secrets.token_hex(32)
            secret_file.write_text(secret_key)
            return secret_key
    
    def _ensure_users_file(self):
        """Ensure users file exists with default admin."""
        if not self._users_file.exists():
            # Create default admin user
            default_admin = {
                "username": "admin",
                "password_hash": self._hash_password("admin123"),
                "role": UserRole.ADMIN.value,
                "created_at": datetime.now().isoformat(),
                "created_by": "system",
                "active": True
            }
            
            users_data = {
                "metadata": {
                    "created": datetime.now().isoformat(),
                    "version": "1.0"
                },
                "users": [default_admin]
            }
            self._save_users_data(users_data)
            logger.info(f"Created users file with default admin. Username: admin, Password: admin123")
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using SHA-256 with salt."""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    def _verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify a password against stored hash."""
        try:
            salt, password_hash = stored_hash.split(':')
            computed_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return hmac.compare_digest(computed_hash, password_hash)
        except Exception:
            return False
    
    def _load_users_data(self) -> Dict:
        """Load users data from file."""
        try:
            with open(self._users_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading users data: {e}")
            return {"metadata": {}, "users": []}
    
    def _save_users_data(self, data: Dict):
        """Save users data to file."""
        try:
            with open(self._users_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving users data: {e}")
            raise
    
    def _load_tokens(self) -> Dict:
        """Load active tokens from file."""
        try:
            if self._tokens_file.exists():
                with open(self._tokens_file, 'r') as f:
                    tokens = json.load(f)
                    # Clean expired tokens
                    now = datetime.now()
                    valid_tokens = {}
                    for token, data in tokens.items():
                        expires = datetime.fromisoformat(data.get('expires', '2000-01-01'))
                        if expires > now:
                            valid_tokens[token] = data
                    return valid_tokens
            return {}
        except Exception as e:
            logger.error(f"Error loading tokens: {e}")
            return {}
    
    def _save_tokens(self):
        """Save active tokens to file."""
        try:
            with open(self._tokens_file, 'w') as f:
                json.dump(self._active_tokens, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving tokens: {e}")
    
    def _generate_token(self) -> str:
        """Generate a secure random token."""
        return secrets.token_urlsafe(32)
    
    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """
        Authenticate a user with username and password.
        
        Returns:
            dict with token and user info if successful, None otherwise
        """
        data = self._load_users_data()
        
        for user in data.get("users", []):
            if user.get("username") == username and user.get("active", True):
                if self._verify_password(password, user.get("password_hash", "")):
                    # Generate token
                    token = self._generate_token()
                    expires = datetime.now() + timedelta(hours=self.TOKEN_EXPIRY_HOURS)
                    
                    self._active_tokens[token] = {
                        "username": username,
                        "role": user.get("role", UserRole.USER.value),
                        "expires": expires.isoformat(),
                        "created": datetime.now().isoformat()
                    }
                    self._save_tokens()
                    
                    logger.info(f"User '{username}' authenticated successfully")
                    
                    return {
                        "token": token,
                        "username": username,
                        "role": user.get("role", UserRole.USER.value),
                        "expires": expires.isoformat()
                    }
        
        logger.warning(f"Failed authentication attempt for user '{username}'")
        return None
    
    def validate_token(self, token: str) -> Optional[Dict]:
        """
        Validate a token and return user info if valid.
        
        Returns:
            dict with user info if valid, None otherwise
        """
        if token not in self._active_tokens:
            return None
        
        token_data = self._active_tokens[token]
        expires = datetime.fromisoformat(token_data.get('expires', '2000-01-01'))
        
        if datetime.now() > expires:
            # Token expired
            del self._active_tokens[token]
            self._save_tokens()
            return None
        
        return {
            "username": token_data.get("username"),
            "role": token_data.get("role")
        }
    
    def logout(self, token: str) -> bool:
        """
        Invalidate a token (logout).
        
        Returns:
            True if token was found and removed
        """
        if token in self._active_tokens:
            del self._active_tokens[token]
            self._save_tokens()
            return True
        return False
    
    def is_admin(self, token: str) -> bool:
        """Check if token belongs to an admin user."""
        user_info = self.validate_token(token)
        if user_info:
            return user_info.get("role") == UserRole.ADMIN.value
        return False
    
    def create_user(
        self,
        username: str,
        password: str,
        role: str = "user",
        created_by: str = "admin"
    ) -> Dict:
        """
        Create a new user (admin only).
        
        Returns:
            dict with success status and message
        """
        data = self._load_users_data()
        
        # Check if username exists
        for user in data.get("users", []):
            if user.get("username") == username:
                return {"success": False, "message": f"Username '{username}' already exists"}
        
        # Validate role
        if role not in [r.value for r in UserRole]:
            return {"success": False, "message": f"Invalid role. Must be 'admin' or 'user'"}
        
        # Create user
        new_user = {
            "username": username,
            "password_hash": self._hash_password(password),
            "role": role,
            "created_at": datetime.now().isoformat(),
            "created_by": created_by,
            "active": True
        }
        
        data["users"].append(new_user)
        self._save_users_data(data)
        
        logger.info(f"User '{username}' created by '{created_by}'")
        
        return {
            "success": True,
            "message": f"User '{username}' created successfully",
            "user": {
                "username": username,
                "role": role,
                "created_at": new_user["created_at"]
            }
        }
    
    def delete_user(self, username: str, deleted_by: str) -> Dict:
        """
        Delete a user (admin only).
        
        Returns:
            dict with success status and message
        """
        if username == "admin":
            return {"success": False, "message": "Cannot delete the default admin user"}
        
        data = self._load_users_data()
        
        for i, user in enumerate(data.get("users", [])):
            if user.get("username") == username:
                del data["users"][i]
                self._save_users_data(data)
                
                # Invalidate any tokens for this user
                tokens_to_remove = [
                    t for t, d in self._active_tokens.items() 
                    if d.get("username") == username
                ]
                for token in tokens_to_remove:
                    del self._active_tokens[token]
                self._save_tokens()
                
                logger.info(f"User '{username}' deleted by '{deleted_by}'")
                return {"success": True, "message": f"User '{username}' deleted"}
        
        return {"success": False, "message": f"User '{username}' not found"}
    
    def update_password(self, username: str, new_password: str, updated_by: str) -> Dict:
        """
        Update a user's password.
        
        Returns:
            dict with success status and message
        """
        data = self._load_users_data()
        
        for user in data.get("users", []):
            if user.get("username") == username:
                user["password_hash"] = self._hash_password(new_password)
                user["updated_at"] = datetime.now().isoformat()
                user["updated_by"] = updated_by
                self._save_users_data(data)
                
                logger.info(f"Password updated for user '{username}' by '{updated_by}'")
                return {"success": True, "message": "Password updated successfully"}
        
        return {"success": False, "message": f"User '{username}' not found"}
    
    def list_users(self) -> List[Dict]:
        """
        List all users (without password hashes).
        
        Returns:
            List of user info dicts
        """
        data = self._load_users_data()
        
        users = []
        for user in data.get("users", []):
            users.append({
                "username": user.get("username"),
                "role": user.get("role"),
                "created_at": user.get("created_at"),
                "created_by": user.get("created_by"),
                "active": user.get("active", True)
            })
        
        return users
    
    def toggle_user_active(self, username: str, active: bool, updated_by: str) -> Dict:
        """
        Enable or disable a user.
        
        Returns:
            dict with success status and message
        """
        if username == "admin":
            return {"success": False, "message": "Cannot disable the default admin user"}
        
        data = self._load_users_data()
        
        for user in data.get("users", []):
            if user.get("username") == username:
                user["active"] = active
                user["updated_at"] = datetime.now().isoformat()
                user["updated_by"] = updated_by
                self._save_users_data(data)
                
                if not active:
                    # Invalidate tokens for disabled user
                    tokens_to_remove = [
                        t for t, d in self._active_tokens.items() 
                        if d.get("username") == username
                    ]
                    for token in tokens_to_remove:
                        del self._active_tokens[token]
                    self._save_tokens()
                
                status = "enabled" if active else "disabled"
                logger.info(f"User '{username}' {status} by '{updated_by}'")
                return {"success": True, "message": f"User '{username}' {status}"}
        
        return {"success": False, "message": f"User '{username}' not found"}


# Global instance
_auth_manager = None


def get_auth_manager() -> AuthManager:
    """Get or create global auth manager instance."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager
