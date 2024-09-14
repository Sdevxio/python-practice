def calculate_expression_test(num1, num2, operator):
    if operator == '+':
        result = num1 + num2
    elif operator == '-':
        result = num1 - num2
    elif operator == '*':
        result = num1 * num2
    elif operator == '/':
        if num2 != 0:
            result = num1 / num2
        else:
            return "Error: Division by zero"
    else:
        return "Invalid operator"
    return f"{num1:.2f} {operator} {num2:.2f} = {result:.2f} "


def calculate_expression(num1: float, num2: float, operator: str) -> float | str:
    if operator == '+':
        result = num1 + num2
    elif operator == '-':
        result = num1 - num2
    elif operator == '*':
        result = num1 * num2
    elif operator == '/':
        if num2 != 0:
            result = num1 / num2
        else:
            return "Cannot divide by zero"
    else:
        return "Invalid operator"
    return round(result, 2)


print(calculate_expression(5, 3, '+'))  # Should output 8.00
print(calculate_expression(10, 4, '-'))  # Should output 6.00
print(calculate_expression(3, 7, '*'))  # Should output 21.00
print(calculate_expression(15, 3, '/'))  # Should output 5.00
print(calculate_expression(10, 0, '/'))  # Should output "Cannot divide by zero"
print(calculate_expression(5, 3, '%'))  # Should output "Invalid operator"