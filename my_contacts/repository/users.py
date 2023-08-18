from typing import Type

from sqlalchemy.orm import Session

from my_contacts.database.models import User
from my_contacts.schemas import UserModel


async def get_user_by_email(email: str, db: Session) -> Type[User]:
    user = db.query(User).filter_by(user_email=email).first()
    if user:
        return user


async def create_user(body: UserModel, db: Session) -> User:
    new_user = User(**body.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


async def delete_user(user: User, db: Session) -> None:
    db.delete(user)
    db.commit()
    db.refresh(user)


async def update_token(user: Type[User], token: str | None, db: Session) -> None:
    user.refresh_token = token
    db.commit()
    db.refresh(user)
