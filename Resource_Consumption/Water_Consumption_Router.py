from fastapi import APIRouter, Depends, HTTPException, status
from .Data_Schemas import CreateConsumption, UpdateConsumption, GetConsumption
from .Methods import (
    create_water_consumption,
    update_water_consumption,
    delete_water_consumption,
    get_water_consumption,
)
from Utility_Methods.Utility_Methods import verify_jwt

Water_Consumption_Router = APIRouter()


@Water_Consumption_Router.post("/", status_code=status.HTTP_201_CREATED)
async def create_water_record(
    data: CreateConsumption, payload=Depends(verify_jwt)
):
    user_id = payload.get("user_id")
    if user_id:
        try:
            response = await create_water_consumption(
                user_id=user_id, data=data
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error: {e}",
            )
    return response


@Water_Consumption_Router.patch("/", status_code=status.HTTP_200_OK)
async def update_water_record(
    data: UpdateConsumption, payload=Depends(verify_jwt)
):
    user_id = payload.get("user_id")
    if user_id:
        try:
            response = await update_water_consumption(
                user_id=user_id, data=data
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error: {e}",
            )
    return response


@Water_Consumption_Router.delete("/", status_code=status.HTTP_200_OK)
async def delete_water_record(
    data: GetConsumption, payload=Depends(verify_jwt)
):
    user_id = payload.get("user_id")
    if user_id:
        try:
            response = await delete_water_consumption(
                user_id=user_id, data=data
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error: {e}",
            )
    return response


@Water_Consumption_Router.get("/", status_code=status.HTTP_200_OK)
async def get_water_records(data: GetConsumption, payload=Depends(verify_jwt)):
    user_id = payload.get("user_id")
    if user_id:
        try:
            response = await get_water_consumption(user_id=user_id, data=data)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error: {e}",
            )
    return response
