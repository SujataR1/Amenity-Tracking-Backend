from pydantic import BaseModel, EmailStr, Field
from enum import Enum
from typing import Optional


class RoleEnum(str, Enum):
    admin = "admin"
    user = "user"


class UserCreate(BaseModel):
    name: str
    email: EmailStr  # Automatically validates email format
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None


class LoginData(BaseModel):
    email: str
    password: str
