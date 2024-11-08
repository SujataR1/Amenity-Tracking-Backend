from tortoise import Tortoise
from tortoise.exceptions import DBConnectionError
from Database_Models import Database_Models
from decouple import config

async def init_db():
    try:
        await Tortoise.init(
            db_url=f"mysql://{config("DATABASE_USERNAME")}:{config("DATABASE_PASSWORD")}@{config("DATABASE_HOST")}:{config("DATABASE_PORT")}/{config("DATABASE_NAME")}",
            modules={"models": ["Database-Models"]},
        )
        await Tortoise.generate_schemas(safe=True)
    except DBConnectionError as e:
        print("Database connection error:", e)

async def close_db():
    await Tortoise.close_connections()