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
from Utility_Methods.Utility_Methods import parse_limit_to_years


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


# async def update_electricity_consumption(
#     user_id: str, data: UpdateConsumption
# ) -> dict:
#     try:
#         record = await ElectricityConsumption.get(
#             user_id=user_id, month=data.month, year=data.year
#         )
#         record.electricity_consumption = data.consumption
#         record.updated_at = datetime.now(timezone.utc)
#         await record.save()
#         return {
#             "message": "Electricity consumption updated successfully",
#             "record": record,
#         }
#     except DoesNotExist:
#         return {"error": "Record not found for the specified criteria."}


# async def delete_electricity_consumption(
#     user_id: str, data: GetConsumption
# ) -> dict:
#     try:
#         record = await ElectricityConsumption.get(
#             user_id=user_id, month=data.month, year=data.year
#         )
#         await record.delete()
#         return {
#             "message": "Electricity consumption record deleted successfully"
#         }
#     except DoesNotExist:
#         return {"error": "Record not found for the specified criteria."}


async def get_electricity_consumption(
    user_id: str, data: GetConsumption
) -> dict:
    try:
        limit = data.limit
        years = await parse_limit_to_years(limit)

        if data.month and data.year:
            record = await ElectricityConsumption.get(
                user_id=user_id, month=data.month, year=data.year
            )
            return {"record": record}

        elif data.month and not data.year:
            records = (
                await ElectricityConsumption.filter(
                    user_id=user_id, month=data.month, year__in=years
                )
                .order_by("year")
                .all()
            )

            return {"records": records}

        elif data.year and not data.month:
            records = (
                await ElectricityConsumption.filter(
                    user_id=user_id, year=data.year
                )
                .order_by("month")
                .all()
            )
            return {"records": records}

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

    except DoesNotExist:
        return {"error": "No records found for the specified criteria."}
    except Exception as e:
        return {"error": str(e)}


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
    """
    Fetch gas consumption records based on the input criteria:
    - If both `month` and `year` are provided, return the specific record.
    - If only `year` is provided, return records for all months in that year.
    - If only `month` is provided, return records for the specified month across multiple years based on the `limit`.
    - If neither is provided, return records for the last 6 months.
    """
    try:
        limit = data.limit
        if data.month and data.year:
            # Fetch specific record for the given month and year
            record = await GasConsumption.get(
                user_id=user_id, month=data.month, year=data.year
            )
            return {"record": record}

        elif data.year and not data.month:
            # Fetch all records for the specified year
            records = (
                await GasConsumption.filter(user_id=user_id, year=data.year)
                .order_by("month")
                .all()
            )
            return {"records": records}

        elif data.month and not data.year:
            # Fetch records for the specified month across multiple years based on limit
            years = await parse_limit_to_years(limit)
            records = (
                await GasConsumption.filter(
                    user_id=user_id, month=data.month, year__in=years
                )
                .order_by("year")
                .all()
            )
            return {"records": records}

        else:
            # Default: Fetch records for the last 6 months
            six_months_ago = datetime.now() - timedelta(days=180)
            records = (
                await GasConsumption.filter(
                    user_id=user_id, created_at__gte=six_months_ago
                )
                .order_by("-created_at")
                .all()
            )
            return {"records": records}

    except DoesNotExist:
        return {"error": "No records found for the specified criteria."}
    except Exception as e:
        return {"error": str(e)}


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
    Fetch water consumption records based on the input criteria:
    - If both `month` and `year` are provided, return the specific record.
    - If only `year` is provided, return records for all months in that year.
    - If only `month` is provided, return records for the specified month across multiple years based on the `limit`.
    - If neither is provided, return records for the last 6 months.
    """
    try:
        limit = data.limit
        if data.month and data.year:
            # Fetch specific record for the given month and year
            record = await WaterConsumption.get(
                user_id=user_id, month=data.month, year=data.year
            )
            return {"record": record}

        elif data.year and not data.month:
            # Fetch all records for the specified year
            records = (
                await WaterConsumption.filter(user_id=user_id, year=data.year)
                .order_by("month")
                .all()
            )
            return {"records": records}

        elif data.month and not data.year:
            # Fetch records for the specified month across multiple years based on limit
            years = await parse_limit_to_years(limit)
            records = (
                await WaterConsumption.filter(
                    user_id=user_id, month=data.month, year__in=years
                )
                .order_by("year")
                .all()
            )
            return {"records": records}

        else:
            # Default: Fetch records for the last 6 months
            six_months_ago = datetime.now() - timedelta(days=180)
            records = (
                await WaterConsumption.filter(
                    user_id=user_id, created_at__gte=six_months_ago
                )
                .order_by("-created_at")
                .all()
            )
            return {"records": records}

    except DoesNotExist:
        return {"error": "No records found for the specified criteria."}
    except Exception as e:
        return {"error": str(e)}


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
    Retrieves fuel consumption records for the user based on the following:
    - If both `month` and `year` are provided, returns the specific record.
    - If only `year` is provided, returns records for all months in that year.
    - If only `month` is provided, returns records for the specified month across multiple years based on the `limit`.
    - If neither is provided, defaults to the latest 6 months.
    """
    try:
        limit = data.limit
        if data.month and data.year:
            # Fetch specific record for the given month and year
            record = await FuelConsumption.get(
                user_id=user_id, month=data.month, year=data.year
            )
            return {"record": record}

        elif data.year and not data.month:
            # Fetch all records for the specified year
            records = (
                await FuelConsumption.filter(user_id=user_id, year=data.year)
                .order_by("month")
                .all()
            )
            return {"records": records}

        elif data.month and not data.year:
            # Fetch records for the specified month across multiple years based on limit
            years = await parse_limit_to_years(limit)
            records = (
                await FuelConsumption.filter(
                    user_id=user_id, month=data.month, year__in=years
                )
                .order_by("year")
                .all()
            )
            return {"records": records}

        else:
            # Default: Fetch records for the last 6 months
            six_months_ago = datetime.now() - timedelta(days=180)
            records = (
                await FuelConsumption.filter(
                    user_id=user_id, created_at__gte=six_months_ago
                )
                .order_by("-created_at")
                .all()
            )
            return {"records": records}

    except DoesNotExist:
        return {"error": "No records found for the specified criteria."}
    except Exception as e:
        return {"error": str(e)}
