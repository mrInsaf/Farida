import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, KeyboardButton, InlineKeyboardMarkup, CallbackQuery, ReplyKeyboardMarkup
from aiogram.types.web_app_info import WebAppInfo
from aiogram import F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.methods.send_message import SendMessage
from aiogram.types import FSInputFile
import sqlite3
import datetime

from states import *
from db import *
from models import *
from add_group import *
from show_grades import *

import sys
import os

# Получаем путь к текущему каталогу
current_dir = os.path.dirname(os.path.realpath(__file__))

# Добавляем текущий каталог в sys.path
sys.path.append(current_dir)

# TEST_TOKEN = "6748840687:AAEah69Bw4LUvpc43bcGA_Hr19_u98TZiJo"
# MAIN_TOKEN = '6910756464:AAEWeQXTtuNnDHG3XrLIYDBC42ziAr7LfU8'

TOKEN = '6748840687:AAEah69Bw4LUvpc43bcGA_Hr19_u98TZiJo'
dp = Dispatcher()

mark_types = {
    "sem": "Посещение",
    "conspect": "Конспект",
    "srs": "СРС",
    "doklad": "Доклад",
    "presentation": "Презентация",
    "bashvat": "Головоломка",
    "test": "Тестирование",
    "exam": "Экзамен",
    "z_contr": "Заоч Контр",
    "z_sem": "Заоч Семинар",
    "z_test": "Заоч Тест",
    "z_cross": "Заоч Кросс",
    "shtraf": "Штраф",
}

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


def create_kb():
    kb = InlineKeyboardBuilder()
    cancel_button = InlineKeyboardButton(text="Назад", callback_data=f'back', )
    kb.add(cancel_button)
    return kb


async def show_student_list(message: Message) -> bool:
    student_list = find_student_by_surname(message.text)
    kb = create_kb()
    if not student_list:
        await message.answer(text="Такой студент не найден, попробуйте еще раз", reply_markup=kb.as_markup())
    else:
        for student in student_list:
            str_lst = [str(element) for element in student]
            student_string = ' '.join(str_lst)
            kb.add(InlineKeyboardButton(text=student_string, callback_data=student_string))
            kb.adjust(1)
            await message.answer(
                text="Найдены следующие студенты",
                reply_markup=kb.as_markup()
            )
            return True


async def show_groups_list(callback: CallbackQuery):
    kb = create_kb()
    groups = select_groups_from_db()
    for group in groups:
        kb.add(InlineKeyboardButton(text=group[0], callback_data=group[0]))
    kb.adjust(1)
    await callback.message.answer(text="Выберите группу", reply_markup=kb.as_markup())


@dp.callback_query(F.data == "to_start")
@dp.callback_query(F.data == "back",
                   Rate.zveno_choose,
                   )
async def start_command(callback: types.CallbackQuery, state: FSMContext):
    print(await state.get_state())
    await state.set_state(StartState.start_state)
    kb = create_kb()
    kb.add(
        InlineKeyboardButton(text="Выставить оценку", callback_data="rate"),
        InlineKeyboardButton(text="Посмотреть оценки", callback_data="show_grades"),
        InlineKeyboardButton(text="Создать событие", callback_data="create_event"),
        InlineKeyboardButton(text="Добавить группу", callback_data="add_group"),
    )
    kb.adjust(1)
    await callback.message.answer(text="Выберите действие", reply_markup=kb.as_markup())


@dp.message(StartState.start_state)
@dp.message(Command('start'))
async def start_command(message: types.Message, state: FSMContext):
    await state.set_state(StartState.start_state)
    kb = create_kb()
    kb.add(
        InlineKeyboardButton(text="Выставить оценку", callback_data="rate"),
        InlineKeyboardButton(text="Посмотреть оценки", callback_data="show_grades"),
        InlineKeyboardButton(text="Создать событие", callback_data="create_event"),
        InlineKeyboardButton(text="Добавить группу", callback_data="add_group"),
    )
    kb.adjust(1)
    await message.answer(text="Выберите действие", reply_markup=kb.as_markup())
    print(await state.get_state())


@dp.callback_query(F.data == "rate")
@dp.callback_query(F.data == "back", Rate.student_choose)
async def rate_student_start(callback: CallbackQuery, state: FSMContext):
    await show_groups_list(callback)
    await state.set_state(Rate.zveno_choose)


