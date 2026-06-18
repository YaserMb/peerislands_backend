from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.users import User


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email.lower())
    return db.scalar(statement)


def create_user(
    db: Session,
    *,
    name: str,
    email: str,
    hashed_password: str,
) -> User:
    user = User(
        name=name,
        email=email.lower(),
        hashed_password=hashed_password,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
