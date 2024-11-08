from Database_and_ORM.Methods import init_db, close_db
from Database_and_ORM.Database_Models import Blacklisted_Tokens
from fastapi.middleware.cors import CORSMiddleware
import jwt
from fastapi import Request, HTTPException, status, Header
from starlette.middleware.base import BaseHTTPMiddleware
from decouple import config


async def startup_event():
    await init_db()


async def shutdown_event():
    await close_db()


def add_cors_middleware(app):
    """
    Adds CORS middleware to the FastAPI app, permitting all origins.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allows all origins; customize as needed
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        """
        Middleware to check for a valid API key in the request headers.
        """
        api_key = request.headers.get("API-Key")
        valid_api_key = config("API_KEY")  # Fetch API key from environment

        if api_key != valid_api_key:
            raise HTTPException(status_code=403, detail="Invalid API Key")

        response = await call_next(request)
        return response

def add_api_key_middleware(app):
    """
    Adds API key middleware to the FastAPI app.
    """
    app.add_middleware(APIKeyMiddleware)

async def verify_jwt_token(authorization: str = Header(None)):
    """
    Dependency that verifies the JWT token and checks if it's blacklisted.
    """
    if authorization is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header missing")

    # Remove "Bearer " prefix and decode the token
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, config("JWT_SECRET_STRING"), algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Your session has expired, Please login again")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # Check if the token is blacklisted
    if await Blacklisted_Tokens.get_or_none(token=token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="You have already logged out. Please log in again.")

    return payload  # Return the decoded payload if the token is valid