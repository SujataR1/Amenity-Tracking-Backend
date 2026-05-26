from Database_and_ORM.Methods import init_db, close_db
from Database_and_ORM.Database_Models import APIActivityLog
from datetime import datetime, timezone
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from decouple import config
import traceback
from typing import Optional, Callable
import asyncio


# -------------------------
# Startup / Shutdown Events
# -------------------------
async def startup_event():
    await init_db()


async def shutdown_event():
    await close_db()


# -------------------------
# API KEY MIDDLEWARE
# -------------------------
class VerifyAPIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        excluded_paths = config(
            "EXCLUDED_PATHS",
            default="/users/signup,/users/login,/docs,/openapi.json"
        ).split(",")

        # NORMALIZE PATH (VERY IMPORTANT FIX)
        path = request.url.path.rstrip("/")

        excluded_paths = [p.strip().rstrip("/") for p in excluded_paths]

        # DEBUG (REMOVE LATER)
        print("PATH:", path)
        print("EXCLUDED:", excluded_paths)

        # SKIP PUBLIC ROUTES
        if path in excluded_paths:
            return await call_next(request)

        api_key = request.headers.get("x-api-key")
        valid_api_key = config("API_KEY", default=None)

        print("API KEY HEADER:", api_key)
        print("VALID KEY:", valid_api_key)

        if not api_key or api_key != valid_api_key:
            raise HTTPException(status_code=403, detail="Invalid API Key")

        return await call_next(request)
# -------------------------
# LOGGING FUNCTION
# -------------------------
async def log_api_activity(
    request: Request,
    response_status: Optional[int] = None,
    response_time: Optional[int] = None,
    error: Optional[str] = None,
    error_location: Optional[str] = None,
):

    endpoint_hit = request.url.path
    requesting_ip = request.client.host if request.client else "unknown"

    request_data = {
        "headers": dict(request.headers),
        "user_agent": request.headers.get("User-Agent"),
    }

    # Safe body read
    try:
        body = await request.body()
        request_data["body"] = body.decode("utf-8") if isinstance(body, bytes) else str(body)
    except Exception:
        request_data["body"] = "<unavailable>"

    response_data = {
        "status_code": response_status or 0,
    }

    try:
        await APIActivityLog.create(
            requesting_ip=requesting_ip,
            request=request_data,
            response=response_data,
            endpoint_hit=endpoint_hit,
            time_taken=response_time or 0,
            time_requested=getattr(request.state, "time_requested", datetime.now(timezone.utc)),
            time_responded=datetime.now(timezone.utc),
            error=error,
            error_location=error_location,
        )
    except Exception:
        # NEVER crash API due to logging failure
        pass


# -------------------------
# API ACTIVITY MIDDLEWARE
# -------------------------
class APIActivityLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):

        request.state.time_requested = datetime.now(timezone.utc)
        start_time = asyncio.get_event_loop().time()

        try:
            response = await call_next(request)

            response_time = int(
                (asyncio.get_event_loop().time() - start_time) * 1000
            )

            await log_api_activity(
                request,
                response_status=response.status_code,
                response_time=response_time,
            )

            return response

        except Exception as e:
            error_location = traceback.format_exc()

            await log_api_activity(
                request,
                error=str(e),
                error_location=error_location,
            )

            raise e