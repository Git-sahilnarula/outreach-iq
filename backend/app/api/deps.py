from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.services.auth import decode_access_token

security = HTTPBearer(auto_error=False)

_AUTH_HEADERS = {"WWW-Authenticate": "Bearer"}


def _raise_401(detail: str = "Invalid authentication credentials"):
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail, headers=_AUTH_HEADERS)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Get the current authenticated user."""
    if credentials is None:
        _raise_401("Not authenticated")

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        _raise_401()

    email: str = payload.get("sub")
    if email is None:
        _raise_401()

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        _raise_401("User not found")

    return user
