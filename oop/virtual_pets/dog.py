from oop.virtual_pets.pets import Pets


class Dog(Pets):

    def __init__(self, name, age=0, breed="Unknown"):
        super().__init__(name, age)
        self.breed = breed

    def make_sound(self):
        return "Woof!"

    def fetch(self):
        self.happiness_level = min(100, self.happiness_level + 15)
        self.energy_level = max(0, self.energy_level - 10)
        return f"{self.name} had fun playing fetch!"
