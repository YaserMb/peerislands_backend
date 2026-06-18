from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.db.models.users import User
from app.schemas.users import UserCreate
from app.services.users import create_user, get_user_by_email


def register_user(db: Session, payload: UserCreate) -> User:
    return create_user(
        db,
        name=payload.name,
        email=str(payload.email),
        hashed_password=get_password_hash(payload.password),
    )


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if user is None:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
