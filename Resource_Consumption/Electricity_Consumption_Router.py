from fastapi import APIRouter, Depends, HTTPException, status
from .Data_Schemas import CreateConsumption, UpdateConsumption, GetConsumption
from .Methods import (
    create_electricity_consumption,
    update_electricity_consumption,
    delete_electricity_consumption,
    get_electricity_consumption,
)
from Utility_Methods.Utility_Methods import verify_jwt

Electricity_Consumption_Router = APIRouter()


@Electricity_Consumption_Router.post("/", status_code=status.HTTP_201_CREATED)
async def create_electricity_record(
    data: CreateConsumption, payload=Depends(verify_jwt)
):
    user_id = payload.get("user_id")
    if user_id:
        try:
            response = await create_electricity_consumption(
                user_id=user_id, data=data
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error: {e}",
            )
    return response


@Electricity_Consumption_Router.patch("/", status_code=status.HTTP_200_OK)
async def update_electricity_record(
    data: UpdateConsumption, payload=Depends(verify_jwt)
):
    user_id = payload.get("user_id")
    if user_id:
        try:
            response = await update_electricity_consumption(
                user_id=user_id, data=data
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error: {e}",
            )
    return response


@Electricity_Consumption_Router.delete("/", status_code=status.HTTP_200_OK)
async def delete_electricity_record(
    data: GetConsumption, payload=Depends(verify_jwt)
):
    user_id = payload.get("user_id")
    if user_id:
        try:
            response = await delete_electricity_consumption(
                user_id=user_id, data=data
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error: {e}",
            )
    return response


@Electricity_Consumption_Router.get("/", status_code=status.HTTP_200_OK)
async def get_electricity_records(
    data: GetConsumption, payload=Depends(verify_jwt)
):
    user_id = payload.get("user_id")
    if user_id:
        try:
            response = await get_electricity_consumption(
                user_id=user_id, data=data
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error: {e}",
            )
    return response
