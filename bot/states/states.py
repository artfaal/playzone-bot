from aiogram.fsm.state import State, StatesGroup


class AddGameStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()


class VoteManualStates(StatesGroup):
    waiting_for_game_ids = State()


class DayVoteStates(StatesGroup):
    waiting_for_dates = State()


class RatingStates(StatesGroup):
    waiting_for_game = State()
