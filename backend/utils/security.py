"""
utils/security.py
------------------
Purpose:
    All password-hashing and JWT (JSON Web Token) logic lives here so it
    is written once and reused by routes/auth.py and by the
    `get_current_user` dependency that protects private routes.

Important functions:
    hash_password(password)        -> bcrypt hash to store in MongoDB
    verify_password(plain, hashed) -> True/False
    create_access_token(data)      -> signed JWT string given to the client
    decode_access_token(token)     -> dict payload, or raises if invalid/expired

Why bcrypt + JWT:
    - We NEVER store plain-text passwords (see requirement #45 SECURITY).
    - JWT lets the backend stay stateless: the token itself proves who the
      user is, so we don't need a server-side session store for this
      mini-project.
"""

import os
import warnings
# Suppress passlib/bcrypt version detection warning (cosmetic only  -  auth works correctly)
warnings.filterwarnings("ignore", ".*error reading bcrypt version.*")
warnings.filterwarnings("ignore", ".*trapped.*")
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt, JWTError

JWT_SECRET = os.getenv("JWT_SECRET", "change_this_secret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# passlib handles bcrypt's salting for us automatically.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Turn a plain-text password into a one-way bcrypt hash."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a login attempt's password against the stored hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """
    Build a signed JWT containing `data` (usually {"sub": user_id, "role": role}).
    The token expires after ACCESS_TOKEN_EXPIRE_MINUTES so a stolen token
    doesn't work forever.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Verify signature + expiry and return the payload. Raises JWTError if invalid."""
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
