from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from .Data_Schemas import CreateConsumption, UpdateConsumption, GetConsumption
from .Methods import (
    create_fuel_consumption,
    update_fuel_consumption,
    delete_fuel_consumption,
    get_fuel_consumption,
)
from Utility_Methods.Utility_Methods import verify_jwt

Fuel_Consumption_Router = APIRouter()


@Fuel_Consumption_Router.post("/", status_code=status.HTTP_201_CREATED)
async def create_fuel_record(
    data: CreateConsumption, payload=Depends(verify_jwt)
):
    user_id = payload.get("user_id")
    if user_id:
        try:
            response = await create_fuel_consumption(
                user_id=user_id, data=data
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error: {e}",
            )
    return response


@Fuel_Consumption_Router.put("/", status_code=status.HTTP_200_OK)
async def update_fuel_record(
    data: UpdateConsumption, payload=Depends(verify_jwt)
):
    user_id = payload.get("user_id")
    if user_id:
        try:
            response = await update_fuel_consumption(
                user_id=user_id, data=data
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error: {e}",
            )
    return response


@Fuel_Consumption_Router.delete("/", status_code=status.HTTP_200_OK)
async def delete_fuel_record(
    data: GetConsumption, payload=Depends(verify_jwt)
):
    user_id = payload.get("user_id")
    if user_id:
        try:
            response = await delete_fuel_consumption(
                user_id=user_id, data=data
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error: {e}",
            )
    return response


@Fuel_Consumption_Router.get("/", status_code=status.HTTP_200_OK)
async def get_fuel_records(
    data: GetConsumption,
    limit: Optional[str] = None,
    payload=Depends(verify_jwt),
):
    user_id = payload.get("user_id")
    if user_id:
        try:
            response = await get_fuel_consumption(
                user_id=user_id, data=data, limit=limit
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error: {e}",
            )
    return response
