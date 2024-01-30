import datetime

class Student:
    id: str
    surname: str
    group: str
    group_id: str

    def __init__(self, id: str, surname: str, group: str, group_id: str):
        self.id = id
        self.surname = surname
        self.group = group
        self.group_id = group_id

    def __str__(self):
        return f"{self.surname}, группа {self.group}"


class Event:
    name: str
    type: str
    date: str

    def __init__(self, name: str, type: str, date: str):
        self.name = name
        self.type = type
        self.date = date




