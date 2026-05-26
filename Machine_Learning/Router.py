# Machine_Learning/Router.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from Machine_Learning.predict import predict_consumption


router = APIRouter(prefix="/ml", tags=["Machine Learning"])


# =========================================================
# INPUT SCHEMA (MATCH YOUR NEW BACKEND MODEL)
# =========================================================
class ElectricityInput(BaseModel):

    num_people: int
    num_children: int
    bedrooms: int
    home_area: float

    has_ac: bool
    has_geyser: bool
    has_iron: bool
    has_washing_machine: bool
    has_dishwasher: bool
    has_induction: bool
    has_microwave: bool
    has_kettle: bool
    has_vacuum: bool
    has_room_heater: bool

    has_pool: bool
    has_garden: bool

    vacation_days: int
    climate: str

    month: int
    year: int


# =========================================================
# PREDICT ENDPOINT
# =========================================================
@router.post("/predict-electricity")
def predict_electricity(data: ElectricityInput):

    try:
        result = predict_consumption(data.dict())

        return {
            "status": "success",
            "data": result
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )