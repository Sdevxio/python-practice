"""
Config Loader for YAML files, JSON files, and other formats.
This module provides a simple way to find and load configuration files
from specified directories, supporting both YAML and JSON formats.

"""
import json
from pathlib import Path

import yaml

from test_framework.utils.consts.constants import (
    DEFAULT_CONFIG_MODULE,
    FALLBACK_CONFIG_MODULES,
    CONFIG_EXTENSIONS,
    DEFAULT_CONFIG_NAME,
    DEFAULT_ENCODING,
    ERROR_CONFIG_NOT_FOUND
)


class ConfigLoader:
    """
    Basic configs loader - finds and loads configs files
    """

    @staticmethod
    def find_config_path(name="stations", config_module=DEFAULT_CONFIG_MODULE):
        """Find config file path using smart discovery"""
        current = Path.cwd()
        modules_to_try = [config_module] + FALLBACK_CONFIG_MODULES

        # Search up directory tree
        for path in [current] + list(current.parents):
            for module in modules_to_try:
                config_dir = path / module
                if config_dir.exists():
                    for ext in CONFIG_EXTENSIONS:
                        config_file = config_dir / f"{name}{ext}"
                        if config_file.exists():
                            return config_file
        return None

    def load_config(self, name=DEFAULT_CONFIG_NAME, config_module=DEFAULT_CONFIG_MODULE):
        """Load config file and return data"""
        config_path = self.find_config_path(name, config_module)

        if not config_path:
            raise FileNotFoundError(
                ERROR_CONFIG_NOT_FOUND.format(
                    name=name,
                    module=config_module,
                    fallbacks=FALLBACK_CONFIG_MODULES
                )
            )

        try:
            with open(config_path, 'r', encoding=DEFAULT_ENCODING) as f:
                if config_path.suffix.lower() == '.json':
                    return json.load(f)
                else:  # .yaml or .yml
                    return yaml.safe_load(f) or {}
        except Exception as e:
            raise Exception(f"Error loading config from {config_path}: {e}")

    def get_config(self, name=DEFAULT_CONFIG_NAME, config_module=DEFAULT_CONFIG_MODULE):
        """Easy alias for load_config"""
        return self.load_config(name, config_module)