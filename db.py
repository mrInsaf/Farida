import sqlite3
from datetime import datetime
from models import Student

import mysql
from mysql.connector import Error, pooling

print("я ща в db.py")
# Параметры подключения к базе данных MySQL
config = {
    'user': 'lesha',
    'password': 'alexei',
    'host': '45.151.31.119',
    'database': 'farida',
    'port': 3306,
    'raise_on_warnings': True,
}

pool = pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=5,
    **config
)
print("Создал пул соединений")


def get_connection():
    try:
        connection = pool.get_connection()
        if connection.is_connected():
            print("Соединение успешно установлено.")
            return connection
        else:
            raise Exception("Не удалось подключиться к базе данных: соединение не активно.")
    except mysql.connector.Error as e:
        print(f"Ошибка подключения: {e}")
        return None



def execute_query(query):
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            conn.commit()
        finally:
            cursor.close()
            conn.close()  # Возвращает соединение в пул
    else:
        raise Exception("Не удалось установить соединение с базой данных")


def select(query):
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            conn.commit()
            return rows
        finally:
            cursor.close()
            conn.close()  # Возвращает соединение в пул
    else:
        return None


def insert(table_name: str, data_list: list, auto_increment_id: int = 1):
    try:
        # Получаем соединение из пула
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(f"SHOW COLUMNS FROM {table_name}")
                columns = [column[0] for column in cursor.fetchall()]
                columns = columns[auto_increment_id:]
                placeholders = ', '.join(['%s'] * len(columns))
                query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"

                cursor.execute(query, data_list)
                row_id = cursor.lastrowid
                conn.commit()
                return row_id
            except Exception as e:
                print(f"Исключение при insert: {e}")
            finally:
                cursor.close()
                conn.close()  # Возвращает соединение в пул
        else:
            return None
    except Exception as e:
        print(f"Исключение при получении соединения: {e}")
        return None


def find_student_by_surname_and_group_id(surname: str, group_id: str):
    student_data = select(
        f'''select s.id, surname, group_name, group_id from students s 
            join `groups` g on g.id = s.group_id
            where surname = "{surname}" and group_id = {group_id}''')[0]
    return Student(*student_data)


def select_all_events_by_teacher_id(teacher_id: int):
    return select(f'select * from events e '
                  f'join teachers t on e.teacher_id = t.teacher_id '
                  f'where t.teacher_id = "{teacher_id}"')


# def select_visit_events_by_teacher_id()


def select_type_and_date_events_by_group_id(group_id: str):
    return select(
        f'''
            select e.type, e.date from grades g 
            join events e 
            on e.id = g.event_id 
            join students s on s.id = g.student_id
            where s.group_id = {group_id}
            group by e.id, e.date, e.type
            order by date desc
    ''')


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


def select_teacher_id_by_name(teacher_name: str):
    return select(f'select id from teachers where name = "{teacher_name}"')[0][0]


def add_group_to_db(group_name: str, teacher_id: int):
    return insert("`groups`", [group_name, teacher_id])


def select_last_group_id():
    return select(f'select max(id) from `groups`')


def select_groups_by_teacher_id(teacher_id: int):
    return select(f'''
    select g.name, g.id from `groups` g
    join teachers t on g.teacher_id = t.teacher_id
    where t.teacher_id = "{teacher_id}"
    ''')


def select_group_name_by_id(group_id: str):
    return select(f'''
    select name from  `groups` 
    where id = {group_id}
''')[0][0]


def select_students_by_group_id(group_id: str) -> list:
    lst = select(
        f'''
        select surname from students s 
         join `groups` g on s.group_id = g.id
         where group_id = {group_id}
        
        ''')
    students = [student[0] for student in lst]
    return students


def select_grades_by_group_id(group_id: str):
    return select(
        f"""select s.surname, value, e.type, e.date from grades g 
        join students s on g.student_id = s.id 
        join events e on g.event_id = e.id
        join `groups` gr on s.group_id = gr.id
        where group_id = {group_id}
        order by date"""
    )


