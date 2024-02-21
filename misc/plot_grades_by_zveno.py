import os

from aiogram.types import FSInputFile, CallbackQuery
from matplotlib import pyplot as plt
from db import select_grades_by_group_id, select_group_name_by_id


def calculate_total_scores(data):
    total_scores = {}  # Словарь для хранения суммарных оценок

    for item in data:
        student_name, score, _, _ = item
        score = int(score)  # Преобразуем оценку в целое число
        if student_name in total_scores:
            total_scores[student_name] += score
        else:
            total_scores[student_name] = score

    return total_scores


def create_and_save_plot(grouped_students: list, group_id: str):
    grades_of_group = select_grades_by_group_id(group_id)
    if len(grades_of_group) == 0:
        return 0
    total_grades = calculate_total_scores(grades_of_group)

    grades_by_zveno = {}
    for i, zveno in enumerate(grouped_students):
        grades_by_zveno[i] = 0
        for student in zveno:
            if student in total_grades.keys():
                grades_by_zveno[i] += total_grades[student]
    zvenos = list(grades_by_zveno.keys())
    plt.bar(zvenos, list(grades_by_zveno.values()), color='skyblue')

    group_name = select_group_name_by_id(group_id)
    plt.xlabel('Звено')
    plt.ylabel('Суммарная оценка')
    plt.title(f'Суммарные оценки студентов. Группа {group_name}')

    # Добавляем названия студентов на ось x
    plt.xticks(zvenos, [f"{zveno + 1}" for zveno in zvenos])

    # Сохраняем график в папку проекта
    filename = 'plot.png'
    plt.savefig(filename)
    plt.close()  # Закрываем график

    return filename


async def send_plot(callback: CallbackQuery, grouped_students: list, group_id: str):
    filename = create_and_save_plot(grouped_students, group_id)
    if filename == 0:
        await callback.message.answer("В данной группе еще нет оценок")
    else:
        photo = FSInputFile(filename)
        await callback.message.answer_photo(photo)
        os.remove(filename)

