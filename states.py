from aiogram.fsm.state import State
from aiogram.fsm.state import StatesGroup


class Keyboard(StatesGroup):
    keyboard = State()

class StartState(StatesGroup):
    start_state = State()


class Registration(StatesGroup):
    input_password = State()
    confirm_password = State()


class Login(StatesGroup):
    login = State()
    password = State()


class Exit(StatesGroup):
    exit = State()


class Rate(StatesGroup):
    # student_input = State()
    group_input = State()
    zveno_choose = State()
    student_choose = State()
    event_choose = State()
    mark_choose = State()
    keyboard = State()
    keyboard_finish = State()
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


