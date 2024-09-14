def calculate_total_test(price: float, quantity: int, discount: float) -> float | str:
    # calculate cost before discount
    total_price = price * quantity
    if discount == 0:
        return total_price
    else:
        # calculate discount
        discount = total_price * (discount / 100)
        total_price = total_price - discount
    return f"Total Price: ${round(total_price, 2)}"


def calculate_total(price: float, quantity: int, discount: float) -> float:
    total_price = price * quantity
    if discount != 0:
        discount_amount = total_price * (discount / 100)
        total_price -= discount_amount
    return round(total_price, 2)


# return final total cost after applying the discount
print(calculate_total(10.00, 2, 10))  # Should output 18.00
print(calculate_total(25.50, 5, 0))  # Should output 127.50
print(calculate_total(5.99, 3, 15))  # Should output 15.27
print(calculate_total(50.00, 1, 20))  # Should output 40.00
