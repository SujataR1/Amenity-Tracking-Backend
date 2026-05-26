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
    await Tortoise.init(
        config={
            "connections": {
                "default": {
                    "engine": "tortoise.backends.mysql",
                    "credentials": {
                        "host": config("DB_HOST"),
                        "port": int(config("DB_PORT")),
                        "user": config("DB_USER"),
                        "password": config("DB_PASSWORD"),
                        "database": config("DB_NAME"),
                        "ssl": {},   # required for Aiven
                    },
                }
            },
            "apps": {
                "models": {
                    "models": ["Database_and_ORM.Database_Models"],
                    "default_connection": "default",
                }
            },
        }
    )
async def close_db():
    await Tortoise.close_connections()
