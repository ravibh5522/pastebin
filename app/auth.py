from datetime import datetime, timedelta
from typing import Optional
import os
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from . import crud, schemas
from .database import SessionLocal

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "43200"))  # 30 days default

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub") #type: ignore
        if username is None:
            return None
        return username
    except JWTError:
        return None

def get_current_user_from_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security), db: Session = Depends(get_db)):
    """Get current user from JWT token (optional)"""
    if not credentials:
        return None
    
    username = verify_token(credentials.credentials)
    if username is None:
        return None
    
    user = crud.get_user_by_username(db, username=username)
    return user

def get_user_from_token_string(token: str, db: Session):
    """Get user from token string (for WebSocket authentication)"""
    username = verify_token(token)
    if username is None:
        return None
    
    user = crud.get_user_by_username(db, username=username)
    return user

def get_current_user_from_request(request: Request, db: Session = Depends(get_db)):
    """Get current user from session cookie (optional)"""
    token = request.cookies.get("access_token")
    if not token:
        return None
    
    username = verify_token(token)
    if username is None:
        return None
    
    user = crud.get_user_by_username(db, username=username)
    return user

def redirect_if_authenticated(request: Request, db: Session = Depends(get_db)):
    """Redirect to dashboard if user is already authenticated"""
    current_user = get_current_user_from_request(request, db)
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return None

def require_user(current_user = Depends(get_current_user_from_token)):
    """Require authentication - raise exception if not authenticated"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user
