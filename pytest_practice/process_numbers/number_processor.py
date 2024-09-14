import json


def process_numbers(numbers):
    try:
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise ValueError(f"Error reading config file: {str(e)}")

    operation = config.get('operation')
    value = config.get('value')

    if operation not in ['add', 'multiply'] or not isinstance(value, (int, float)):
        raise ValueError("Invalid configuration")

    if operation == 'add':
        return [num + value for num in numbers]
    else:  # multiply
        return [num * value for num in numbers]
