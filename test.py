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

student = Student("131", "СалаховИ. М.", 'biv202')

# print(select_grades_by_month_and_group("01", "Б111-07"))

print(create_grades_table_of_group('Б111-07', '01'))

# print(select_type_and_date_events_by_group('Б111-07'))

