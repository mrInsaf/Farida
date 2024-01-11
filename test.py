from db import *
from add_group import *
from show_grades import *

mark_types = {
    "sem": "Посещение",
    "conspect": "Конспект",
    "srs": "СРС",
    "doklad": "Доклад",
    "presentation": "Презентация",
    "bashvat": "Головоломка",
    "test": "Тестирование",
}

student = Student("4", "СалаховИ. М.", 'biv202')
#
# insert_group("Б112-04", 'Б112-04.txt')

# print(select_students_by_group('Б112-04'))

# print(find_student_by_surname('Айтуганова А.Д.'))

# create_grades_table_of_group('Б112-04', '')

# print(select_grades_by_month('01'))

print(select_students_by_group("Документ Google  Keep (1)"))

# print(check_grade_for_event_by_student('5', find_student_by_surname("Айтуганова А.Д.")))

