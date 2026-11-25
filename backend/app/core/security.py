import time
from collections import defaultdict
from typing import Any, Union, Dict, List
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt
from fastapi import HTTPException, status
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = settings.SECRET_KEY
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is missing. It must be configured securely.")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1 day

_LOGIN_ATTEMPTS: Dict[str, List[float]] = defaultdict(list)
RATE_LIMIT_WINDOW = 60.0  # seconds
MAX_LOGIN_ATTEMPTS = 15   # per window

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def validate_password_policy(password: str) -> None:
    """
    Enforces minimum password security policy:
    - Minimum length of 8 characters
    - Must contain at least one letter and at least one digit
    """
    if not password or len(password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password does not meet policy: must be at least 8 characters long."
        )
    if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
        raise HTTPException(
            status_code=400,
            detail="Password does not meet policy: must contain both letters and numbers."
        )

def check_login_rate_limit(key: str) -> None:
    """Enforces in-memory sliding window rate limiting for login attempts."""
    now = time.time()
    attempts = [t for t in _LOGIN_ATTEMPTS[key] if now - t < RATE_LIMIT_WINDOW]
    if len(attempts) >= MAX_LOGIN_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later."
        )
    attempts.append(now)
    _LOGIN_ATTEMPTS[key] = attempts

def reset_login_rate_limit(key: str = None) -> None:
    """Reset rate limit entries."""
    if key:
        _LOGIN_ATTEMPTS.pop(key, None)
    else:
        _LOGIN_ATTEMPTS.clear()
