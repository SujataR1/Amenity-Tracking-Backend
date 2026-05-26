from fastapi import FastAPI
from Database_and_ORM.Database_Connector import init_db, close_db

from Users.Router import User_Router
from Admin.Router import Admin_Router
from Questionnaire.Router import Questionnaire_Router
from Resource_Consumption.Router import Consumption_Router
from Projections.Router import Projection_Router
from Machine_Learning.Router import router as ML_Router

from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware import Middleware
from Methods import VerifyAPIKeyMiddleware, APIActivityLoggingMiddleware
from contextlib import asynccontextmanager

import joblib
from pathlib import Path

MODEL_PATH = Path("Machine_Learning/models/xgboost.pkl")


# -----------------------------
# LIFESPAN (DB INIT / CLOSE)
# -----------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()


# -----------------------------
# MIDDLEWARES
# -----------------------------
middlewares = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Authorization", "authorization"],
    ),
    Middleware(VerifyAPIKeyMiddleware),
    Middleware(APIActivityLoggingMiddleware),
]


# -----------------------------
# FASTAPI APP
# -----------------------------
app = FastAPI(
    title="Amenity Tracking API",
    lifespan=lifespan,
    middleware=middlewares,
)


# -----------------------------
# LOAD ML MODEL
# -----------------------------
@app.on_event("startup")
def load_model():
    global model
    model = joblib.load("Machine_Learning/models/xgboost.pkl")


# -----------------------------
# ROOT
# -----------------------------
@app.get("/")
async def root():
    return {"message": "Welcome to the Amenity Tracking API"}


# -----------------------------
# ROUTERS
# -----------------------------
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