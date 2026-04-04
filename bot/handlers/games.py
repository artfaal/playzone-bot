from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import ForceReply, Message

from bot.database import queries
from bot.filters.is_admin import IsAdmin
from bot.states.states import AddGameStates
from bot.utils.formatters import format_games_desc_chunks, format_games_list

router = Router()


@router.message(Command("games"))
async def cmd_games(message: Message) -> None:
    games = await queries.get_active_games()
    await message.answer(format_games_list(games))


@router.message(Command("games_desc"))
async def cmd_games_desc(message: Message) -> None:
    games = await queries.get_active_games()
    for chunk in format_games_desc_chunks(games):
        await message.answer(chunk, parse_mode="HTML")


@router.message(Command("addgame"))
async def cmd_addgame(message: Message, state: FSMContext) -> None:
    await state.set_state(AddGameStates.waiting_for_name)
    await message.answer(
        "Введите название игры:",
        reply_markup=ForceReply(selective=True),
    )


# /skip должен быть зарегистрирован ДО общего cancel-хендлера,
# иначе /skip тоже попадёт в cancel
@router.message(AddGameStates.waiting_for_description, Command("skip"))
async def addgame_skip_description(message: Message, state: FSMContext) -> None:
    await _save_game(message, state, description=None)


# Перехватываем любую команду во время FSM — иначе "/start_vote_random" сохранится как название игры
@router.message(
    StateFilter(AddGameStates.waiting_for_name, AddGameStates.waiting_for_description),
    F.text.startswith("/"),
)
async def addgame_cancel_on_command(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Добавление игры отменено. Повторите нужную команду.")


@router.message(AddGameStates.waiting_for_name)
async def addgame_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip() if message.text else ""
    if not name:
        await message.answer("Название не может быть пустым. Попробуйте ещё раз:")
        return

    existing = await queries.get_game_by_name(name)
    if existing:
        await state.clear()
        await message.answer(f"Игра «{name}» уже есть в списке.")
        return

    await state.update_data(name=name)
    await state.set_state(AddGameStates.waiting_for_description)
    await message.answer(
        "Введите описание игры (или отправьте /skip, чтобы пропустить):",
        reply_markup=ForceReply(selective=True),
    )


@router.message(AddGameStates.waiting_for_description)
async def addgame_description(message: Message, state: FSMContext) -> None:
    description = message.text.strip() if message.text else None
    await _save_game(message, state, description=description)


async def _save_game(message: Message, state: FSMContext, description: str | None) -> None:
    data = await state.get_data()
    name = data["name"]
    user = message.from_user
    await queries.add_game(
        name=name,
        description=description,
        added_by_id=user.id,
        added_by_username=user.username,
    )
    await state.clear()
    await message.answer(f"✅ Игра «{name}» добавлена в список!")


@router.message(Command("deletegame"), IsAdmin())
async def cmd_deletegame(message: Message) -> None:
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        await message.answer("Укажите название игры: /deletegame &lt;название&gt;", parse_mode="HTML")
        return

    name = args[1].strip()
    deleted = await queries.soft_delete_game(name)
    if deleted:
        await message.answer(f"🗑 Игра «{name}» удалена из списка.")
    else:
        await message.answer(f"Игра «{name}» не найдена в активном списке.")
