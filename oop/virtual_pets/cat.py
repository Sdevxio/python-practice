from oop.virtual_pets.pets import Pets


class Cat(Pets):
    def __init__(self, name, age=0, breed="Unknown"):
        super().__init__(name, age)
        self.breed = breed
        self.fur_cleanliness = 100  # New attribute

    def make_sound(self):
        return "Meow!"

    def sleeping(self):
        self.hunger_level = min(100, self.hunger_level + 15)
        self.happiness_level = min(100, self.happiness_level + 5)
        self.energy_level = min(100, self.energy_level + 30)  # Fixed: Sleeping increases energy
        return f"{self.name} had a nice nap!"

    def groom(self):
        self.fur_cleanliness = min(100, self.fur_cleanliness + 30)
        self.happiness_level = min(100, self.happiness_level + 15)
        return f"{self.name} purrs contentedly while being groomed!"

    def play(self):
        super().play()
        self.fur_cleanliness = max(0, self.fur_cleanliness - 10)  # Playing makes the cat's fur dirty

    def update_status(self):
        super().update_status()
        self.fur_cleanliness = max(0, self.fur_cleanliness - 5)  # Fur gets dirty over time

    def __str__(self):
        return f"{super().__str__()}, Fur Cleanliness: {self.fur_cleanliness}"
