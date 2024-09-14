class Engine:
    def __init__(self):
        self.is_running = False

    def start(self):
        self.is_running = True
        print(f'Engine started')

    def stop(self):
        self.is_running = False
        print(f'Engine stopped')


class Wheel:
    def __init__(self, position: str):
        self.position = position

    def rotate(self):
        return f"Wheel rotating: {self.position}"


class Car:
    def __init__(self):
        self.engine = Engine()
        self.wheels = [
            Wheel("front-left"),
            Wheel("front-right"),
            Wheel("rear-left"),
            Wheel("rear-right"),
        ]

    def start_car(self):
        self.engine.start()

    def stop_car(self):
        self.engine.stop()

    def drive(self):
        if not self.engine.is_running:
            print("Can't drive, engine is not running!")
            return
        for wheel in self.wheels:
            print(wheel.rotate())


if __name__ == '__main__':
    car = Car()
    car.start_car()
    car.drive()
    car.stop_car()
    car.drive()  # This should print that the car can't drive
