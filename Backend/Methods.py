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
        Middleware to check for a valid API key in the request headers, excluding certain paths.
        """
        # List of paths to exclude from API key verification
        excluded_paths = config("EXCLUDED_PATHS")

        # Skip validation if the path is in the excluded paths
        if request.url.path in excluded_paths:
            return await call_next(request)

        # Fetch API key from request headers and compare with the valid key
        api_key = request.headers.get("API-Key")
        valid_api_key = config("API_KEY")

        if api_key != valid_api_key:
            raise HTTPException(status_code=403, detail="Invalid API Key")

        response = await call_next(request)
        return response
