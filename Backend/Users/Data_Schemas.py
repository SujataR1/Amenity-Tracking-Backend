from pydantic import BaseModel, EmailStr, Field
from enum import Enum
from typing import Optional


class RoleEnum(str, Enum):
    admin = "admin"
    user = "user"


class OTPTypeEnum(str, Enum):
    TWO_FA = "2FA"
    PASSWORD_RESET = "Password Reset"
    MAIL_VERIFICATION = "Mail Verification"
    PHONE_VERIFICATION = "Phone Number Verification"


class MartialStatusEnum(str, Enum):
    unmarried = "Unmarried"
    married = "Married"
    divorced = "Divorced"
    judicially_separated = "Judicially Separated"
    widowed = "Widowed"


class UserCreate(BaseModel):
    name: str
    email: EmailStr  # Automatically validates email format
    password: str
    address: str
    pin_code: int
    phone_number: int
    aadhar_card_number: int
    pan: str
    occupation: str
    martial_status: MartialStatusEnum
    annual_income_bar: int


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    pin_code: Optional[int] = None
    phone_number: Optional[int] = None
    aadhar_card_number: Optional[int] = None
    pan: Optional[str] = None
    occupation: Optional[str] = None
    martial_status: Optional[MartialStatusEnum]
    annual_income_bar: Optional[int] = None


class LoginData(BaseModel):
    email: str
    password: str
