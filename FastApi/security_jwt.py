"""
JWT Authentication Module for BecasCGSU API
Provides token generation, validation, and security dependencies
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Security Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer security scheme
security = HTTPBearer()


# Models
class Token(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token data extracted from JWT"""
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None


class User(BaseModel):
    """User model for authentication"""
    id: str
    email: str
    role: str
    nombre: Optional[str] = None
    codigo: Optional[str] = None


# Password Utilities
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password

    Args:
        plain_password: Plain text password
        hashed_password: Bcrypt hashed password

    Returns:
        bool: True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt

    Args:
        password: Plain text password

    Returns:
        str: Bcrypt hashed password
    """
    return pwd_context.hash(password)


# Token Creation
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token

    Args:
        data: Data to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create a JWT refresh token with longer expiration

    Args:
        data: Data to encode in the token

    Returns:
        str: Encoded JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_tokens(user_id: str, email: str, role: str) -> Token:
    """
    Create both access and refresh tokens for a user

    Args:
        user_id: User ID
        email: User email
        role: User role

    Returns:
        Token: Token object with access and refresh tokens
    """
    token_data = {
        "sub": user_id,
        "email": email,
        "role": role
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": user_id})

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
    )


# Token Validation
def decode_token(token: str) -> TokenData:
    """
    Decode and validate a JWT token

    Args:
        token: JWT token string

    Returns:
        TokenData: Decoded token data

    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        role: str = payload.get("role")

        if user_id is None:
            raise credentials_exception

        token_data = TokenData(user_id=user_id, email=email, role=role)
        return token_data

    except JWTError as e:
        print(f"JWT Error: {str(e)}")
        raise credentials_exception


# Security Dependencies
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """
    Dependency to get the current authenticated user from JWT token

    Args:
        credentials: HTTP Bearer credentials from Authorization header

    Returns:
        TokenData: Decoded user information from token

    Raises:
        HTTPException: If token is missing, invalid, or expired
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere autenticación",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    return decode_token(token)


async def get_current_active_user(
    current_user: TokenData = Depends(get_current_user)
) -> TokenData:
    """
    Dependency to get the current active user (can be extended with user status checks)

    Args:
        current_user: Current user from token

    Returns:
        TokenData: Current active user data
    """
    # Here you can add additional checks like user status, account suspension, etc.
    return current_user


# Role-based Access Control
class RoleChecker:
    """
    Dependency class to check if user has required role
    """
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: TokenData = Depends(get_current_user)) -> TokenData:
        """
        Check if current user has one of the allowed roles

        Args:
            current_user: Current authenticated user

        Returns:
            TokenData: Current user if authorized

        Raises:
            HTTPException: If user doesn't have required role
        """
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rol insuficiente. Se requiere uno de: {', '.join(self.allowed_roles)}"
            )
        return current_user


# Pre-defined role dependencies
require_admin = RoleChecker(["admin"])
require_admin_or_campus_admin = RoleChecker(["admin", "campus_admin"])
require_any_role = RoleChecker(["admin", "campus_admin", "user"])
