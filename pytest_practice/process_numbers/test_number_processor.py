import pytest
import json
import os

from pytest_practice.process_numbers.number_processor import process_numbers


@pytest.fixture
def config_file(tmp_path, request):
    config = request.param
    config_path = tmp_path / "config.json"
    with open(config_path, "w") as f:
        json.dump(config, f)

    old_path = os.getcwd()
    os.chdir(tmp_path)
    yield
    os.chdir(old_path)


@pytest.mark.parametrize("config_file, numbers, expected", [
    ({"operation": "add", "value": 5}, [1, 2, 3], [6, 7, 8]),
    ({"operation": "multiply", "value": 2}, [1, 2, 3], [2, 4, 6]),
], indirect=["config_file"])
def test_process_numbers(config_file, numbers, expected):
    result = process_numbers(numbers)
    assert result == expected


@pytest.mark.parametrize("config_file", [{"operation": "add", "value": 5}], indirect=True)
def test_empty_list(config_file):
    assert process_numbers([]) == []


def test_missing_config_file(tmp_path):
    os.chdir(tmp_path)
    with pytest.raises(ValueError) as excinfo:
        process_numbers([1, 2, 3])
    assert "Error reading config file" in str(excinfo.value)
    os.chdir('..')


def test_invalid_config(tmp_path):
    config = {"operation": "invalid", "value": "not a number"}
    config_path = tmp_path / "config.json"
    with open(config_path, "w") as f:
        json.dump(config, f)

    old_path = os.getcwd()
    os.chdir(tmp_path)

    with pytest.raises(ValueError) as excinfo:
        process_numbers([1, 2, 3])

    os.chdir(old_path)
    assert "Invalid configuration" in str(excinfo.value)