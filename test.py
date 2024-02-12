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

student = Student("281", "СалаховИ. М.", 'biv202', "2")

print(check_grade_for_event_by_student("50", student))
