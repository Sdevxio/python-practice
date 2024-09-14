from oop.school_management.student import Student
from oop.school_management.teacher import Teacher


class School:
    def __init__(self):
        self.people = {}

    def add_student(self, name, age, grade):
        if name in self.people:
            return f"A person with the name {name} already exists."
        student = Student(name, age, grade)
        self.people[name] = student
        return f"Added student: {name}"

    def add_teacher(self, name, age, subject):
        if name in self.people:
            return f"A person with the name {name} already exists."
        teacher = Teacher(name, age, subject)
        self.people[name] = teacher
        return f"Added teacher: {name}"

    def find_by_name(self, name):
        return self.people.get(name, f"No person found with the name {name}.")

    def list_all_people(self):
        return [person.introduce() for person in self.people.values()]
