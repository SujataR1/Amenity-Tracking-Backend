import logging
import re
from urllib.parse import urlparse

from decouple import config
from dotenv import load_dotenv
from tortoise import Tortoise
from tortoise.exceptions import ValidationError

load_dotenv()

# =========================================================
# LOGGING
# =========================================================
logging.basicConfig(level=logging.INFO)

logging.getLogger("tortoise").setLevel(logging.INFO)
logging.getLogger("asyncio").setLevel(logging.WARNING)


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
    database_url = config("DATABASE_URL")
    parsed_url = urlparse(database_url)

    print("\n========== DATABASE DEBUG ==========")
    print("DB_ENGINE = PostgreSQL / asyncpg")
    print("DB_HOST =", parsed_url.hostname)
    print("DB_PORT =", parsed_url.port or 5432)
    print("DB_USER =", parsed_url.username)
    print("DB_NAME =", parsed_url.path.lstrip("/"))
    print("====================================\n")

    await Tortoise.init(
        db_url=database_url,
        modules={"models": ["Database_and_ORM.Database_Models"]},
    )

    print("Tortoise initialized successfully")

    await Tortoise.generate_schemas(safe=True)

    print("Schemas generated successfully")


# =========================================================
# CLOSE DB
# =========================================================
async def close_db():
    await Tortoise.close_connections()