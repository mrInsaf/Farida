from db import *
import pandas as pd
import datetime

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


def create_grades_table_of_group(group_name: str, date: str) -> str:
    events = select_type_and_date_events()
    columns = ["За все время", f"За {months[int(date) - 1]}"]
    events = [f"{event[0]} {event[1]}" for event in events]
    columns.extend(events)
    students = select_students_by_group(group_name)
    main_df = pd.DataFrame(index=students, columns=columns)
    month_grades = select_grades_by_month_and_group(month(date), group_name)
    total_grades = select_total_grades_by_group(group_name)
    for total_grade in total_grades:
        main_df.at[total_grade[0], f"За все время"] = total_grade[1]
    for month_grade in month_grades:
        main_df.at[month_grade[0], f"За {months[int(date) - 1]}"] = month_grade[1]
    for student in students:
        grades = select_grades_by_student(student)
        for grade in grades:
            print(student)
            event = f"{grade[1]} {grade[2]}"
            value = grade[0]
            row_label, column_name = student, event
            main_df.at[row_label, column_name] = value
    current_time = datetime.datetime.now().strftime("%d-%m-%Y %H-%M-%S")
    summary_path = f"Summaries/Отчет_{group_name}---{current_time}.xlsx"
    main_df.to_excel(summary_path, )
    return summary_path


def month(date: str):
    if int(date) < 10:
        return f'0{date}'
    else:
        return date