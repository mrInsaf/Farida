from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from MarkTypes import mark_types
from db import *


def create_kb():
    kb = InlineKeyboardBuilder()
    cancel_button = InlineKeyboardButton(text="Назад", callback_data=f'back', )
    kb.add(cancel_button)
    return kb


async def group_students_into_zveno(group, state) -> list:
    students = select_students_by_group_id(group)
    group_size = 4
    grouped_students = [students[i:i + group_size] for i in range(0, len(students), group_size)]
    await state.update_data(grouped_students=grouped_students)
    return grouped_students


async def show_student_list(message: Message) -> bool:
    student_list = find_student_by_surname_and_group_id(message.text)
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

    teacher_id = callback.from_user.id
    print(teacher_id)
    groups = select_groups_by_teacher_id(teacher_id)
    for group in groups:
        kb.add(InlineKeyboardButton(text=group[0], callback_data=str(group[1])))
    kb.adjust(1)
    await callback.message.answer(text="Выберите группу", reply_markup=kb.as_markup())


async def show_zveno_list(callback: CallbackQuery, state: FSMContext):
    kb = create_kb()
    if callback.data != "back" and callback.data != "choose_zveno":
        group = callback.data
        await state.update_data(group=group)
    else:
        data = await state.get_data()
        group = data['group']

    grouped_students = await group_students_into_zveno(group, state)

    for i in range(len(grouped_students)):
        kb.add(InlineKeyboardButton(text=f"Звено {i + 1}", callback_data=str(i)))
    kb.adjust(1)
    await callback.message.answer(text="Выберите звено", reply_markup=kb.as_markup())


async def show_students_list(callback: CallbackQuery, state: FSMContext, text: str = "студента"):
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
    await callback.message.answer(text=f"Выберите {text}", reply_markup=kb.as_markup())


async def show_event_list(callback: CallbackQuery, state: FSMContext, visit: bool):
    kb = create_kb()
    data = await state.get_data()

    if callback.data != "back":
        if not visit:
            group_id = data['group']
            student = find_student_by_surname_and_group_id(callback.data, group_id)
            print(f"student: {student}")
            await state.update_data(student=student)

    events = select_all_events_by_teacher_id(callback.from_user.id)
    print(f"events: {events}")

    current_date = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    upcoming_events = [event for event in events if event[2] >= current_date.date()]

    for event in upcoming_events:
        btn_text = f"{event[2]} {mark_types[event[1]]}"
        callback_data = str(event[0])
        kb.add(
            InlineKeyboardButton(text=btn_text, callback_data=callback_data)
        )
        print(f"Добавил кнопку")
    kb.adjust(1)
    await callback.message.answer(text="Выберите оцениваемое событие", reply_markup=kb.as_markup())