@dp.callback_query(Rate.zveno_choose)
@dp.callback_query(F.data == "back", Rate.event_choose)
async def rate_zveno_choose(callback: CallbackQuery, state: FSMContext):
    kb = create_kb()
    if callback.data != "back":
        group = callback.data
        await state.update_data(group=group)
    else:
        data = await state.get_data()
        group = data['group']

    students = select_students_by_group(group)
    group_size = 4
    grouped_students = [students[i:i + group_size] for i in range(0, len(students), group_size)]
    await state.update_data(grouped_students=grouped_students)

    for i in range(len(grouped_students)):
        kb.add(InlineKeyboardButton(text=f"Звено {i + 1}", callback_data=str(i)))
    kb.adjust(1)
    await callback.message.answer(text="Выберите звено", reply_markup=kb.as_markup())
    await state.set_state(Rate.student_choose)


@dp.callback_query(F.data == "choose_another_student")
@dp.callback_query(F.data == "back", Rate.mark_choose)
@dp.callback_query(Rate.student_choose)
async def rate_student_choose(callback: CallbackQuery, state: FSMContext):
    kb = create_kb()
    data = await state.get_data()
    if callback.data != "choose_another_student" and callback.data != "back":
        zveno = int(callback.data)
        await state.update_data(zveno=zveno)
    else:
        zveno = data['zveno']
    grouped_students = data['grouped_students']

    for student in grouped_students[zveno]:
        kb.add(InlineKeyboardButton(text=student, callback_data=student))
    kb.adjust(1)
    await callback.message.answer(text="Выберите студента", reply_markup=kb.as_markup())
    await state.set_state(Rate.event_choose)


@dp.callback_query(Rate.event_choose)
@dp.callback_query(F.data == "back", Rate.finish)
async def rate_event_choose(callback: CallbackQuery, state: FSMContext):
    kb = create_kb()
    print(callback.data)

    if callback.data != "back":
        student = find_student_by_surname(callback.data)
        await state.update_data(student=student)

    events = select_all_events()

    current_date = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    print(current_date)
    upcoming_events = [event for event in events if datetime.datetime.strptime(event[2], "%d.%m.%Y") >= current_date]

    for event in upcoming_events:
        btn_text = f"{event[2]} {mark_types[event[1]]}"
        callback_data = str(event[0])
        kb.add(
            InlineKeyboardButton(text=btn_text, callback_data=callback_data)
        )
    kb.adjust(1)
    await callback.message.answer(text="Выберите оцениваемое событие", reply_markup=kb.as_markup())
    await state.set_state(Rate.mark_choose)


@dp.callback_query(Rate.mark_choose)
async def rate_mark_choose(callback: CallbackQuery, state: FSMContext):
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
        print(event_type)
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
    print('yo')
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
        print(number)
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
                 f"превышает максимальный за тип {event_type} ({max_scores[event_type]})",
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
            datetime.datetime.strptime(date_string, "%d.%m.%Y")
            await state.update_data(date=date_string)
            await state.set_state(CreateEvent.finish)
            await create_event_finish(message, state)
        except Exception as ex:
            print(ex)
            await message.answer(text="Неправильная дата.\nВведите дату в формате дд.мм.гггг")
    else:
        date = datetime.date.today()
        await state.update_data(date=date.strftime("%d.%m.%Y"))
        await state.set_state(CreateEvent.finish)
        await create_event_finish(message, state)


@dp.message(CreateEvent.finish)
async def create_event_finish(message: types.Message, state: FSMContext):
    data = await state.get_data()
    insert("events", [data['type'], data['date']])
    await message.answer(text=f"Событие {mark_types[data['type']]}, {data['date']} добавлено")
    await state.set_state(StartState.start_state)


@dp.callback_query(F.data == "add_group")
async def add_group_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(text="Отправьте файл со списком группы")
    await state.set_state(AddGroup.input_group_name)


@dp.message(AddGroup.input_group_name)
async def add_group_input_group_name(message: Message, state: FSMContext, bot: Bot):
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

        insert_group(file_name[:-4], file_name)
        await message.answer(text=f"Группа {file_name[:-4]} добавлена")
    else:
        await message.answer(text=f"Что-то пошло не так")


@dp.callback_query(F.data == "show_grades")
async def show_grades_start(callback: CallbackQuery, state: FSMContext):
    await show_groups_list(callback)
    await state.set_state(ShowGrades.choose_group)


@dp.callback_query(ShowGrades.choose_group)
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


async def main() -> None:
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    await dp.start_polling(bot)


if __name__ == "__main__":
    # logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
