from tortoise import Tortoise
from tortoise.exceptions import DBConnectionError
from Database_Models import User
from decouple import config


async def init_db():
    try:
        await Tortoise.init(
            db_url=f"mysql://{config("DATABASE_USERNAME")}:{config("DATABASE_PASSWORD")}@{config("DATABASE_HOST")}:{config("DATABASE_PORT")}/{config("DATABASE_NAME")}?minsize={config("MINIMUM_NUMBER_OF_CONCURRENT_DATABASE_CONNECTIONS_IN_THE_POOL")}&maxsize={config("MAXIMUM_NUMBER_OF_CONCURRENT_DATABASE_CONNECTIONS_IN_THE_POOL")}",
            modules={"models": ["User"]},
        )
        await Tortoise.generate_schemas(safe=True)
    except DBConnectionError as e:
        print("Database connection error:", e)


async def close_db():
    await Tortoise.close_connections()
