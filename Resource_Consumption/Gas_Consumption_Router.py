from fastapi import APIRouter, Depends, HTTPException, status
from .Data_Schemas import CreateConsumption, UpdateConsumption, GetConsumption
from .Methods import (
    create_gas_consumption,
    update_gas_consumption,
    delete_gas_consumption,
    get_gas_consumption,
)
from Utility_Methods.Utility_Methods import verify_jwt

Gas_Consumption_Router = APIRouter()


@Gas_Consumption_Router.post("/", status_code=status.HTTP_201_CREATED)
async def create_gas_record(
    data: CreateConsumption, payload=Depends(verify_jwt)
):
    user_id = payload.get("user_id")
    if user_id:
        try:
            response = await create_gas_consumption(user_id=user_id, data=data)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error: {e}",
            )
    return response


@Gas_Consumption_Router.patch("/", status_code=status.HTTP_200_OK)
async def update_gas_record(
    data: UpdateConsumption, payload=Depends(verify_jwt)
):
    user_id = payload.get("user_id")
    if user_id:
        try:
            response = await update_gas_consumption(user_id=user_id, data=data)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error: {e}",
            )
    return response


@Gas_Consumption_Router.delete("/", status_code=status.HTTP_200_OK)
async def delete_gas_record(data: GetConsumption, payload=Depends(verify_jwt)):
    user_id = payload.get("user_id")
    if user_id:
        try:
            response = await delete_gas_consumption(user_id=user_id, data=data)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error: {e}",
            )
    return response


@Gas_Consumption_Router.get("/", status_code=status.HTTP_200_OK)
async def get_gas_records(data: GetConsumption, payload=Depends(verify_jwt)):
    user_id = payload.get("user_id")
    if user_id:
        try:
            response = await get_gas_consumption(user_id=user_id, data=data)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error: {e}",
            )
    return response
