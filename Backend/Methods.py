from Database_and_ORM.Methods import init_db, close_db
from Database_and_ORM.Database_Models import Blacklisted_Tokens, User
import jwt
from fastapi import Request, HTTPException, status, Header
from starlette.middleware.base import BaseHTTPMiddleware
from decouple import config


async def startup_event():
    await init_db()


async def shutdown_event():
    await close_db()


class VerifyAPIKeyMiddleware(BaseHTTPMiddleware):
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
