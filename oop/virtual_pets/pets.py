from abc import ABC, abstractmethod


class Pets(ABC):
    def __init__(self, name, age):
        self.name = name
        self.age = age
        self.hunger_level = 50
        self.happiness_level = 50
        self.energy_level = 50

    def feed(self):
        self.hunger_level = max(0, self.hunger_level - 20)
        self.happiness_level = min(100, self.happiness_level + 10)

    def play(self):
        self.hunger_level = min(100, self.hunger_level + 10)
        self.happiness_level = min(100, self.happiness_level + 20)
        self.energy_level = max(0, self.energy_level - 20)

    def sleep(self):
        self.energy_level = min(100, self.energy_level + 40)
        self.hunger_level = min(100, self.hunger_level + 10)

    @abstractmethod
    def make_sound(self):
        pass

    def update_status(self):
        self.hunger_level = min(100, self.hunger_level + 5)
        self.happiness_level = max(0, self.happiness_level)
        self.energy_level = max(0, self.energy_level)

    def __str__(self):
        return f"{self.name} - Hunger: {self.hunger_level}, Happiness: {self.happiness_level}, Energy: {self.energy_level} "
