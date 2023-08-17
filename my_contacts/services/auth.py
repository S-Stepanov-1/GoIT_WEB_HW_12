import logging
import os

from configparser import ConfigParser
from typing import Optional

from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime, timedelta

from my_contacts.database.db_connect import get_db
from my_contacts.repository import users as repository_users

current_folder = os.path.dirname(os.path.abspath(__file__))
parent_folder = os.path.dirname(current_folder)
base_folder = os.path.dirname(parent_folder)

init_file = os.path.join(base_folder, "config.ini")

config = ConfigParser()
config.read(init_file)

secret_key = config.get("KEY", "secret_key")


class Auth:
    pws_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    SECRET_KEY = secret_key
    ALGORITHM = "HS256"
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

    async def verify_password(self, plain_password, hashed_password):
        return self.pws_context.verify(plain_password, hashed_password)

    async def get_password_hash(self, password: str):
        return self.pws_context.hash(password)

    # define a function to generate a new access token
    async def create_access_token(self, data: dict, expires_delta: Optional[float] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(minutes=20)

        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "access_token"})
        encoded_access_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_access_token

    # define a function to generate a new refresh token
    async def create_refresh_token(self, data: dict, expires_delta: Optional[float] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(days=5)

        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "refresh_token"})
        encoded_refresh_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_refresh_token

    # define a function to decode a refresh_token
    async def decode_refresh_token(self, refresh_token: str):
        try:
            payload = jwt.decode(refresh_token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload["scope"] == "refresh_token":
                email = payload["sub"]
                return email
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid scope for token")
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    async def get_current_user(self, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            # Decode JWT
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'access_token':
                email = payload["sub"]
                if email is None:
                    raise credentials_exception
            else:
                raise credentials_exception
        except JWTError as err:
            logging.info(err)
            raise credentials_exception

        user = await repository_users.get_user_by_email(email, db)
        if user is None:
            raise credentials_exception
        return user


auth_service = Auth()