def select_grades_by_student(surname: str, group_id: str):
    student = find_student_by_surname_and_group_id(surname, group_id)
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


def select_grades_by_month_and_group_id(month: str, group_id: str):
    return select(
        f'''
        SELECT surname, SUM(value) FROM grades g
        JOIN (
            SELECT id FROM events
            WHERE date LIKE "____-{month}-%"
        ) me ON g.event_id = me.id
        JOIN students s ON g.student_id = s.id
        join `groups` gr on s.group_id = gr.id
        WHERE group_id = {group_id}
        GROUP BY student_id
        '''
    )


def select_total_grades_by_group_id(group_id: str):
    return select(
        f"""
        select surname, sum(value) from grades g
        join students s on g.student_id = s.id
        join `groups` gr on s.group_id = gr.id
        where group_id = {group_id}
        group by surname
        """
    )


def select_total_conspect_by_group_id(group_id: str):
    return select(
        f"""
        select surname, sum(value) from grades g
        join students s on g.student_id = s.id
        join `groups` gr on s.group_id = gr.id
        join events e on g.event_id = e.id
        where group_id = {group_id} and e.type = "conspect"
        group by surname
"""
    )


def select_total_srs_by_group_id(group_id: str):
    return select(
        f"""
        select surname, sum(value) from grades g
        join students s on g.student_id = s.id
        join `groups` gr on s.group_id = gr.id
        join events e on g.event_id = e.id
        where group_id = {group_id} and e.type = "srs"
        group by surname
"""
    )


def select_total_sem_by_group_id(group_id: str):
    return select(
        f"""
        select surname, sum(value) from grades g
        join students s on g.student_id = s.id
        join `groups` gr on s.group_id = gr.id
        join events e on g.event_id = e.id
        where group_id = {group_id} and e.type = "sem"
        group by surname
"""
    )


def select_total_grade_by_student(student_id: str):
    return select(f'select sum(value) from grades where student_id = {student_id}')[0][0]


def check_teacher_exists(teacher_id: int):
    return select(f'select id from teachers where teacher_id = {teacher_id}')


def check_auth_by_teacher_id(teacher_id: int):
    auth = select(f'select is_authorised from teachers where teacher_id = {teacher_id}')[0][0]
    if auth == 1:
        return True
    else:
        return False


def register_teacher(teacher_id: int, encrypted_password: str):
    insert("teachers", [teacher_id, encrypted_password, 0, "-"])


def get_hashed_password(teacher_id: int):
    hashed_password = select(f'select password from teachers where teacher_id = {teacher_id}')[0][0]
    return hashed_password


def authorise_teacher(teacher_id: int):
    current_datetime = datetime.now()
    formatted_datetime = current_datetime.strftime("%d.%m.%Y %H:%M:%S")

    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE teachers SET is_authorised = 1, auth_dttm = %s WHERE teacher_id = %s',
                (formatted_datetime, teacher_id)
            )
            conn.commit()
            print(f"Teacher with ID {teacher_id} authorised.")
        except Exception as e:
            print(f"Исключение при авторизации учителя: {e}")
        finally:
            cursor.close()
            conn.close()  # Возвращает соединение в пул
    else:
        print("Не удалось получить соединение.")


def unauthorise_teacher(teacher_id: int):
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE teachers SET is_authorised = 0 WHERE teacher_id = %s',
                (teacher_id,)
            )
            conn.commit()
            print(f"Teacher with ID {teacher_id} unauthorised.")
        except Exception as e:
            print(f"Исключение при деавторизации учителя: {e}")
        finally:
            cursor.close()
            conn.close()  # Возвращает соединение в пул
    else:
        print("Не удалось получить соединение.")


def delete_group_by_id(group_id: int):
    execute_query(
        f"""DELETE g FROM grades g
            JOIN students s ON g.student_id = s.id
            WHERE s.group_id = {group_id};"""
    )
    execute_query(
        f"""DELETE FROM students
            WHERE group_id = {group_id};"""
    )
    execute_query(
        f"""DELETE FROM `groups`
            WHERE id = {group_id};"""
    )

