from db import *
import pandas as pd
import datetime
from MarkTypes import mark_types


months = [
    "Январь",
    "Февраль",
    "Март",
    "Апрель",
    "Май",
    "Июнь",
    "Июль",
    "Август",
    "Сентябрь",
    "Октябрь",
    "Ноябрь",
    "Декабрь",
]


# Функция формирования таблицы с оценками для определенной группы и месяца
def create_grades_table_of_group(group_name: str, date: str) -> str:
    print("Начал создавать таблицу")
    # Получение списка событий и студентов для данной группы из базы данных
    events = select_type_and_date_events_by_group_id(group_name)
    students = select_students_by_group_id(group_name)
    # Формирование заголовков таблицы, включая столбцы "За все время" и "За указанный месяц"
    columns = [
        "За все время",
        f"За {months[int(date) - 1]}",
        "За посещения",
        "За конспекты",
        "За СРС",
    ]
    # Добавление событий в качестве дополнительных столбцов в таблицу
    print(f"events: {events}")
    for event in events:
        print(f"event_date: {type(event[1])}")
    events = [f"{mark_types[event[0]]} {event[1].strftime('%d-%m')}" for event in events]
    columns.extend(events)
    # Создание пустой таблицы с индексами студентов и указанными столбцами
    main_df = pd.DataFrame(index=students, columns=columns)
    # Получение оценок студентов за указанный месяц и за все время из базы данных
    month_grades = select_grades_by_month_and_group_id(month(date), group_name)
    total_grades = select_total_grades_by_group_id(group_name)
    total_conspect_grades = select_total_conspect_by_group_id(group_name)
    total_srs_grades = select_total_srs_by_group_id(group_name)
    total_sem_grades = select_total_sem_by_group_id(group_name)

    for total_conspect_grade in total_conspect_grades:
        main_df.at[total_conspect_grade[0], f"За конспекты"] = total_conspect_grade[1]

    for total_srs_grade in total_srs_grades:
        main_df.at[total_srs_grade[0], f"За СРС"] = total_srs_grade[1]

    for total_sem_grade in total_sem_grades:
        main_df.at[total_sem_grade[0], f"За посещения"] = total_sem_grade[1]



    # Заполнение таблицы общими оценками за все время для каждого студента
    for total_grade in total_grades:
        main_df.at[total_grade[0], f"За все время"] = total_grade[1]
    # Заполнение таблицы оценками за указанный месяц для каждого студента
    for month_grade in month_grades:
        main_df.at[month_grade[0], f"За {months[int(date) - 1]}"] = month_grade[1]
    # Заполнение таблицы оценками по каждому событию для каждого студента
    for student in students:
        grades = select_grades_by_student(student, group_name)
        for grade in grades:
            event = f"{mark_types[grade[1]]} {grade[2].strftime('%d-%m')}"
            value = grade[0]  # Значение оценки
            row_label, column_name = student, event  # Получение меток строк и столбцов
            main_df.at[row_label, column_name] = value  # Заполнение ячейки таблицы оценкой
    # Создание пути для сохранения файла с именем, содержащим название группы и текущую дату и время
    current_time = datetime.datetime.now().strftime("%d-%m-%Y %H-%M-%S")
    summary_path = f"Summaries/Отчет_{group_name}---{current_time}.xlsx"
    # Сохранение таблицы в файл Excel
    main_df.to_excel(summary_path)
    print("ЗАкончил создавать таблицу")

    return summary_path  # Возврат пути к сохраненному файлу


def month(date: str):
    if int(date) < 10:
        return f'0{date}'
    else:
        return date