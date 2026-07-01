import uuid
from datetime import datetime, timedelta

import bcrypt
from jose import jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.models import User


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def normalize_email(email: str) -> str:
    return email.strip().lower()


def create_user(db: Session, email: str, password: str, name: str) -> User:
    user = User(
        id=str(uuid.uuid4()),
        name=name.strip(),
        email=normalize_email(email),
        password_hash=hash_password(password),
        role="user",
        created_at=datetime.utcnow().isoformat(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == normalize_email(email)).first()


def create_tokens(user: User) -> dict[str, str]:
    payload = {
        "sub": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    refresh_payload = {
        "sub": user.id,
        "exp": datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return {
        "token": jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM),
        "refresh": jwt.encode(
            refresh_payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        ),
    }
