# main.py
from fastapi import FastAPI
from Database_and_ORM.Database_Connector import init_db, close_db
from Users.Router import User_Router
from Questionnaire.Router import Questionnaire_Router
from decouple import config
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware import Middleware
from Methods import VerifyAPIKeyMiddleware
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run startup code here
    await init_db()
    yield
    # Run shutdown code here
    await close_db()


middlewares = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allows all origins; customize as needed
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Authorization", "authorization"],
    ),
    # Middleware(RateLimitMiddleware),
    Middleware(VerifyAPIKeyMiddleware),
    # Middleware(APITrackingMiddleware),
]

app = FastAPI(title="Amenity Tracking API", lifespan=lifespan, middleware=middlewares)


# Global route
@app.get("/")
async def root():
    return {"message": "Welcome to the Amenity Tracking API"}


# Register the routers
routers = [
    (User_Router, "/users", ["Users"]),
    (Questionnaire_Router, "/questionnaire", ["Questionnaire"]),
]

for router, prefix, tags in routers:
    app.include_router(router, prefix=prefix, tags=tags)
