from datetime import datetime, timedelta, timezone
from tortoise.exceptions import DoesNotExist, IntegrityError
from typing import List, Union
from Database_and_ORM.Database_Models import (
    ElectricityConsumption,
    GasConsumption,
    WaterConsumption,
    FuelConsumption,
)
from .Data_Schemas import (
    CreateConsumption,
    UpdateConsumption,
    GetConsumption,
)


async def create_electricity_consumption(
    user_id: str, data: CreateConsumption
) -> dict:
    try:
        record = await ElectricityConsumption.create(
            user_id=user_id,
            month=data.month,
            year=data.year,
            electricity_consumption=data.consumption,
        )
        return {
            "message": "Electricity consumption record created successfully",
            "record": record,
        }
    except IntegrityError:
        return {"error": "Record for this month and year already exists."}


async def update_electricity_consumption(
    user_id: str, data: UpdateConsumption
) -> dict:
    try:
        record = await ElectricityConsumption.get(
            user_id=user_id, month=data.month, year=data.year
        )
        record.electricity_consumption = data.consumption
        record.updated_at = datetime.now(timezone.utc)
        await record.save()
        return {
            "message": "Electricity consumption updated successfully",
            "record": record,
        }
    except DoesNotExist:
        return {"error": "Record not found for the specified criteria."}


async def delete_electricity_consumption(
    user_id: str, data: GetConsumption
) -> dict:
    try:
        record = await ElectricityConsumption.get(
            user_id=user_id, month=data.month, year=data.year
        )
        await record.delete()
        return {
            "message": "Electricity consumption record deleted successfully"
        }
    except DoesNotExist:
        return {"error": "Record not found for the specified criteria."}


async def get_electricity_consumption(
    user_id: str, data: GetConsumption
) -> Union[List[dict], dict]:
    if data.month and data.year:
        try:
            record = await ElectricityConsumption.get(
                user_id=user_id, month=data.month, year=data.year
            )
            return {"record": record}
        except DoesNotExist:
            return {"error": "No record found for the specified criteria."}
    else:
        six_months_ago = datetime.now() - timedelta(days=180)
        records = (
            await ElectricityConsumption.filter(
                user_id=user_id, created_at__gte=six_months_ago
            )
            .order_by("-created_at")
            .all()
        )
        return {"records": records}


# Gas Consumption Methods
async def create_gas_consumption(
    user_id: str, data: CreateConsumption
) -> dict:
    try:
        record = await GasConsumption.create(
            user_id=user_id,
            month=data.month,
            year=data.year,
            gas_consumption=data.consumption,
        )
        return {
            "message": "Gas consumption record created successfully",
            "record": record,
        }
    except IntegrityError:
        return {"error": "Record for this month and year already exists."}


async def update_gas_consumption(
    user_id: str, data: UpdateConsumption
) -> dict:
    try:
        record = await GasConsumption.get(
            user_id=user_id, month=data.month, year=data.year
        )
        record.gas_consumption = data.consumption
        record.updated_at = datetime.now(timezone.utc)
        await record.save()
        return {
            "message": "Gas consumption updated successfully",
            "record": record,
        }
    except DoesNotExist:
        return {"error": "Record not found for the specified criteria."}


async def delete_gas_consumption(user_id: str, data: GetConsumption) -> dict:
    try:
        record = await GasConsumption.get(
            user_id=user_id, month=data.month, year=data.year
        )
        await record.delete()
        return {"message": "Gas consumption record deleted successfully"}
    except DoesNotExist:
        return {"error": "Record not found for the specified criteria."}


async def get_gas_consumption(
    user_id: str, data: GetConsumption
) -> Union[List[dict], dict]:
    if data.month and data.year:
        try:
            record = await GasConsumption.get(
                user_id=user_id, month=data.month, year=data.year
            )
            return {"record": record}
        except DoesNotExist:
            return {"error": "No record found for the specified criteria."}
    else:
        six_months_ago = datetime.now() - timedelta(days=180)
        records = (
            await GasConsumption.filter(
                user_id=user_id, created_at__gte=six_months_ago
            )
            .order_by("-created_at")
            .all()
        )
        return {"records": records}


