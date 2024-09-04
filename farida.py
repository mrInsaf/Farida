import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, Router, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.methods import EditMessageText
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, KeyboardButton, InlineKeyboardMarkup, CallbackQuery, ReplyKeyboardMarkup
from aiogram.types.web_app_info import WebAppInfo
from aiogram import F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.methods.send_message import SendMessage
from aiogram.types import FSInputFile
import sqlite3
from datetime import date

from misc.plot_grades_by_zveno import send_plot
from states import *
from models import *
from add_group import *
from show_grades import *
from MarkTypes import mark_types
from authorised_users import authorised_users
from crypt import *
from misc.show_lists import *

import sys
import os

# Получаем путь к текущему каталогу
current_dir = os.path.dirname(os.path.realpath(__file__))

# Добавляем текущий каталог в sys.path
sys.path.append(current_dir)

TEST_TOKEN = "6748840687:AAEah69Bw4LUvpc43bcGA_Hr19_u98TZiJo"
MAIN_TOKEN = '6910756464:AAEWeQXTtuNnDHG3XrLIYDBC42ziAr7LfU8'

# TOKEN = '6910756464:AAEWeQXTtuNnDHG3XrLIYDBC42ziAr7LfU8'
dp = Dispatcher()

bot = None

logging.basicConfig(filename='app.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

max_scores = {
    "sem": 8,
    "conspect": 8,
    "srs": 8,
    "doklad": 8,
    "presentation": 10,
    "bashvat": 10,
    "test": 8,
    "exam": 40,
    "z_contr": 30,
    "z_sem": 6,
    "z_test": 6,
    "z_cross": 4,
    "shtraf": 0
}

keyboard_events = [
    "exam",
    "z_contr",
    "z_sem",
    "z_test",
    "z_cross",
]


@dp.callback_query(F.data == "to_start")
@dp.callback_query(F.data == "back", Rate.zveno_choose)
@dp.callback_query(F.data == "back", ShowGrades.choose_group)
@dp.callback_query(F.data == "back", CreateEvent.choose_type)
@dp.callback_query(F.data == "back", RateVisit.choose_group)
@dp.callback_query(F.data == "back", PlotGrades.choose_group)
async def start_command(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(StartState.start_state)
    kb = create_kb()
    kb.add(
        InlineKeyboardButton(text="Выставить оценку", callback_data="rate"),
        InlineKeyboardButton(text="Выставить посещение", callback_data="rate_visit"),
        InlineKeyboardButton(text="Посмотреть оценки", callback_data="show_grades"),
        InlineKeyboardButton(text="Построить график оценок по звеньям", callback_data="plot_grades_by_zveno"),
        InlineKeyboardButton(text="Создать событие", callback_data="create_event"),
        InlineKeyboardButton(text="Добавить группу", callback_data="add_group"),
        InlineKeyboardButton(text="Выйти", callback_data="exit"),
    )
    kb.adjust(1)
    await callback.message.answer(text="Выберите действие", reply_markup=kb.as_markup())


@dp.message(StartState.start_state)
@dp.message(Command('start'))
async def start_command(message: types.Message, state: FSMContext):
    kb = InlineKeyboardBuilder()
    teacher_id = message.from_user.id
    if not check_teacher_exists(teacher_id):
        kb.add(
            InlineKeyboardButton(text="Зарегистрироваться", callback_data="register"),
        )
    else:
        if not check_auth_by_teacher_id(teacher_id):
            kb.add(
                InlineKeyboardButton(text="Войти", callback_data="login")
            )
        else:
            await state.set_state(StartState.start_state)

            kb.add(
                InlineKeyboardButton(text="Выставить оценку", callback_data="rate"),
                InlineKeyboardButton(text="Выставить посещение", callback_data="rate_visit"),
                InlineKeyboardButton(text="Посмотреть оценки", callback_data="show_grades"),
                InlineKeyboardButton(text="Построить график оценок по звеньям", callback_data="plot_grades_by_zveno"),
                InlineKeyboardButton(text="Создать событие", callback_data="create_event"),
                InlineKeyboardButton(text="Добавить группу", callback_data="add_group"),
                InlineKeyboardButton(text="Выйти", callback_data="exit"),
            )

            if message.from_user.id == 816831722:
                kb.add(
                    InlineKeyboardButton(text="Посмотреть логи", callback_data="export_logs"),
                )
            kb.adjust(1)
    await message.answer(text="Выберите действие", reply_markup=kb.as_markup())


@dp.callback_query(F.data == "export_logs")
async def export_logs(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer_document(FSInputFile("nohup.out"))
    await callback.message.answer_document(FSInputFile("app.log"))


@dp.callback_query(F.data == "rate")
@dp.callback_query(F.data == "back", Rate.student_choose)
async def rate_student_start(callback: CallbackQuery, state: FSMContext):
    await show_groups_list(callback)
    await state.set_state(Rate.zveno_choose)


@dp.callback_query(Rate.zveno_choose)
@dp.callback_query(F.data == "back", Rate.event_choose)
async def rate_zveno_choose(callback: CallbackQuery, state: FSMContext):
    await show_zveno_list(callback, state)
    await state.set_state(Rate.student_choose)


@dp.callback_query(F.data == "choose_another_student")
@dp.callback_query(F.data == "back", Rate.mark_choose)
@dp.callback_query(Rate.student_choose)
async def rate_student_choose(callback: CallbackQuery, state: FSMContext):
    await show_students_list(callback, state)
    await state.set_state(Rate.event_choose)


@dp.callback_query(Rate.event_choose)
@dp.callback_query(F.data == "back", Rate.finish)
async def rate_event_choose(callback: CallbackQuery, state: FSMContext):
    print("Выбор студента")
    await show_event_list(callback, state, False)
    await state.set_state(Rate.mark_choose)


@dp.callback_query(Rate.mark_choose)
async def rate_mark_choose(callback: CallbackQuery, state: FSMContext):
    print("Выбор ивента")
    kb = create_kb()
    data = await state.get_data()
    event_id = callback.data
    event_type = select_event_type_by_id(event_id)
    if check_grade_for_event_by_student(event_id, data['student']):
        kb = InlineKeyboardBuilder(
            [
                [InlineKeyboardButton(text="Выбрать студента", callback_data="choose_another_student")],
                [InlineKeyboardButton(text="В начало", callback_data="to_start")]
            ]
        )
        await callback.message.answer(text=f"У студента {data['student'].surname} уже есть оценка "
                                           f"за {select_event_by_id(int(event_id))}",
                                      reply_markup=kb.as_markup())
    else:
        await state.update_data(event=event_id)
        if event_type not in keyboard_events:
            if event_type == "shtraf":
                marks_list = [-1, -3, -5]
            else:
                marks_list = [1, 2, 3]
            for mark in marks_list:
                kb.add(
                    InlineKeyboardButton(text=str(mark), callback_data=str(mark))
                )
            kb.adjust(1)
            await callback.message.answer(text="Выберите оценку", reply_markup=kb.as_markup())
            await state.set_state(Rate.finish)
        else:
            await state.set_state(Rate.keyboard)
            await keyboard(callback, state)


@dp.callback_query(Rate.keyboard)
async def keyboard(callback: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardBuilder()
    # Добавляем кнопки от 0 до 9 и кнопку "Ввод"
    for i in range(1, 10):
        kb.add(InlineKeyboardButton(text=str(i), callback_data=f"{str(i)}"))
    kb.add(InlineKeyboardButton(text="0", callback_data="0"))
    input_button = InlineKeyboardButton(text="Ввод", callback_data="Enter")
    kb.add(input_button)
    kb.adjust(3)
    await callback.message.answer("Цифровая клавиатура", reply_markup=kb.as_markup())
    await state.update_data(number="")
    await state.set_state(Rate.keyboard_finish)


@dp.callback_query(Rate.keyboard_finish)
async def handle_digits(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    number = data["number"]
    if callback.data != "Enter":
        number += callback.data
        await state.update_data(number=number)
    else:
        await callback.message.answer(text=f"Вы ввели {number}")
        await state.update_data(number="")
        await state.update_data(mark=number)
        await state.set_state(Rate.finish)
        await rate_finish(callback, state)


@dp.callback_query(Rate.finish)
async def rate_finish(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    student = data['student']
    if callback.data != "Enter":
        mark = callback.data
    else:
        mark = data['mark']
    kb = InlineKeyboardBuilder(
        [
            [InlineKeyboardButton(text="Выбрать студента", callback_data="choose_another_student")],
            [InlineKeyboardButton(text="В начало", callback_data="to_start")]
        ]
    )

    event_score = calculate_score_of_student_by_event_type(data['student'], data['event'])
    event_type = select_event_type_by_id(data['event'])
    if int(event_score) + int(mark) > max_scores[event_type]:
        await callback.message.answer(
            text=f"Выбранный балл {mark} + накопленный балл {event_score} "
                 f"превышает максимальный за тип {event_type} ({max_scores[event_type]} для {student}"
                 f")",
            reply_markup=kb.as_markup()
        )
        await state.set_state(StartState.start_state)
    else:
        event = select_event_by_id(data['event'])
        insert("grades", [data['student'].id, mark, data['event']])
        total_grade = select_total_grade_by_student(student.id)
        await callback.message.answer(
            text=f"Выставлена оценка\nСтудент: {data['student']}\nСобытие: {mark_types[event[0]]} {event[1]}\nОценка: "
                 f"{mark}\nОбщая сумма баллов: {total_grade}",
            reply_markup=kb.as_markup()
        )


@dp.callback_query(F.data == "create_event")
async def create_event_start(callback: CallbackQuery, state: FSMContext):
    kb = create_kb()
    for mark_type in mark_types:
        kb.add(InlineKeyboardButton(
            text=mark_types[mark_type],
            callback_data=mark_type
        ))
    kb.adjust(1)
    await callback.message.answer(text="Выберите тип события", reply_markup=kb.as_markup())
    await state.set_state(CreateEvent.choose_type)


@dp.callback_query(CreateEvent.choose_type)
async def create_event_choose_type(callback: CallbackQuery, state: FSMContext):
    await state.update_data(type=callback.data)
    kb = [
        [KeyboardButton(text="Сегодня")]
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Дата события"
    )
    await callback.message.answer(text="Введите дату в формате дд.мм.гггг", reply_markup=keyboard)
    await state.set_state(CreateEvent.choose_date)


@dp.message(CreateEvent.choose_date)
async def create_event_choose_date(message: types.Message, state: FSMContext):
    date_string = message.text.title()
    if date_string != "Сегодня":
        try:
            parsed_date = datetime.strptime(date_string, "%d.%m.%Y")
            # TODO Сделать перевод в корректный формат для MYSQL
            await state.update_data(date=parsed_date)
            await state.set_state(CreateEvent.finish)
            await create_event_finish(message, state)
        except Exception as ex:
            print(ex)
            await message.answer(text="Неправильная дата.\nВведите дату в формате дд.мм.гггг")
    else:
        print("Сегодня")
        _date = date.today()
        await state.update_data(date=_date)
        await state.set_state(CreateEvent.finish)
        await create_event_finish(message, state)


@dp.message(CreateEvent.finish)
async def create_event_finish(message: types.Message, state: FSMContext):
    data = await state.get_data()
    input_date = data['date']
    norm_date = input_date.strftime("%d.%m.%Y")
    print(f"data is: {data}")
    print(f"norm_date is: {norm_date}")
    insert("events", [data['type'], data['date'], message.from_user.id])
    await message.answer(text=f"Событие {mark_types[data['type']]}, {norm_date} добавлено. Нажмите /start")
    await state.set_state(StartState.start_state)


@dp.callback_query(F.data == "add_group")
async def add_group_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(text="Отправьте файл со списком группы")
    await state.set_state(AddGroup.input_group_name)


@dp.message(AddGroup.input_group_name)
async def add_group_input_group_name(message: Message, state: FSMContext, bot: Bot):
    teacher_id = message.from_user.id
    document = message.document
    file_id = document.file_id
    file_name = document.file_name

    if file_name.endswith('.txt'):
        # Скачиваем файл
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path
        downloaded_file = await bot.download_file(file_path)

        with open(f'./{file_name}', 'wb') as new_file:
            new_file.write(downloaded_file.read())

        insert_group(file_name[:-4], file_name, teacher_id)
        await message.answer(text=f"Группа {file_name[:-4]} добавлена. Нажмите /start")
    else:
        await message.answer(text=f"Что-то пошло не так")


@dp.callback_query(F.data == "show_grades")
async def show_grades_start(callback: CallbackQuery, state: FSMContext):
    await show_groups_list(callback)
    await state.set_state(ShowGrades.choose_group)


@dp.callback_query(F.data != "back", ShowGrades.choose_group)
async def show_grades_choose_group(callback: CallbackQuery, state: FSMContext):
    kb = create_kb()
    for i, month in enumerate(months):
        kb.add(InlineKeyboardButton(text=month, callback_data=str(i + 1)))
    kb.adjust(1, 3)
    group = callback.data
    await state.update_data(group=group)
    await callback.message.answer(text="Выберите месяц", reply_markup=kb.as_markup())
    await state.set_state(ShowGrades.choose_month)


@dp.callback_query(ShowGrades.choose_month)
async def show_grades_finish(callback: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardBuilder(
        [
            [InlineKeyboardButton(text="В начало", callback_data="to_start")]
        ]
    )
    month = callback.data
    data = await state.get_data()
    group = data['group']
    summary_path = create_grades_table_of_group(group, month)
    file = FSInputFile(summary_path)
    await callback.message.answer_document(file, reply_markup=kb.as_markup())


@dp.callback_query(F.data == "register")
async def register(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(text="Придумайте и введите пароль")
    await state.set_state(Registration.input_password)


@dp.message(Registration.input_password)
async def confirm_password(message: Message, state: FSMContext):
    await state.update_data(password=message.text)
    await message.answer(text="Повторите пароль")
    await state.set_state(Registration.confirm_password)


@dp.message(Registration.confirm_password)
async def registration_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    password = data['password']
    if message.text == password:
        ecnrypted_password = encrypt_password(password)
        register_teacher(message.from_user.id, ecnrypted_password)
        await message.answer(text="Успешная регистрация. Нажмите /start")
    else:
        await message.answer(text="Пароли не совпадают, введите еще раз")


@dp.callback_query(F.data == "login")
async def login(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(text="Введите пароль")
    await state.set_state(Login.password)


@dp.message(Login.password)
async def login_input_password(message: Message, state: FSMContext):
    teacher_id = message.from_user.id
    hashed_password = get_hashed_password(teacher_id)
    if check_password(message.text, hashed_password):
        authorise_teacher(teacher_id)
        await message.answer(text="Успешный вход, нажмите /start")
        await state.set_state(StartState.start_state)
    else:
        await message.answer(text="Неверный пароль, попробуйте еще раз")


@dp.callback_query(F.data == "exit")
async def exit(callback: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="Нет", callback_data="no"))
    kb.add(InlineKeyboardButton(text="Да", callback_data="yes"))
    kb.adjust(1)
    await callback.message.answer(text="Точно выйти?", reply_markup=kb.as_markup())
    await state.set_state(Exit.exit)


@dp.callback_query(Exit.exit)
async def logout(callback: CallbackQuery, state: FSMContext):
    if callback.data == "yes":
        unauthorise_teacher(callback.from_user.id)
        await callback.message.answer(text="Успешный выход, нажмите /start")


@dp.callback_query(F.data == "rate_visit")
@dp.callback_query(F.data == "back", RateVisit.choose_zveno)
async def rate_visit_start(callback: CallbackQuery, state: FSMContext):
    await show_event_list(callback, state, True)
    await state.set_state(RateVisit.choose_group)


@dp.callback_query(RateVisit.choose_group)
@dp.callback_query(F.data == "back", RateVisit.show_student_list)
async def rate_visit_choose_group(callback: CallbackQuery, state: FSMContext):
    await state.update_data(event_id=callback.data)
    await show_groups_list(callback)
    await state.set_state(RateVisit.choose_zveno)


@dp.callback_query(F.data == "choose_zveno")
@dp.callback_query(RateVisit.choose_zveno)
@dp.callback_query(F.data == "back", RateVisit.choose_student)
async def rate_visit_choose_zveno(callback: CallbackQuery, state: FSMContext):
    await show_zveno_list(callback, state)
    await state.update_data(visited_list=[])
    await state.set_state(RateVisit.show_student_list)


@dp.callback_query(RateVisit.show_student_list)
async def rate_visit_show_student_list(callback: CallbackQuery, state: FSMContext):
    kb = [
        [KeyboardButton(text="Подтвердить")]
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Для подтверждения списка студентов нажмите 'Подтвердить'"
    )
    await show_students_list(callback, state, "посетивших студентов")
    await callback.message.answer("Посетили занятие", reply_markup=keyboard)
    msg_id = await callback.message.answer("Студенты: ")
    await state.update_data(msg_id=msg_id.message_id)
    await state.set_state(RateVisit.choose_student)


@dp.callback_query(RateVisit.choose_student)
async def rate_visit_choose_student(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    msg_id = data.get("msg_id")

    visited_list = data.get("visited_list")
    visited_student = callback.data
    if visited_student != "back":
        if visited_student not in visited_list:
            visited_list.append(visited_student)
        else:
            visited_list.remove(visited_student)
        visited_list_text = "Студенты:\n" + "\n".join(visited_list)
        await state.update_data(visited_list=visited_list)
        await bot(EditMessageText(text=visited_list_text, chat_id=callback.from_user.id, message_id=msg_id))


@dp.message(RateVisit.choose_student)
async def rate_visit_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    group_id = data['group']
    visited_list: list = data.get("visited_list")
    event = select_event_by_id(data['event_id'])

    for student_text in visited_list:
        student = find_student_by_surname_and_group_id(student_text, group_id)
        print(student)
        if not check_grade_for_event_by_student(data['event_id'], student):
            await message.answer(text=f"Студенту {student.surname} выставлена оценка за {event[0]} {event[1]}")
            insert("grades", [student.id, 1, data['event_id']])
        else:
            await message.answer(text=f"У студента {student.surname} уже есть оценка за {event[0]} {event[1]}")

    kb = InlineKeyboardBuilder()
    buttons = [
        InlineKeyboardButton(text="Выбрать звено", callback_data="choose_zveno"),
        InlineKeyboardButton(text="В начало", callback_data="to_start"),
    ]
    for button in buttons:
        kb.add(button)
    await message.answer(text="Выберите следующее действие", reply_markup=kb.as_markup())
    await state.set_state(RateVisit.finish)


@dp.callback_query(F.data == "plot_grades_by_zveno")
async def plot_grades_start(callback: CallbackQuery, state: FSMContext):
    await show_groups_list(callback)
    await state.set_state(PlotGrades.choose_group)


@dp.callback_query(PlotGrades.choose_group)
async def plot_grades_plot(callback: CallbackQuery, state: FSMContext):
    group = callback.data
    grouped_students = await group_students_into_zveno(group, state)
    print(group)
    await send_plot(callback, grouped_students, group)


async def main(token: str) -> None:
    global bot
    if token == "test":
        bot = Bot(token=TEST_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        await dp.start_polling(bot)
    else:
        bot = Bot(token=MAIN_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        await dp.start_polling(bot)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python farida.py <token>")
    else:
        try:
            TOKEN = sys.argv[1]
            asyncio.run(main(TOKEN))
        except Exception as e:
            logging.exception(f"Произошла ошибка: {e}")
            print(f"Произошла ошибка: {e}")

# async def main(token: str) -> None:
#     global bot
#     bot = Bot(TEST_TOKEN, parse_mode=ParseMode.HTML)
#     await dp.start_polling(bot)
#
#
# if __name__ == "__main__":
#     TOKEN = TEST_TOKEN
#     asyncio.run(main(TOKEN))
