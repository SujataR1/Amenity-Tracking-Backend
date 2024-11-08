# main.py
from fastapi import FastAPI
from Database_and_ORM.Methods import init_db, close_db
from Users.Router import User_Router  # Import the user router
from decouple import config
from Methods import add_cors_middleware, add_api_key_middleware

app = FastAPI(title="Amenity Tracking API")

add_api_key_middleware(app)
add_cors_middleware(app)


# Global route
@app.get("/")
async def root():
    return {"message": "Welcome to the Amenity Tracking API"}


# Registering the user router
app.include_router(User_Router, prefix="/users", tags=["Users"])


# Initialize the database when the app starts
@app.on_event("startup")
async def startup_event():
    await init_db()


# Close the database when the app shuts down
@app.on_event("shutdown")
async def shutdown_event():
    await close_db()
