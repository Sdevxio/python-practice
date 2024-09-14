import configparser

import pytest


@pytest.fixture
def config_file(tmp_path):
    # Create a temporary config.ini file
    config = configparser.ConfigParser()
    config['Database'] = {
        'host': 'localhost',
        'port': '5432',
        'username': 'admin',
        'password': 'secret'
    }
    file_path = tmp_path / "config.ini"
    print(file_path)
    with open(file_path, 'w') as f:
        config.write(f)

    # Yield the path to the temporary file
    yield str(file_path)

    # Teardown (file will be automatically deleted after the test)



@pytest.fixture
def expected_data():
    return {
        'host': 'localhost',
        'port': '5432',
        'username': 'admin',
        'password': 'secret'
    }
