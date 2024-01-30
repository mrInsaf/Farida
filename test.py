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

# student = Student("131", "СалаховИ. М.", 'biv202')

# print(find_student_by_surname("Платон"))

# print(select_groups_by_teacher("Insaf"))
#
# print(select_last_group_id())

# print(select_teacher_id_by_name('816831722'))

# print(add_group_to_db("yoo2o", '816831722'))

print(authorise_teacher("yp"))
