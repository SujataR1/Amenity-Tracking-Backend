from tortoise import Tortoise
from tortoise.exceptions import DBConnectionError, ValidationError
from decouple import config
import re


def validate_pan(value: str):
    PAN_PATTERN = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")
    if not PAN_PATTERN.match(value):
        raise ValidationError(
            "PAN must follow the format `AAAAANNNNA`, where `A` is an alphabet and `N` is a number."
        )


async def init_db():
    try:
        await Tortoise.init(
            db_url=f"{config('DATABASE_URL')}",
            modules={"models": ["Database_and_ORM.Database_Models"]},
        )
        await Tortoise.generate_schemas(safe=True)
    except DBConnectionError as e:
        print("Database connection error:", e)


async def close_db():
    await Tortoise.close_connections()
