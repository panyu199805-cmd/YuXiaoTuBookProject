"""启动时轻量 schema 补丁（generate_schemas 不会改已有表结构）。"""
from __future__ import annotations


async def apply_schema_patches() -> None:
    from tortoise import Tortoise

    conn = Tortoise.get_connection("default")

    rows = await conn.execute_query_dict(
        """
        SELECT COUNT(*) AS cnt FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'book_video'
          AND COLUMN_NAME = 'sort_order'
        """
    )
    if rows and rows[0].get("cnt", 0) == 0:
        await conn.execute_script(
            "ALTER TABLE book_video ADD COLUMN sort_order INT NOT NULL DEFAULT 0"
        )

    indexes = await conn.execute_query_dict(
        """
        SELECT INDEX_NAME, NON_UNIQUE FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'book_video'
          AND COLUMN_NAME = 'book_id'
        """
    )
    for row in indexes or []:
        if row.get("NON_UNIQUE") == 0:
            name = row.get("INDEX_NAME")
            if name and name != "PRIMARY":
                await conn.execute_script(f"ALTER TABLE book_video DROP INDEX `{name}`")
