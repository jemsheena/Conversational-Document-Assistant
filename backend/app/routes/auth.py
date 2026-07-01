from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from jose import jwt
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.auth_utils import create_tokens, create_user, get_user_by_email, verify_password
from app.config import settings
from app.database import get_db

router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6)


class TokenResponse(BaseModel):
    token: str
    refresh: str


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if get_user_by_email(db, req.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    user = create_user(db, req.email, req.password, req.name)
    return TokenResponse(**create_tokens(user))


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = get_user_by_email(db, req.email)
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return TokenResponse(**create_tokens(user))


class RefreshRequest(BaseModel):
    token: str


@router.post("/refresh")
async def refresh(req: RefreshRequest):
    try:
        payload = jwt.decode(req.token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        new_payload = {
            "sub": payload["sub"],
            "name": payload.get("name"),
            "email": payload.get("email"),
            "role": payload.get("role", "user"),
            "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        }
        return {
            "token": jwt.encode(new_payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
