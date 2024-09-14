from abc import ABC, abstractmethod


class Person(ABC):
    def __init__(self, name, age):
        self.name = name
        self.age = age

    @abstractmethod
    def get_person_role(self):
        pass

    def introduce(self):
        return f"Hi, my name {self.name} and my age {self.age}, and I am a {self.get_person_role()}"

    def __str__(self):
        return self.introduce()
