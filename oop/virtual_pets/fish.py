from oop.virtual_pets.pets import Pets


class Fish(Pets):
    def __init__(self, name, age=0,breed="Unknown"):
        super().__init__(name, age)
        self.breed = breed
        self.water_cleanliness = 100

    def make_sound(self):
        return "Blub blub"

    def eating(self):
        self.energy_level = min(100, self.energy_level + 20)
        self.hunger_level = max(0, self.hunger_level - 15)
        self.water_cleanliness = max(0, self.water_cleanliness - 10)  # Eating makes the water dirty
        return f"{self.name} enjoyed eating!"

    def clean_tank(self):
        self.water_cleanliness = 100
        self.happiness_level = min(100, self.happiness_level + 10)
        return f"{self.name}'s tank is now clean and fresh!"

    def update_status(self):
        super().update_status()
        self.water_cleanliness = max(0, self.water_cleanliness - 5)  # Water gets dirty over time

    def __str__(self):
        return f"{super().__str__()}, Water Cleanliness: {self.water_cleanliness}"
