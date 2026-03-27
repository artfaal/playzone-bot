from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from bot.config import config


class TopicFilterMiddleware(BaseMiddleware):
    """Пропускает только сообщения из указанного топика (или из личных чатов)."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if config.topic_thread_id is None:
            return await handler(event, data)

        if isinstance(event, Message):
            # Личные чаты пропускаем — админ может управлять из ЛС
            if event.chat.type == "private":
                return await handler(event, data)

            # В группе пропускаем только сообщения из нужного топика
            if event.message_thread_id != config.topic_thread_id:
                return  # молча игнорируем

        return await handler(event, data)