async def create_water_consumption(
    user_id: str, data: CreateConsumption
) -> dict:
    """
    Creates a new water consumption record for the user.
    """
    try:
        record = await WaterConsumption.create(
            user_id=user_id,
            month=data.month,
            year=data.year,
            water_consumption=data.consumption,
        )
        return {
            "message": "Water consumption record created successfully",
            "record": record,
        }
    except IntegrityError:
        return {"error": "Record for this month and year already exists."}


async def update_water_consumption(
    user_id: str, data: UpdateConsumption
) -> dict:
    """
    Updates an existing water consumption record for the user.
    """
    try:
        record = await WaterConsumption.get(
            user_id=user_id, month=data.month, year=data.year
        )
        record.water_consumption = data.consumption
        record.updated_at = datetime.now(timezone.utc)
        await record.save()
        return {
            "message": "Water consumption updated successfully",
            "record": record,
        }
    except DoesNotExist:
        return {"error": "Record not found for the specified criteria."}


async def delete_water_consumption(user_id: str, data: GetConsumption) -> dict:
    """
    Deletes an existing water consumption record for the user.
    """
    try:
        record = await WaterConsumption.get(
            user_id=user_id, month=data.month, year=data.year
        )
        await record.delete()
        return {"message": "Water consumption record deleted successfully"}
    except DoesNotExist:
        return {"error": "Record not found for the specified criteria."}


async def get_water_consumption(
    user_id: str, data: GetConsumption
) -> Union[List[dict], dict]:
    """
    Retrieves water consumption records for the user. If month and year are provided, retrieves a specific record.
    Defaults to the latest 6 months if no month and year are provided.
    """
    if data.month and data.year:
        try:
            record = await WaterConsumption.get(
                user_id=user_id, month=data.month, year=data.year
            )
            return {"record": record}
        except DoesNotExist:
            return {"error": "No record found for the specified criteria."}
    else:
        six_months_ago = datetime.now() - timedelta(days=180)
        records = (
            await WaterConsumption.filter(
                user_id=user_id, created_at__gte=six_months_ago
            )
            .order_by("-created_at")
            .all()
        )
        return {"records": records}


# Fuel Consumption Methods


async def create_fuel_consumption(
    user_id: str, data: CreateConsumption
) -> dict:
    """
    Creates a new fuel consumption record for the user.
    """
    try:
        record = await FuelConsumption.create(
            user_id=user_id,
            month=data.month,
            year=data.year,
            fuel_consumption=data.consumption,
        )
        return {
            "message": "Fuel consumption record created successfully",
            "record": record,
        }
    except IntegrityError:
        return {"error": "Record for this month and year already exists."}


async def update_fuel_consumption(
    user_id: str, data: UpdateConsumption
) -> dict:
    """
    Updates an existing fuel consumption record for the user.
    """
    try:
        record = await FuelConsumption.get(
            user_id=user_id, month=data.month, year=data.year
        )
        record.fuel_consumption = data.consumption
        record.updated_at = datetime.now(timezone.utc)
        await record.save()
        return {
            "message": "Fuel consumption updated successfully",
            "record": record,
        }
    except DoesNotExist:
        return {"error": "Record not found for the specified criteria."}


async def delete_fuel_consumption(user_id: str, data: GetConsumption) -> dict:
    """
    Deletes an existing fuel consumption record for the user.
    """
    try:
        record = await FuelConsumption.get(
            user_id=user_id, month=data.month, year=data.year
        )
        await record.delete()
        return {"message": "Fuel consumption record deleted successfully"}
    except DoesNotExist:
        return {"error": "Record not found for the specified criteria."}


async def get_fuel_consumption(
    user_id: str, data: GetConsumption
) -> Union[List[dict], dict]:
    """
    Retrieves fuel consumption records for the user. If month and year are provided, retrieves a specific record.
    Defaults to the latest 6 months if no month and year are provided.
    """
    if data.month and data.year:
        try:
            record = await FuelConsumption.get(
                user_id=user_id, month=data.month, year=data.year
            )
            return {"record": record}
        except DoesNotExist:
            return {"error": "No record found for the specified criteria."}
    else:
        six_months_ago = datetime.now() - timedelta(days=180)
        records = (
            await FuelConsumption.filter(
                user_id=user_id, created_at__gte=six_months_ago
            )
            .order_by("-created_at")
            .all()
        )
        return {"records": records}
