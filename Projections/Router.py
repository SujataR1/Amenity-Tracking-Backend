# Projections/Router.py

from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    status,
)

from .Data_Schemas import ProjectionRequest

from .Methods import predict_consumption

from Utility_Methods.Utility_Methods import verify_jwt


# =========================================================
# ROUTER
# =========================================================
Projection_Router = APIRouter()


# =========================================================
# PREDICT CONSUMPTION
# =========================================================
@Projection_Router.post(
    "/predict-consumption",
    status_code=status.HTTP_200_OK,
)
async def predict_consumption_api(
    request: ProjectionRequest,
    payload: dict = Depends(verify_jwt),
):
    """
    Predict electricity consumption for a user
    using ML models + questionnaire data.
    """

    try:

        result = await predict_consumption(
            resource_type=request.resource_type,
            month=request.month,
            year=request.year,
            payload=payload,
        )

        return result

    except HTTPException as e:
        # Forward existing HTTP errors
        raise e

    except Exception as e:
        print("Projection Error:", str(e))

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to predict consumption",
        )