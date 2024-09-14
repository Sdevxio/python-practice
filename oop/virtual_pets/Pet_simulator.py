import random

from oop.virtual_pets.cat import Cat
from oop.virtual_pets.dog import Dog
from oop.virtual_pets.fish import Fish


class PetSimulator:
    def __init__(self):
        self.pets = {}
        self.breeds = {
            "dog": ["Labrador", "German Shepherd", "Golden Retriever", "Bulldog", "Poodle"],
            "cat": ["Persian", "Siamese", "Maine Coon", "British Shorthair", "Sphynx"],
            "fish": ["Goldfish", "Betta", "Guppy", "Angelfish", "Tetra"]
        }

    def adopt_pet(self, pet_type, name, breed=None):
        if name in self.breeds:
            return f"The pet {name} already exists. Please choose a different pet name."

        pet_type = pet_type.lower()
        if pet_type not in ['dog', 'cat', 'fish']:
            return f"Sorry the {pet_type} is not valid pet type. Choose from Dog, Cat, or Fish."

        if breed is None:
            breed = random.choice(self.breeds[pet_type])
        elif breed not in self.breeds[pet_type]:
            return f"Sorry, {breed} is not a valid breed for {pet_type}. Available breeds arr: {', '.join(self.breeds[pet_type])}"

        match pet_type:
            case "dog":
                new_pet = Dog(name, breed=breed)
            case "cat":
                new_pet = Cat(name, breed=breed)
            case "fish":
                new_pet = Fish(name, breed=breed)
            case _:
                return f"Unexpected error occurred with pet type: {pet_type}"
        self.pets[name] = new_pet
        return f"Congratulations You've adopted s {breed} {pet_type} named {name}"

    def list_breeds(self, pet_type):
        pet_type = pet_type.lower()
        if pet_type in self.breeds:
            return f"Available {pet_type} in breeds '{', '.join(self.breeds[pet_type])}'"
        else:
            return f"Sorry, {pet_type} is not available. Choose from Dog, Cat, or Fish. "

    def interact_with_pet(self, pet_name, action):
        if pet_name not in self.pets:
            return f"No pet named {pet_name} found."

        pet = self.pets[pet_name]
        match action.lower():
            case 'sleep':
                pet.sleep()
                return f"{pet_name} took a nap."
            case 'feed':
                pet.feed()
                return f"{pet_name} has been fed."
            case 'play':
                pet.play()
                return f"You played with {pet_name}."
            case 'make_sound':
                return f"{pet_name} says: {pet.make_sound()}"
            case _:
                return f"Unknown action: {action}. Try 'feed', 'play', 'sleep', or 'make_sound'."


        # def display_pet_status(self, pet_name):



# def lis_pets(self):
#     pass
#
# def save_game(self, filename):
#     pass
#
# def load_game(self, filename):
#     pass


def run(self):
    # Main game loop
    while True:
        # Display menu, get user input, and call appropriate methods
        pass
