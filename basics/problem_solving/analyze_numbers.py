def analyze_numbers_test(numbers: list) -> dict:
    result = {}
    # Calculate the sum of all numbers in the list
    if len(numbers) != 0:
        result['sum'] = round(sum(numbers), 2)
        # Find the maximum number in the list
        result['max'] = round(max(numbers), 2)
        # Find the minimum number in the list
        result['min'] = round(min(numbers), 2)
        # Calculate the average (mean) of all numbers in the list
        average = round(sum(numbers) / len(numbers), 2)
        result['average'] = round(average, 2)
    else:
        result['sum'] = 0
        result['max'] = None
        result['min'] = None
        result['average'] = 0
    # The function should return a dictionary with these results.
    return result


def analyze_numbers(numbers: list) -> dict:
    if not numbers:
        return {'sum': 0,
                'max': None,
                'min': None,
                'average': 0}
    total = sum(numbers)
    return {
        'sum': round(total, 2),
        'max': max(numbers),
        'min': min(numbers),
        'average': round(total / len(numbers), 2)
    }


print(analyze_numbers([1, 2, 3, 4, 5]))
print(analyze_numbers([10.5, 20.3, 3.25, -4.5]))
print(analyze_numbers([]))
print(analyze_numbers([100]))

