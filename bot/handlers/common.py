from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

HELP_TEXT = """
/start — Приветствие
/help — Список команд
/addgame — Добавить игру в список
/games — Показать список игр с рейтингом
/games_desc — Показать игры с описаниями

<b>Команды для администраторов:</b>
/deletegame &lt;название&gt; — Удалить игру
/start_vote_random — Голосование: 5 случайных игр
/start_vote_manual — Голосование: выбрать игры из списка
/start_rating — Голосование: рейтинг игры (1–10)
/start_day_vote — Голосование: выбор даты
/close_poll — Закрыть текущий опрос и показать итоги
""".strip()


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    name = message.from_user.first_name if message.from_user else "друг"
    await message.answer(
        f"Привет, {name}! 👋\n\n"
        "Я помогаю организовывать игровые сессии: голосования за игры, даты и рейтинги.\n\n"
        f"{HELP_TEXT}",
        parse_mode="HTML",
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT, parse_mode="HTML")
