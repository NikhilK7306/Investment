"""Security utilities for authentication and authorization."""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID

from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel, Field

from app.core.config.settings import get_settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenData(BaseModel):
    """JWT token payload."""
    sub: str  # user_id
    email: str
    roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    exp: int
    iat: int
    type: str = "access"


class TokenPair(BaseModel):
    """Access and refresh token pair."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenData(BaseModel):
    """Refresh token payload."""
    sub: str
    token_id: str
    exp: int
    iat: int
    type: str = "refresh"


def create_access_token(
    user_id: str,
    email: str,
    roles: Optional[List[str]] = None,
    permissions: Optional[List[str]] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create JWT access token."""
    settings = get_settings()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    now = datetime.utcnow()
    
    payload = {
        "sub": user_id,
        "email": email,
        "roles": roles or [],
        "permissions": permissions or [],
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "type": "access",
    }
    
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(user_id: str, token_id: str) -> str:
    """Create JWT refresh token."""
    settings = get_settings()
    
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    now = datetime.utcnow()
    
    payload = {
        "sub": user_id,
        "token_id": token_id,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "type": "refresh",
    }
    
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_token_pair(
    user_id: str,
    email: str,
    roles: Optional[List[str]] = None,
    permissions: Optional[List[str]] = None,
    refresh_token_id: Optional[str] = None,
) -> TokenPair:
    """Create access and refresh token pair."""
    import uuid
    
    access_token = create_access_token(user_id, email, roles, permissions)
    refresh_token = create_refresh_token(user_id, refresh_token_id or str(uuid.uuid4()))
    
    settings = get_settings()
    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


def decode_token(token: str, token_type: str = "access") -> TokenData:
    """Decode and validate JWT token."""
    settings = get_settings()
    
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        
        if payload.get("type") != token_type:
            raise JWTError(f"Invalid token type: expected {token_type}")
        
        if token_type == "access":
            return TokenData(**payload)
        else:
            return RefreshTokenData(**payload)
            
    except JWTError as e:
        raise ValueError(f"Invalid token: {str(e)}")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


class Permission:
    """Permission constants."""
    
    # IPO permissions
    IPO_READ = "ipo:read"
    IPO_WRITE = "ipo:write"
    IPO_DELETE = "ipo:delete"
    IPO_ANALYZE = "ipo:analyze"
    
    # Analysis permissions
    ANALYSIS_READ = "analysis:read"
    ANALYSIS_WRITE = "analysis:write"
    ANALYSIS_DELETE = "analysis:delete"
    
    # Report permissions
    REPORT_READ = "report:read"
    REPORT_WRITE = "report:write"
    REPORT_EXPORT = "report:export"
    
    # Memory permissions
    MEMORY_READ = "memory:read"
    MEMORY_WRITE = "memory:write"
    MEMORY_DELETE = "memory:delete"
    
    # Reflection permissions
    REFLECTION_READ = "reflection:read"
    REFLECTION_WRITE = "reflection:write"
    
    # Admin permissions
    ADMIN_USERS = "admin:users"
    ADMIN_SYSTEM = "admin:system"
    ADMIN_MONITORING = "admin:monitoring"
    
    # All permissions
    ALL = [
        IPO_READ, IPO_WRITE, IPO_DELETE, IPO_ANALYZE,
        ANALYSIS_READ, ANALYSIS_WRITE, ANALYSIS_DELETE,
        REPORT_READ, REPORT_WRITE, REPORT_EXPORT,
        MEMORY_READ, MEMORY_WRITE, MEMORY_DELETE,
        REFLECTION_READ, REFLECTION_WRITE,
        ADMIN_USERS, ADMIN_SYSTEM, ADMIN_MONITORING,
    ]


class Role:
    """Role definitions with permissions."""
    
    ROLE_PERMISSIONS: Dict[str, List[str]] = {
        "admin": Permission.ALL,
        "analyst": [
            Permission.IPO_READ,
            Permission.IPO_ANALYZE,
            Permission.ANALYSIS_READ,
            Permission.ANALYSIS_WRITE,
            Permission.REPORT_READ,
            Permission.REPORT_WRITE,
            Permission.REPORT_EXPORT,
            Permission.MEMORY_READ,
            Permission.REFLECTION_READ,
        ],
        "viewer": [
            Permission.IPO_READ,
            Permission.ANALYSIS_READ,
            Permission.REPORT_READ,
            Permission.MEMORY_READ,
            Permission.REFLECTION_READ,
        ],
        "api_user": [
            Permission.IPO_READ,
            Permission.IPO_ANALYZE,
            Permission.ANALYSIS_READ,
            Permission.REPORT_READ,
        ],
    }
    
    @classmethod
    def get_permissions(cls, role: str) -> List[str]:
        """Get permissions for a role."""
        return cls.ROLE_PERMISSIONS.get(role, [])
    
    @classmethod
    @classmethod
    def has_permission(cls, role: str, permission: str) -> bool:
        """Check if role has permission."""
        return permission in cls.get_permissions(role)
    
    @classmethod
    def get_all_roles(cls) -> List[str]:
        """Get all defined roles."""
        return list(cls.ROLE_PERMISSIONS.keys())


def require_permissions(required_permissions: List[str]) -> callable:
    """Dependency factory for permission checking."""
    from fastapi import Depends, HTTPException, status
    from app.core.security.auth import get_current_user
    
    async def permission_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_permissions = current_user.get("permissions", [])
        user_roles = current_user.get("roles", [])
        
        # Check direct permissions
        for perm in required_permissions:
            if perm in user_permissions:
                continue
            
            # Check role-based permissions
            has_perm = False
            for role in user_roles:
                if Role.has_permission(role, perm):
                    has_perm = True
                    break
            
            if not has_perm:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permission: {perm}"
                )
        
        return current_user
    
    return permission_checker


def require_roles(required_roles: List[str]) -> callable:
    """Dependency factory for role checking."""
    from fastapi import Depends, HTTPException, status
    from app.core.security.auth import get_current_user
    
    async def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_roles = current_user.get("roles", [])
        
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required roles: {', '.join(required_roles)}"
            )
        
        return current_user
    
    return role_checker


class APIKeyManager:
    """Manage API keys for external access."""
    
    def __init__(self):
        self.settings = get_settings()
    
    def generate_api_key(self, prefix: str = "ipo") -> str:
        """Generate a new API key."""
        import secrets
        return f"{prefix}_{secrets.token_urlsafe(32)}"
    
    def hash_api_key(self, api_key: str) -> str:
        """Hash an API key for storage."""
        return hash_password(api_key)
    
    def verify_api_key(self, plain_key: str, hashed_key: str) -> bool:
        """Verify an API key against its hash."""
        return verify_password(plain_key, hashed_key)


# Global API key manager
api_key_manager = APIKeyManager()