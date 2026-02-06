from aiogram.fsm.state import StatesGroup, State

class Form(StatesGroup):
    waiting_for_message = State()