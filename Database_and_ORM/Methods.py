import logging
import os
import re

from tortoise import Tortoise
from tortoise.exceptions import ValidationError
from decouple import config
from dotenv import load_dotenv

load_dotenv()

# =========================================================
# LOGGING
# =========================================================
logging.basicConfig(level=logging.DEBUG)

# Tortoise ORM logs
logging.getLogger("tortoise").setLevel(logging.DEBUG)

# aiomysql logs
logging.getLogger("aiomysql").setLevel(logging.DEBUG)

# asyncio logs
logging.getLogger("asyncio").setLevel(logging.DEBUG)

# =========================================================
# SSL CERTIFICATE PATH
# =========================================================
DB_CA_PATH = os.path.abspath(os.getenv("DB_CA_PATH"))

# =========================================================
# VALIDATION
# =========================================================
def validate_pan(value: str):
    PAN_PATTERN = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")

    if not PAN_PATTERN.match(value):
        raise ValidationError(
            "PAN must follow the format `AAAAANNNNA`"
        )

# =========================================================
# INIT DB
# =========================================================
async def init_db():

    print("\n========== DATABASE DEBUG ==========")
    print("DB_HOST =", config("DB_HOST"))
    print("DB_PORT =", config("DB_PORT"))
    print("DB_USER =", config("DB_USER"))
    print("DB_NAME =", config("DB_NAME"))
    print("DB_CA_PATH =", DB_CA_PATH)
    print("====================================\n")

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
                        "ssl": {
                            "ca": DB_CA_PATH
                        },
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

    print("Tortoise initialized successfully")

    await Tortoise.generate_schemas()

    print("Schemas generated successfully")

# =========================================================
# CLOSE DB
# =========================================================
async def close_db():
    await Tortoise.close_connections()