import sqlite3
from datetime import datetime
from models import Student

conn = sqlite3.connect('grades.db')  # Замените 'mydatabase.db' на имя вашей базы данных
cursor = conn.cursor()


def select(query):
    conn = sqlite3.connect('grades.db')
    query = query
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.commit()
    return rows


def insert(table_name: str, data_list: list, auto_increment_id: int = 1):
    # Получаем информацию о столбцах в таблице
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [column[1] for column in cursor.fetchall()]
    columns = columns[auto_increment_id:]
    # print(columns)

    # Генерируем SQL-запрос для вставки данных
    placeholders = ', '.join(['?'] * len(columns))
    query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"

    # Вставляем данные в таблицу
    cursor.execute(query, data_list)
    conn.commit()


def find_student_by_surname(surname: str):
    student_data = select(f'select id, surname, group_name from students where surname = "{surname}"')[0]
    id, surname, group = student_data
    return Student(id, surname, group)


def select_all_events():
    return select(f'select * from events')


def select_type_and_date_events():
    return select(f'select type, date from events order by date')


def select_event_by_id(event_id: int):
    return select(f'select type, date from events where id = {event_id}')[0]


def select_event_type_by_id(event_id: str):
    return select(f'select type from events where id = "{event_id}"')[0][0]


def calculate_score_of_student_by_event_type(student: Student, event_id: str):
    student_id = student.id
    event_type = select_event_type_by_id(event_id)
    print(event_type)
    total_score = select(
        f'''select sum(value) from grades g join events e
        on g.event_id = e.id
        where student_id = {student_id} and e.type = "{event_type}"
        group by type'''
    )
    if not total_score:
        return 0
    else:
        return total_score[0][0]


def add_group_to_db(group_name: str):
    insert("groups", [group_name])


def select_groups_from_db():
    return select(f'select name from groups')


def select_students_by_group(group_name: str) -> list:
    lst = select(f'select surname from students where group_name = "{group_name}"')
    students = [student[0] for student in lst]
    return students


def select_grades_by_group(group_name: str):
    return select(
        f"""select s.surname, value, e.type, e.date from grades g 
        join students s on g.student_id = s.id 
        join events e on g.event_id = e.id
        where group_name = "{group_name}"
        order by date"""
    )


def select_grades_by_student(surname: str):
    student = find_student_by_surname(surname)
    student_id = student.id
    return select(
        f'select value, e.type, e.date from grades g '
        f'join events e on g.event_id = e.id '
        f'where student_id = {student_id}'
    )


def check_grade_for_event_by_student(event_id: str, student: Student):
    grade = select(f'select value from grades '
                   f'where event_id = "{event_id}" and student_id = {student.id}')
    if not grade:
        return False
    else:
        return True


def select_grades_by_month_and_group(month: str, group: str):
    return select(
        f'''
        SELECT surname, SUM(value) FROM grades g
        JOIN (
            SELECT id FROM events
            WHERE date LIKE "%.{month}.____"
        ) me ON g.event_id = me.id
        JOIN students s ON g.student_id = s.id
        WHERE group_name = "{group}" 
        GROUP BY student_id
        '''
    )


def select_total_grades_by_group(group: str):
    return select(
        f"""select surname, sum(value) from grades g
        join students s on g.student_id = s.id
        where group_name = "{group}"
        group by surname
        """
    )


def select_total_grade_by_student(student_id: str):
    return select(f'select sum(value) from grades where student_id = {student_id}')[0][0]



