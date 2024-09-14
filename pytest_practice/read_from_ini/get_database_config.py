import configparser


def get_database_config_test(config_file, section):
    config = configparser.ConfigParser()
    config.read(config_file)
    properties = {}
    for section in config.sections():
        for key, value in config.items(section):
            properties[key] = value
    return properties


def get_database_config(config_file, section):
    config = configparser.ConfigParser()
    config.read(config_file)
    return dict(config[section])