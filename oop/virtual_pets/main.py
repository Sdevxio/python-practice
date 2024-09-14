from oop.virtual_pets.Pet_simulator import PetSimulator

if __name__ == '__main__':
    simulator = PetSimulator()
    # print(simulator.adopt_pet('dog', 'Bubby', 'Labrador'))
    #
    # # Adopt a pet with a random breed
    # print(simulator.adopt_pet('cat', 'Nisa'))
    # print(simulator.adopt_pet('fish', 'Nimo'))
    #
    # # List available breeds
    # print(simulator.list_breeds("dog"))

    # Adopt some pets
    # simulator.adopt_pet("dog", "Buddy", "Labrador")
    # simulator.adopt_pet("cat", "Whiskers", "Siamese")

    # List all pets
    # print(simulator.list_pets())

    # Interact with pets
    print(simulator.interact_with_pet("Buddy", "feed"))
    print(simulator.interact_with_pet("Whiskers", "play"))
