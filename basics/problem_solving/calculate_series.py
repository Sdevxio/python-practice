def calculate_series_claud(numbers: list, operations: list) -> float:
    # Convert all numbers to floats
    numbers = list(map(float, numbers))

    # Handle cases with fewer than 2 numbers
    if len(numbers) < 2:
        return round(numbers[0] if numbers else 0, 2)

    # If no operations provided, return sum of numbers
    if not operations:
        return round(sum(numbers), 2)

    result = numbers[0]
    op_index = 0

    for num in numbers[1:]:
        op = operations[op_index % len(operations)]

        if op == '+':
            result += num
        elif op == '-':
            result -= num
        elif op == '*':
            result *= num
        elif op == '/' and num != 0:
            result /= num
        # If division by zero, skip this operation

        op_index += 1

    return round(result, 2)


def calculate_series_gpt(numbers: list, operators: list) -> float | str:
    # Convert input numbers to floats using list comprehension
    numbers = [float(num) for num in numbers]

    # If the list of numbers is empty, return 0
    if len(numbers) == 0:
        return 0.0

    # If the list has only one number, return that number
    if len(numbers) == 1:
        return round(numbers[0], 2)

    # If operations list is empty, return the sum of all numbers
    if len(operators) == 0:
        return round(sum(numbers), 2)

    # Start with the first number
    result = numbers[0]

    # Apply operations in sequence, repeating if there are fewer operations than gaps between numbers
    for i in range(1, len(numbers)):
        operator = operators[(i - 1) % len(operators)]  # Repeat operations if there are fewer than gaps

        # Perform the operation based on the current operator
        if operator == '+':
            result += numbers[i]
        elif operator == '-':
            result -= numbers[i]
        elif operator == '*':
            result *= numbers[i]
        elif operator == '/':
            # Handle division by zero by skipping the operation
            if numbers[i] != 0:
                result /= numbers[i]

    # Return the result rounded to two decimal places
    return round(result, 2)


print(calculate_series_claud([1, 2, 3, 4], ['+', '*', '-']))  # Should output 5.00
print(calculate_series_claud([1, 2, 0, 4], ['+', '/', '*']))  # Should output 12.00
print(calculate_series_claud([1], ['+']))  # Should output 1.00
print(calculate_series_claud([], ['+']))  # Should output 0.00
print(calculate_series_claud([1, 2, 3, 4], []))  # Should output 10.00
print(calculate_series_claud([1, 2, 3, 4], ['+', '*', '-']))
print(calculate_series_claud([1.5, 2.5, 3.5], []))  # Should output 7.50.5 + 2.5 + 3.5 = 7.50
print(calculate_series_claud([10], ['*', '+', '-']))  # Should output 10.00
print(calculate_series_claud([], ['*', '+', '-']))  # Should output 0.00
