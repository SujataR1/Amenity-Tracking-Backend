from fastapi import HTTPException, status, Header
from Database_and_ORM.Database_Models import Blacklisted_Tokens
from decouple import config
import jwt


async def verify_jwt(authorization: str = Header(None)):
    """
    Dependency that verifies the JWT token and checks if it's blacklisted.
    """
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
        )

    # Remove "Bearer " prefix and decode the token
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(
            token, config("JWT_SECRET_STRING"), algorithms=["HS256"]
        )
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
    if await Blacklisted_Tokens.get_or_none(token=token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You have already logged out. Please log in again.",
        )

    return payload  # Return the decoded payload if the token is valid
