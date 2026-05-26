from decouple import config

TORTOISE_ORM = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.mysql",
            "credentials": {
                "host": config("DB_HOST"),
                "port": int(config("DB_PORT")),
                "user": config("DB_USER"),
                "password": config("DB_PASSWORD"),
                "database": config("DB_NAME"),
                "ssl": {},
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