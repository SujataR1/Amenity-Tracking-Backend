# main.py
from fastapi import FastAPI
from Database_and_ORM.Database_Connector import init_db, close_db
from Users.Router import User_Router
from Admin.Router import Admin_Router
from Questionnaire.Router import Questionnaire_Router
from Resource_Consumption.Router import Consumption_Router
from Projections.Router import Projection_Router
from decouple import config
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware import Middleware
from Methods import VerifyAPIKeyMiddleware, APIActivityLoggingMiddleware
from contextlib import asynccontextmanager
from Machine_Learning.Router import router as ML_Router

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
    Middleware(VerifyAPIKeyMiddleware),
    Middleware(APIActivityLoggingMiddleware),
]

app = FastAPI(
    title="Amenity Tracking API",
    lifespan=lifespan,
    middleware=middlewares,
)


# Global route
@app.get("/")
async def root():
    return {"message": "Welcome to the Amenity Tracking API"}


# Register the routers
routers = [
    (User_Router, "/users", ["Users"]),
    (Questionnaire_Router, "/questionnaire", ["Questionnaire"]),
    (Admin_Router, "/admin", ["Admin"]),
    (Consumption_Router, "/consumption", ["Consumption"]),
    (Projection_Router, "/projection", ["Projection"]),
        (ML_Router, "/ml", ["Machine Learning"]),  
]

for router, prefix, tags in routers:
    app.include_router(router, prefix=prefix, tags=tags)
