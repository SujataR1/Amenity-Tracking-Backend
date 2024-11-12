from Database_and_ORM.Database_Models import User, Blacklisted_Tokens, OTP
from Users.Data_Schemas import UserCreate, OTPTypeEnum
from tortoise.exceptions import IntegrityError
from passlib.hash import bcrypt
from typing import Union
import jwt
from datetime import datetime, timedelta
from decouple import config
from fastapi import HTTPException, status
from typing import Dict
from Utility_Methods.Utility_Methods import (
    get_token_from_authorization_header_value,
    create_jwt,
    verify_otp,
)


async def create_user(user_data: UserCreate) -> Union[User, dict]:
    """
    Creates a new user in the database with hashed password.
    """
    # Hash the password with a salt
    hashed_password = bcrypt.hash(user_data.password)

    # Create user model instance
   # Convert Pydantic model fields to a dictionary, excluding password
    user_dict = user_data.dict(exclude={"password"})  # Exclude password if not needed in user_dict
    user_dict['password'] = hashed_password  # Add the hashed password

    # Create user model instance
    user = User(**user_dict)

    try:
        await user.save()
        return {"message": "Account succesfully created!"}
    except IntegrityError:
        return {"error": "A user with this email already exists."}


async def authenticate_user(email: str, password: str):
    """
    Authenticates a user by email and password.
    """
    user = await User.get_or_none(email=email)
    if user is None or not bcrypt.verify(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token = create_jwt(str(user.id), expiration_duration=1440)
    return user, token


async def logout_user(authorization: str, payload: dict):
    """
    Logs out the user by adding the token to the blacklist.
    """
    if payload:
        try:
            token = get_token_from_authorization_header_value(authorization)
            await Blacklisted_Tokens.create(Blacklisted_Tokens=token)
            return {"message": "Successfully logged out"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Either you have already logged out, or there's something wrong on our end",
            )
    else:
        return "You have already logged out!"


async def update_user(update_data: dict, payload: dict):
    """
    Updates user details based on user_id extracted from JWT token in authorization header.
    """
    # Manually call verify_jwt with the authorization header

    if payload:
        user_id = payload.get("user_id")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Please log in",
            )

        # Retrieve the user from the database
        user = await User.get_or_none(id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        changes = {}

        # Iterate through the update data and apply changes
        for field, new_value in update_data.items():
            if field == "role":  # Exclude updating the role field
                continue
            current_value = getattr(user, field)
            if current_value != new_value:
                setattr(user, field, new_value)
                changes[field] = (
                    f"`{field}` updated from `{current_value}` to `{new_value}`"
                )

        if changes:
            await user.save()
            return changes
        else:
            return {"message": "Nothing was changed!"}

    else:
        return "Please login to update your data!"


async def delete_user(payload: dict, authorization: str):
    """
    Deletes a user based on user ID extracted from JWT token and blacklists the token.
    """
    # Extract user_id from payload
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please log in first to delete your account",
        )

    # Find the user and delete
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    await user.delete()

    # Blacklist the token
    token = get_token_from_authorization_header_value(
        authorization
    )  # Extract the token part from "Bearer <token>"
    await Blacklisted_Tokens.create(Blacklisted_Tokens=token)

    return {"message": "User deleted successfully and token blacklisted"}


async def verify_2fa_and_login(payload: dict, otp_code: int):
    """
    Verifies the OTP for 2FA and, if valid, generates a JWT token and sets it in the response headers.
    """
    # Retrieve the OTP entry for the user and 2FA purpose
    user_id = payload.get(user_id)
    verified = verify_otp(user_id, otp_code, purpose=OTPTypeEnum.TWO_FA)

    if verified:
        # Generate JWT token
        token = create_jwt(user_id, expiration_duration=1440)

        # Prepare response with the token in the headers
        response = {
            "message": "2FA verification successful. You are now logged in."
        }
        response.headers["Authorization"] = f"Bearer {token}"

    else:
        response = {"message": "2FA verification unsuccessful"}

    return response


async def verify_email_otp(payload: dict, otp_code: int) -> bool:
    """
    Verifies the OTP for email verification. If valid, marks the user's email as verified.
    """
    user_id = payload.get("user_id")
    if await verify_otp(
        otp_code, user_id, purpose=OTPTypeEnum.MAIL_VERIFICATION
    ):
        # Update the user's email_verified status
        user = await User.get(id=user_id)
        user.email_verified = True
        await user.save()
        return True
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired OTP for email verification",
    )


async def request_password_reset_by_email(email: str) -> str:
    """
    Checks if a user exists with the provided email and generates a password reset JWT token.
    """
    # Find user by email
    user = await User.get_or_none(email=email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with the provided email.",
        )

    # Generate reset token if user exists
    reset_token = await create_jwt(user.id, expiration_duration=2)
    return reset_token


async def reset_password(token: str, payload: dict, new_password: str):
    user_id = payload.get("user_id")
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )

    # Hash the new password and update the user's password
    user.password = bcrypt.hash(new_password)
    try:
        await user.save()
        await Blacklisted_Tokens.create(Blacklisted_Tokens=token)
        return {"message": "Password has been reset successfully."}
    except Exception as error:
        await Blacklisted_Tokens.create(Blacklisted_Tokens=token)
        return f"Error resetting password \n Details: {error}"
