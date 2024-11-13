# main.py
from fastapi import FastAPI
from Database_and_ORM.Database_Connector import init_db, close_db
from Users.Router import User_Router  # Import the user router
from decouple import config
from fastapi.middleware.cors import CORSMiddleware
from Methods import APIKeyMiddleware
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run startup code here
    await init_db()
    yield
    # Run shutdown code here
    await close_db()


# Initialize the app with lifespan
app = FastAPI(title="Amenity Tracking API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins; customize as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Apply APIKey middleware
app.add_middleware(APIKeyMiddleware)


# Global route
@app.get("/")
async def root():
    return {"message": "Welcome to the Amenity Tracking API"}


# Register the user router
app.include_router(User_Router, prefix="/users", tags=["Users"])
