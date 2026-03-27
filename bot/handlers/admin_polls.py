import json
import random
from datetime import datetime

from aiogram import Bot, Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.config import config
from bot.database import queries
from bot.filters.is_admin import IsAdmin
from bot.states.states import DayVoteStates, RatingStates, VoteManualStates
from bot.utils.formatters import (
    format_day_results,
    format_game_select_results,
    format_rating_results,
)

router = Router()

RU_WEEKDAYS = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
RU_MONTHS = {
    1: "янв", 2: "фев", 3: "мар", 4: "апр", 5: "май", 6: "июн",
    7: "июл", 8: "авг", 9: "сен", 10: "окт", 11: "ноя", 12: "дек",
}


# Отменяем FSM admin-флоу при любой команде
@router.message(
    StateFilter(
        VoteManualStates.waiting_for_game_ids,
        DayVoteStates.waiting_for_dates,
        RatingStates.waiting_for_game,
    ),
    F.text.startswith("/"),
)
async def admin_fsm_cancel_on_command(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Действие отменено. Повторите нужную команду.")


# --- /start_vote_random ---

@router.message(Command("start_vote_random"), IsAdmin())
async def cmd_start_vote_random(message: Message, bot: Bot) -> None:
    games = await queries.get_active_games()
    if not games:
        await message.answer("Список игр пуст. Добавьте игры командой /addgame")
        return

    open_poll = await queries.get_open_poll(config.group_chat_id)
    if open_poll:
        await message.answer("Уже есть активный опрос. Сначала закройте его командой /close_poll")
        return

    selected = random.sample(list(games), min(5, len(games)))
    options = [g["name"] for g in selected]
    options_map = {str(i): g["id"] for i, g in enumerate(selected)}

    sent = await bot.send_poll(
        chat_id=config.group_chat_id,
        question="В какую игру будем играть? 🎮",
        options=options,
        is_anonymous=False,
        allows_multiple_answers=True,
        message_thread_id=config.topic_thread_id,
    )
    await queries.create_poll(
        telegram_poll_id=sent.poll.id,
        message_id=sent.message_id,
        chat_id=config.group_chat_id,
        poll_type="game_select",
        options_map=options_map,
    )
    if message.chat.id != config.group_chat_id:
        await message.answer("Голосование запущено в группе ✅")


# --- /start_vote_manual ---

@router.message(Command("start_vote_manual"), IsAdmin())
async def cmd_start_vote_manual(message: Message, state: FSMContext) -> None:
    games = await queries.get_active_games()
    if not games:
        await message.answer("Список игр пуст. Добавьте игры командой /addgame")
        return

    lines = ["Выберите игры для голосования (введите номера через запятую или пробел):\n"]
    for i, g in enumerate(games, 1):
        lines.append(f"{i}. {g['name']}")

    await state.update_data(games=[dict(g) for g in games])
    await state.set_state(VoteManualStates.waiting_for_game_ids)
    await message.answer("\n".join(lines))


@router.message(VoteManualStates.waiting_for_game_ids, IsAdmin())
async def vote_manual_game_ids(message: Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    games = data["games"]

    raw = message.text.replace(",", " ").split()
    indices = []
    for token in raw:
        if token.isdigit():
            idx = int(token) - 1
            if 0 <= idx < len(games):
                indices.append(idx)

    indices = list(dict.fromkeys(indices))  # deduplicate preserving order

    if not indices:
        await message.answer("Не удалось распознать номера. Введите числа от 1 до " + str(len(games)))
        return

    if len(indices) > 10:
        await message.answer("Telegram позволяет максимум 10 вариантов в опросе. Выберите не более 10.")
        return

    open_poll = await queries.get_open_poll(config.group_chat_id)
    if open_poll:
        await state.clear()
        await message.answer("Уже есть активный опрос. Сначала закройте его командой /close_poll")
        return

    selected = [games[i] for i in indices]
    options = [g["name"] for g in selected]
    options_map = {str(i): g["id"] for i, g in enumerate(selected)}

    sent = await bot.send_poll(
        chat_id=config.group_chat_id,
        question="В какую игру будем играть? 🎮",
        options=options,
        is_anonymous=False,
        allows_multiple_answers=True,
        message_thread_id=config.topic_thread_id,
    )
    await queries.create_poll(
        telegram_poll_id=sent.poll.id,
        message_id=sent.message_id,
        chat_id=config.group_chat_id,
        poll_type="game_select",
        options_map=options_map,
    )
    await state.clear()
    if message.chat.id != config.group_chat_id:
        await message.answer("Голосование запущено в группе ✅")


# --- /start_rating ---

@router.message(Command("start_rating"), IsAdmin())
async def cmd_start_rating(message: Message, state: FSMContext) -> None:
    games = await queries.get_active_games()
    if not games:
        await message.answer("Список игр пуст.")
        return

    lines = ["Введите номер игры для рейтинга:\n"]
    for i, g in enumerate(games, 1):
        lines.append(f"{i}. {g['name']}")

    await state.update_data(games=[dict(g) for g in games])
    await state.set_state(RatingStates.waiting_for_game)
    await message.answer("\n".join(lines))


@router.message(RatingStates.waiting_for_game, IsAdmin())
async def rating_game_selected(message: Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    games = data["games"]

    text = message.text.strip() if message.text else ""
    if not text.isdigit():
        await message.answer("Введите номер игры из списка.")
        return

    idx = int(text) - 1
    if not (0 <= idx < len(games)):
        await message.answer(f"Введите номер от 1 до {len(games)}.")
        return

    game = games[idx]

    open_poll = await queries.get_open_poll(config.group_chat_id)
    if open_poll:
        await state.clear()
        await message.answer("Уже есть активный опрос. Сначала закройте его командой /close_poll")
        return

    options = [str(i) for i in range(1, 11)]
    options_map = {str(i): str(i + 1) for i in range(10)}

    sent = await bot.send_poll(
        chat_id=config.group_chat_id,
        question=f"Оцените игру «{game['name']}» от 1 до 10 ⭐",
        options=options,
        is_anonymous=False,
        allows_multiple_answers=False,
        message_thread_id=config.topic_thread_id,
    )
    await queries.create_poll(
        telegram_poll_id=sent.poll.id,
        message_id=sent.message_id,
        chat_id=config.group_chat_id,
        poll_type="rating",
        options_map=options_map,
        related_game_id=game["id"],
    )
    await state.clear()
    if message.chat.id != config.group_chat_id:
        await message.answer("Голосование запущено в группе ✅")


# --- /start_day_vote ---

@router.message(Command("start_day_vote"), IsAdmin())
async def cmd_start_day_vote(message: Message, state: FSMContext) -> None:
    await state.set_state(DayVoteStates.waiting_for_dates)
    await message.answer(
        "Введите даты через запятую в формате ДД.ММ\n"
        "Например: <code>25.02, 01.03, 07.03</code>",
        parse_mode="HTML",
    )


@router.message(DayVoteStates.waiting_for_dates, IsAdmin())
async def day_vote_dates(message: Message, state: FSMContext, bot: Bot) -> None:
    text = message.text.strip() if message.text else ""
    raw_dates = [d.strip() for d in text.replace(",", " ").split() if d.strip()]

    options = []
    options_map = {}
    current_year = datetime.now().year

    for raw in raw_dates:
        try:
            day, month = raw.split(".")
            day, month = int(day), int(month)
            dt = datetime(current_year, month, day)
            weekday = RU_WEEKDAYS[dt.weekday()]
            month_name = RU_MONTHS[month]
            label = f"{day} {month_name} ({weekday})"
            idx = str(len(options))
            options.append(label)
            options_map[idx] = label
        except (ValueError, KeyError):
            await message.answer(
                f"Не удалось распознать дату: <code>{raw}</code>\n"
                "Используйте формат ДД.ММ",
                parse_mode="HTML",
            )
            return

    if not options:
        await message.answer("Не введено ни одной даты.")
        return

    if len(options) > 10:
        await message.answer("Максимум 10 дат. Введите меньше вариантов.")
        return

    open_poll = await queries.get_open_poll(config.group_chat_id)
    if open_poll:
        await state.clear()
        await message.answer("Уже есть активный опрос. Сначала закройте его командой /close_poll")
        return

    sent = await bot.send_poll(
        chat_id=config.group_chat_id,
        question="Когда играем? 📅",
        options=options,
        is_anonymous=False,
        allows_multiple_answers=True,
        message_thread_id=config.topic_thread_id,
    )
    await queries.create_poll(
        telegram_poll_id=sent.poll.id,
        message_id=sent.message_id,
        chat_id=config.group_chat_id,
        poll_type="day_select",
        options_map=options_map,
    )
    await state.clear()
    if message.chat.id != config.group_chat_id:
        await message.answer("Голосование запущено в группе ✅")


# --- /close_poll ---

@router.message(Command("close_poll"), IsAdmin())
async def cmd_close_poll(message: Message, bot: Bot) -> None:
    poll_row = await queries.get_open_poll(config.group_chat_id)
    if not poll_row:
        await message.answer("Нет активных опросов.")
        return

    try:
        await bot.stop_poll(chat_id=config.group_chat_id, message_id=poll_row["message_id"])
    except Exception:
        pass  # poll may already be stopped

    await queries.close_poll(poll_row["id"])

    votes = await queries.get_poll_votes(poll_row["telegram_poll_id"])
    options_map: dict = json.loads(poll_row["options_map"])
    poll_type = poll_row["poll_type"]

    if poll_type == "game_select":
        named_map: dict[str, str] = {}
        for oid, game_id in options_map.items():
            game = await queries.get_game_by_id(int(game_id))
            named_map[oid] = game["name"] if game else f"Игра #{game_id}"
        result = format_game_select_results(poll_row, votes, named_map)

    elif poll_type == "rating":
        game_id = poll_row["related_game_id"]
        game = await queries.get_game_by_id(int(game_id)) if game_id else None
        game_name = game["name"] if game else "Неизвестная игра"

        for vote in votes:
            option_ids = json.loads(vote["option_ids"])
            if not option_ids:
                continue
            oid = str(option_ids[0])
            score = int(options_map.get(oid, 0))
            if 1 <= score <= 10:
                await queries.add_rating(
                    game_id=int(game_id),
                    poll_id=poll_row["id"],
                    user_id=vote["user_id"],
                    full_name=vote["full_name"],
                    username=vote["username"],
                    score=score,
                )

        result = format_rating_results(game_name, votes, options_map)

    elif poll_type == "day_select":
        result = format_day_results(votes, options_map)

    else:
        result = "Неизвестный тип опроса."

    # Результаты всегда в группу
    await bot.send_message(
        chat_id=config.group_chat_id,
        text=result,
        message_thread_id=config.topic_thread_id,
    )

    # Если admin писал из лички — подтверждаем там
    if message.chat.id != config.group_chat_id:
        await message.answer("Опрос закрыт, результаты отправлены в группу.")
