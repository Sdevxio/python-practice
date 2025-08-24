"""
YamlLoader - YAML file loader with comprehensive error handling
"""
from pathlib import Path
from typing import Any, Dict, Optional, Union
import yaml

from test_framework.utils.consts.constants import (
    DEFAULT_ENCODING,
    ERROR_FILE_NOT_FOUND,
    ERROR_YAML_PARSE
)


class YamlLoader:
    """YAML file loader with support for reading all values and getting specific values."""

    def __init__(self, file_path: Union[str, Path]):
        """Initialize the YAML loader with a file path.

        Args:
            file_path: Path to the YAML file
        """
        self.file_path = Path(file_path)
        self._data: Optional[Dict[str, Any]] = None

    def load(self) -> Dict[str, Any]:
        """Load and return all values from the YAML file.

        Returns:
            Dictionary containing all YAML data

        Raises:
            FileNotFoundError: If the YAML file doesn't exist
            yaml.YAMLError: If the YAML file is invalid
        """
        if not self.file_path.exists():
            raise FileNotFoundError(ERROR_FILE_NOT_FOUND.format(path=self.file_path))

        try:
            with open(self.file_path, 'r', encoding=DEFAULT_ENCODING) as file:
                self._data = yaml.safe_load(file)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(ERROR_YAML_PARSE.format(path=self.file_path) + f": {e}")
        except Exception as e:
            raise Exception(f"Unexpected error loading YAML file {self.file_path}: {e}")

        return self._data or {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get a specific value from the YAML file using dot notation.

        Args:
            key: Key to retrieve (supports dot notation for nested values)
            default: Default value if key is not found

        Returns:
            The value at the specified key or default value

        Examples:
            loader.get('name')  # Get top-level value
            loader.get('database.host')  # Get nested value
            loader.get('database.settings.timeout', 30)  # Get deeply nested with default
            loader.get('items.0.name')  # Get item from list by index
        """
        if self._data is None:
            self.load()

        keys = key.split('.')
        value = self._data

        try:
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                elif isinstance(value, list) and k.isdigit():
                    index = int(k)
                    if 0 <= index < len(value):
                        value = value[index]
                    else:
                        return default
                else:
                    return default
        except (TypeError, ValueError, KeyError):
            # Handle any unexpected errors during key traversal
            return default

        return value

    def get_all(self) -> Dict[str, Any]:
        """Get all values from the YAML file.

        Returns:
            Dictionary containing all YAML data
        """
        if self._data is None:
            self.load()

        return self._data or {}

    def reload(self) -> Dict[str, Any]:
        """Reload the YAML file from disk.

        Returns:
            Dictionary containing all YAML data
        """
        self._data = None
        return self.load()

    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access to values.

        Args:
            key: Key to retrieve

        Returns:
            The value at the specified key

        Raises:
            KeyError: If the key doesn't exist
        """
        value = self.get(key)
        if value is None and key not in self.get_all():
            raise KeyError(f"Key '{key}' not found in YAML file: {self.file_path}")
        return value

    def __contains__(self, key: str) -> bool:
        """Check if a key exists in the YAML data.

        Args:
            key: Key to check (supports dot notation)

        Returns:
            True if key exists, False otherwise
        """
        return self.get(key, sentinel := object()) is not sentinel

    def exists(self) -> bool:
        """Check if the YAML file exists on disk.

        Returns:
            True if file exists, False otherwise
        """
        return self.file_path.exists()

    def is_loaded(self) -> bool:
        """Check if the YAML data has been loaded.

        Returns:
            True if data is loaded, False otherwise
        """
        return self._data is not None

    def validate_structure(self, required_keys: list) -> bool:
        """Validate that the YAML file contains required top-level keys.

        Args:
            required_keys: List of required top-level keys

        Returns:
            True if all required keys exist, False otherwise

        Example:
            loader.validate_structure(['stations', 'defaults'])
        """
        if self._data is None:
            self.load()

        return all(key in self._data for key in required_keys)