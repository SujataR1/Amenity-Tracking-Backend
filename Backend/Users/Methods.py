from Database_and_ORM.Database_Models import User, Blacklisted_Tokens
from JWT_Authentication.Verify_JWT import verify_jwt
from Users.API_Data_Schemas import UserCreate
from tortoise.exceptions import IntegrityError
from passlib.hash import bcrypt
from typing import Union
import jwt
from datetime import datetime, timedelta
from decouple import config
from fastapi import HTTPException, status, Depends


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
        return f"Account for {user.name} created successfully!"
    except IntegrityError:
        return {"error": "A user with this email already exists."}


def create_jwt_token(user_id: str):
    """
    Generates a JWT token with the user ID.
    """
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=24),  # Token valid for 1 day
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


async def logout_user(token: str, payload=Depends(verify_jwt)):
    """
    Logs out the user by adding the token to the blacklist.
    """
    try:
        await Blacklisted_Tokens.create(Blacklisted_Tokens=token)
        return {"message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Either you have already logged out, or there's something wrong on our end",
        )
