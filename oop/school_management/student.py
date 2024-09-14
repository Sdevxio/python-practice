from oop.school_management.person import Person


class Student(Person):
    def __init__(self, name, age, grade):
        super().__init__(name, age)
        self.grade = grade

    def get_person_role(self):
        return f"student in grade {self.grade}"
