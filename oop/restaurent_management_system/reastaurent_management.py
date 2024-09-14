from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class MenuItem(ABC):
    def __init__(self, name: str, price: float):
        self.name = name
        self.price = price
        print(
            f"*********** \n Name: '{self.name}' created. "
            f"\n Price = ${self.price:.2f}"
            f"\n*********** ")

    @abstractmethod
    def prepare(self) -> str:
        pass

    def get_details(self) -> str:
        return f"{self.name}: ${self.price:.2f}"


class Appetizer(MenuItem):
    def __init__(self, name: str, price: float, size: str):
        super().__init__(name, price)
        self.size = size

    def prepare(self) -> str:
        return f"Preparing {self.size} appetizer: {self.name}"


class MainCourse(MenuItem):
    def __init__(self, name: str, price: float, cuisine: str):
        super().__init__(name, price)
        self.cuisine = cuisine

    def prepare(self) -> str:
        return f"Cooking {self.cuisine} main course: {self.name}"


class Dessert(MenuItem):
    def __init__(self, name: str, price: float, is_warm: bool):
        super().__init__(name, price)
        self.is_warm = is_warm

    def prepare(self) -> str:
        temperature = "warm" if self.is_warm else "cold"
        return f"Preparing {temperature} dessert: {self.name}"


class Menu:
    def __init__(self, name: str):
        self.name = name
        self.items: Dict[str, MenuItem] = {}

    def add_item(self, item: MenuItem) -> None:
        if item.name not in self.items:
            self.items[item.name] = item
        else:
            print(f"Item '{item.name}' already exists in the menu.")

    def remove_item(self, item_name: str) -> bool:
        return self.items.pop(item_name, None) is not None

    def get_total_price(self) -> float:
        return sum(item.price for item in self.items.values())

    def display_items(self) -> str:
        output = f"Menu: {self.name}\n"
        for category in [Appetizer, MainCourse, Dessert]:
            category_name = category.__name__
            items = [item for item in self.items.values() if isinstance(item, category)]
            if items:
                output += f"\n{category_name}s:\n"
                for item in items:
                    output += f"  {item.get_details()}\n"
        return output

    def find_item(self, item_name: str) -> Optional[MenuItem]:
        return self.items.get(item_name)


class Order:
    def __init__(self, order_id: int):
        self.order_id = order_id
        self.items: List[MenuItem] = []

    def add_item(self, item: MenuItem) -> None:
        self.items.append(item)

    def remove_item(self, item_name: str) -> bool:
        for item in self.items:
            if item.name == item_name:
                self.items.remove(item)
                return True
        return False

    def get_total_price(self) -> float:
        return sum(item.price for item in self.items)

    def prepare_order(self) -> List[str]:
        return [item.prepare() for item in self.items]


class Restaurant:
    def __init__(self, name: str):
        self.name = name
        self.menus: Dict[str, Menu] = {}
        self.orders: List[Order] = []

    def create_menu(self, menu_name: str) -> None:
        if menu_name not in self.menus:
            self.menus[menu_name] = Menu(menu_name)
        else:
            print(f"Menu '{menu_name}' already exists.")

    def add_item_to_menu(self, menu_name: str, item: MenuItem) -> bool:
        if menu_name in self.menus:
            self.menus[menu_name].add_item(item)
            return True
        return False

    def create_order(self) -> Order:
        order = Order(len(self.orders) + 1)
        self.orders.append(order)
        return order

    def find_most_popular_item(self) -> Optional[MenuItem]:
        if not self.orders:
            return None
        all_items = [item for order in self.orders for item in order.items]
        return max(set(all_items), key=all_items.count)

    def calculate_total_revenue(self) -> float:
        return sum(order.get_total_price() for order in self.orders)


# Demonstration
if __name__ == "__main__":
    # Create a restaurant
    restaurant = Restaurant("Gourmet Delight")

    # Create a menu and add items
    restaurant.create_menu("Lunch Special")
    restaurant.add_item_to_menu("Lunch Special", Appetizer("Garlic Bread", 5.99, "Small"))
    restaurant.add_item_to_menu("Lunch Special", MainCourse("Spaghetti Carbonara", 15.99, "Italian"))
    restaurant.add_item_to_menu("Lunch Special", Dessert("Tiramisu", 7.99, False))

    # Display the menu
    print(restaurant.menus["Lunch Special"].display_items())

    # Create an order
    order1 = restaurant.create_order()
    order1.add_item(restaurant.menus["Lunch Special"].find_item("Garlic Bread"))
    order1.add_item(restaurant.menus["Lunch Special"].find_item("Spaghetti Carbonara"))

    # Prepare the order
    print("\nPreparing Order:")
    for step in order1.prepare_order():
        print(step)

    # Calculate total price of the order
    print(f"\nTotal Price: ${order1.get_total_price():.2f}")

    # Find the most popular item
    popular_item = restaurant.find_most_popular_item()
    if popular_item:
        print(f"\nMost Popular Item: {popular_item.name}")

    # Calculate total revenue
    print(f"\nTotal Revenue: ${restaurant.calculate_total_revenue():.2f}")
