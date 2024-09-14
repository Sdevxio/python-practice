from oop.school_management.person import Person


class Teacher(Person):
    def __init__(self, name, age, subject):
        super().__init__(name, age)
        self.subject = subject

    def get_person_role(self):
        return f"teacher in {self.subject} class"
