import configparser

import pytest

from pytest_practice.read_from_ini.get_database_config import get_database_config


def test_get_database_config(config_file, expected_data):
    result = get_database_config(config_file, 'Database')
    assert result == expected_data
    # Additional tests for each key
    for key in expected_data:
        assert key in result
        assert result[key] == expected_data[key]
