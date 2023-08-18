from fastapi import APIRouter, HTTPException, Depends, status, Security
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer

from my_contacts.database.db_connect import get_db
from ..repository import users as repository_users
from my_contacts.schemas import UserModel, UserResponse, TokenModel
from my_contacts.services.auth import auth_service


router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def register_user(body: UserModel = Depends(), db: Session = Depends(get_db)):
    exist_user = await repository_users.get_user_by_email(body.user_email, db)
    if exist_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        )
    body.password = await auth_service.get_password_hash(body.password)
    new_user = await repository_users.create_user(body, db)
    return {"user": [new_user.username, new_user.user_email], "detail": "User successfully created"}


@router.post("/login", response_model=TokenModel, status_code=status.HTTP_201_CREATED)
async def login(body: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = await repository_users.get_user_by_email(body.username, db)
    if user is None or not await auth_service.verify_password(body.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    access_token = await auth_service.create_access_token(data={"sub": user.user_email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.user_email})
    await repository_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token}


@router.get("/refresh_token")
async def get_refresh_token(credentials: HTTPAuthorizationCredentials = Security(security),
                            db: Session = Depends(get_db)):
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repository_users.get_user_by_email(email, db)

    if user.refresh_token != token:
        await repository_users.update_token(user, None, db)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    new_access_token = await auth_service.create_access_token(data={"sub": email})
    new_refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    await repository_users.update_token(user, new_refresh_token, db)
    return {"new_access_token": new_access_token, "refresh_token": new_refresh_token}
