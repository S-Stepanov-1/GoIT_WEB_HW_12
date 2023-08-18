from sqlalchemy import Column, Integer, String, func, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import Date, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(50), nullable=True, unique=True)
    phone_number = Column(String(30), nullable=False, unique=True)
    birthday = Column(Date, nullable=True)
    position = Column(String(50), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    user = relationship("User", back_populates="contacts")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False, unique=True)
    user_email = Column(String(50), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=func.now())
    refresh_token = Column(String(255), nullable=True)
    contacts = relationship("Contact", back_populates="user")
