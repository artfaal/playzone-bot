from aiogram import Router
from aiogram.types import PollAnswer

from bot.database import queries

router = Router()


@router.poll_answer()
async def on_poll_answer(poll_answer: PollAnswer) -> None:
    poll_row = await queries.get_poll_by_telegram_id(poll_answer.poll_id)
    if poll_row is None:
        return

    user = poll_answer.user
    full_name = " ".join(filter(None, [user.first_name, user.last_name])) or None

    await queries.upsert_poll_vote(
        telegram_poll_id=poll_answer.poll_id,
        user_id=user.id,
        full_name=full_name,
        username=user.username,
        option_ids=list(poll_answer.option_ids),
    )
