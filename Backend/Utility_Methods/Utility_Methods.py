from fastapi import HTTPException, status, Header
from Users.Data_Schemas import OTPTypeEnum
from Database_and_ORM.Database_Models import Blacklisted_Tokens, OTP
from decouple import config
import jwt
import random
from datetime import datetime, timedelta
from passlib.hash import bcrypt


async def get_token_from_authorization_header_value(
    authorization_header_value: str,
):
    token = authorization_header_value.split(" ")[1]
    return token


async def decode_jwt(token):
    payload = jwt.decode(
        token, config("JWT_SECRET_STRING"), algorithms=["HS256"]
    )
    return payload


async def verify_jwt(authorization: str = Header(None)):
    """
    Dependency that verifies the JWT token and checks if it's blacklisted.
    """
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please log in",
        )

    # Remove "Bearer " prefix and decode the token
    token = await get_token_from_authorization_header_value(authorization)
    try:
        payload = await decode_jwt(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your session has expired, Please login again",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    # Check if the token is blacklisted
    if await Blacklisted_Tokens.get_or_none(Blacklisted_Tokens=token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You have already logged out. Please log in again.",
        )

    return payload  # Return the decoded payload if the token is valid


async def generate_random_otp(length: int = 6) -> int:
    """Generates a random numeric OTP of specified length."""
    return "".join([str(random.randint(0, 9)) for _ in range(length)])


async def create_jwt(user_id: str, expiration_duration: int) -> str:
    """
    Generates a JWT token containing the user ID and expiration date.
    """
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow()
        + timedelta(minutes=expiration_duration),  # Token valid for 1 day
    }
    token = jwt.encode(payload, config("JWT_SECRET_STRING"), algorithm="HS256")
    return token


async def verify_otp(
    user_id: str, otp_code: int, purpose: OTPTypeEnum
) -> bool:
    """
    Verifies an OTP for a specific user and purpose. If valid, deletes the OTP.
    """
    otp_entry = await OTP.get_or_none(
        user_id=user_id, otp_code=otp_code, purpose=purpose
    )

    # Check OTP existence and expiration
    if otp_entry and otp_entry.expiration > datetime.utcnow():
        # OTP is valid; delete it after successful verification
        await otp_entry.delete()
        return True

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired OTP",
    )


async def verify_user_password(entered_password, user_password):
    verified = bcrypt.verify(entered_password, user_password)
    return verified
