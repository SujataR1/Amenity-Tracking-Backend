from Database_and_ORM.Database_Models import User, Blacklisted_Tokens
from Backend.Users.Data_Schemas import UserCreate
from tortoise.exceptions import IntegrityError
from passlib.hash import bcrypt
from typing import Union
import jwt
from datetime import datetime, timedelta
from decouple import config
from fastapi import HTTPException, status
from typing import Dict
from Utilities.Utilities import get_token_from_authorization_header_value


async def create_user(user_data: UserCreate) -> Union[User, dict]:
    """
    Creates a new user in the database with hashed password.
    """
    # Hash the password with a salt
    hashed_password = bcrypt.hash(user_data.password)

    # Create user model instance
    user = User(
        name=user_data.name,
        email=user_data.email,
        password=hashed_password,
    )

    try:
        await user.save()
        return {"message": "Account succesfully created!"}
    except IntegrityError:
        return {"error": "A user with this email already exists."}


def create_jwt_token(user_id: str):
    """
    Generates a JWT token with the user ID.
    """
    payload = {
        "user_id": user_id,
        "exp": datetime.now() + timedelta(hours=24),  # Token valid for 1 day
    }
    token = jwt.encode(payload, config("JWT_SECRET_STRING"), algorithm="HS256")
    return token


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

    token = create_jwt_token(str(user.id))
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
