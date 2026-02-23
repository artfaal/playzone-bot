import json
from typing import Any
import aiosqlite
from bot.database.connection import get_db


# --- Games ---

async def add_game(name: str, description: str | None, added_by_id: int, added_by_username: str | None) -> int:
    db = await get_db()
    cursor = await db.execute(
        "INSERT INTO games (name, description, added_by_id, added_by_username) VALUES (?, ?, ?, ?)",
        (name, description, added_by_id, added_by_username),
    )
    await db.commit()
    return cursor.lastrowid


async def get_active_games() -> list[aiosqlite.Row]:
    db = await get_db()
    cursor = await db.execute(
        """
        SELECT g.id, g.name, g.description,
               ROUND(AVG(r.score), 1) as avg_score,
               COUNT(r.id) as rating_count
        FROM games g
        LEFT JOIN ratings r ON r.game_id = g.id
        WHERE g.is_active = 1
        GROUP BY g.id
        ORDER BY
            CASE WHEN COUNT(r.id) > 0 THEN 0 ELSE 1 END,
            AVG(r.score) DESC NULLS LAST,
            g.name ASC
        """
    )
    return await cursor.fetchall()


async def get_game_by_name(name: str) -> aiosqlite.Row | None:
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM games WHERE name = ? AND is_active = 1", (name,)
    )
    return await cursor.fetchone()


async def get_game_by_id(game_id: int) -> aiosqlite.Row | None:
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM games WHERE id = ? AND is_active = 1", (game_id,)
    )
    return await cursor.fetchone()


async def soft_delete_game(name: str) -> bool:
    db = await get_db()
    cursor = await db.execute(
        "UPDATE games SET is_active = 0 WHERE name = ? AND is_active = 1", (name,)
    )
    await db.commit()
    return cursor.rowcount > 0


# --- Polls ---

async def create_poll(
    telegram_poll_id: str,
    message_id: int,
    chat_id: int,
    poll_type: str,
    options_map: dict,
    related_game_id: int | None = None,
) -> int:
    db = await get_db()
    cursor = await db.execute(
        """
        INSERT INTO polls (telegram_poll_id, message_id, chat_id, poll_type, options_map, related_game_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (telegram_poll_id, message_id, chat_id, poll_type, json.dumps(options_map), related_game_id),
    )
    await db.commit()
    return cursor.lastrowid


async def get_open_poll(chat_id: int) -> aiosqlite.Row | None:
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM polls WHERE chat_id = ? AND is_closed = 0 ORDER BY created_at DESC LIMIT 1",
        (chat_id,),
    )
    return await cursor.fetchone()


async def close_poll(poll_id: int) -> None:
    db = await get_db()
    await db.execute("UPDATE polls SET is_closed = 1 WHERE id = ?", (poll_id,))
    await db.commit()


async def get_poll_by_telegram_id(telegram_poll_id: str) -> aiosqlite.Row | None:
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM polls WHERE telegram_poll_id = ?", (telegram_poll_id,)
    )
    return await cursor.fetchone()


# --- Poll votes ---

async def upsert_poll_vote(
    telegram_poll_id: str,
    user_id: int,
    full_name: str | None,
    username: str | None,
    option_ids: list[int],
) -> None:
    db = await get_db()
    existing = await db.execute(
        "SELECT id FROM poll_votes WHERE telegram_poll_id = ? AND user_id = ?",
        (telegram_poll_id, user_id),
    )
    row = await existing.fetchone()
    option_ids_json = json.dumps(option_ids)

    if row:
        await db.execute(
            """
            UPDATE poll_votes
            SET full_name = ?, username = ?, option_ids = ?, voted_at = CURRENT_TIMESTAMP
            WHERE telegram_poll_id = ? AND user_id = ?
            """,
            (full_name, username, option_ids_json, telegram_poll_id, user_id),
        )
    else:
        await db.execute(
            """
            INSERT INTO poll_votes (telegram_poll_id, user_id, full_name, username, option_ids)
            VALUES (?, ?, ?, ?, ?)
            """,
            (telegram_poll_id, user_id, full_name, username, option_ids_json),
        )
    await db.commit()


async def get_poll_votes(telegram_poll_id: str) -> list[aiosqlite.Row]:
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM poll_votes WHERE telegram_poll_id = ?", (telegram_poll_id,)
    )
    return await cursor.fetchall()


# --- Ratings ---

async def add_rating(
    game_id: int,
    poll_id: int,
    user_id: int,
    full_name: str | None,
    username: str | None,
    score: int,
) -> None:
    db = await get_db()
    await db.execute(
        """
        INSERT INTO ratings (game_id, poll_id, user_id, full_name, username, score)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (game_id, poll_id, user_id, full_name, username, score),
    )
    await db.commit()
