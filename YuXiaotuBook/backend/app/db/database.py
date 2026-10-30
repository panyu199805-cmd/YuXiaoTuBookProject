from app.core.config import settings

TORTOISE_ORM = {
    "connections": {"default": settings.DATABASE_URL},
    "apps": {
        "models": {
            "models": ["app.models", "aerich.models"],
            "default_connection": "default",
        }
    },
}


async def init_db() -> None:
    from tortoise import Tortoise

    from app.db.schema_patches import apply_schema_patches

    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas(safe=True)
    await apply_schema_patches()


async def close_db() -> None:
    from tortoise import Tortoise

    await Tortoise.close_connections()
