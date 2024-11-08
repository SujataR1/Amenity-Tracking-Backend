from pydantic import BaseModel, EmailStr
from enum import Enum


class RoleEnum(str, Enum):
    admin = "admin"
    user = "user"


class UserCreate(BaseModel):
    name: str
    email: EmailStr  # Automatically validates email format
    password: str


class LoginData(BaseModel):
    email: str
    password: str
