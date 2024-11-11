# main.py
from fastapi import FastAPI
from Database_and_ORM.Methods import init_db, close_db
from Users.Router import User_Router  # Import the user router
from decouple import config
from Methods import add_cors_middleware, add_api_key_middleware
from contextlib import asynccontextmanager

app = FastAPI(title="Amenity Tracking API")

add_cors_middleware(app)
add_api_key_middleware(app)


# Global route
@app.get("/")
async def root():
    return {"message": "Welcome to the Amenity Tracking API"}


# Registering the user router
app.include_router(User_Router, prefix="/users", tags=["Users"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run startup code here
    await init_db()
    yield
    # Run shutdown code here
    await close_db()


app = FastAPI(lifespan=lifespan)
