from fastapi import APIRouter, HTTPException, Depends
from .Data_Schemas import ProjectionRequest
from .Methods import (
    predict_consumption,
    get_training_status_from_file,
)  # Import the method
from Utility_Methods.Utility_Methods import verify_jwt
from os import path
import json
from decouple import config

Projection_Router = APIRouter()


@Projection_Router.post("/predict-consumption")
async def predict_consumption_api(
    request: ProjectionRequest, payload: dict = Depends(verify_jwt)
):
    """
    Predicts electricity consumption for a user based on their history, locality trends,
    and questionnaire answers.

    """
    try:
        result = await predict_consumption(
            user_id=request.user_id,
            month=request.month,
            year=request.year,
            payload=payload,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
