from aiogram.fsm.state import State
from aiogram.fsm.state import StatesGroup


class StartState(StatesGroup):
    start_state = State()


class Rate(StatesGroup):
    # student_input = State()
    group_input = State()
    zveno_choose = State()
    student_choose = State()
    event_choose = State()
    mark_choose = State()
    finish = State()


class AddGroup(StatesGroup):
    input_group_name = State()
    finish = State()


class CreateEvent(StatesGroup):
    choose_type = State()
    choose_date = State()
    finish = State()


class ShowGrades(StatesGroup):
    choose_month = State()
    choose_group = State()


