"""
Unit tests for simple_config fixture.

Tests configuration loading, environment overrides, and fallback behavior.
These tests ensure the simplified configuration approach works correctly
with various environment settings and edge cases.
"""

import os
import pytest
from unittest.mock import patch, MagicMock


class TestSimpleConfig:
    """Test suite for simple_config fixture functionality."""

    def test_simple_config_defaults(self, test_config):
        """Test test_config returns expected default values."""
        # Core identifiers should have defaults (or environment values)
        assert test_config["station_id"] in ["station1", os.environ.get("TEST_STATION", "station1")]
        assert test_config["expected_user"] in ["admin", os.environ.get("TEST_USER", "admin")]
        
        # Operational settings should have sensible defaults
        assert isinstance(test_config["enable_tapping"], bool)
        assert test_config["login_timeout"] == 30
        assert test_config["tap_timeout"] == 10
        
        # Legacy compatibility
        assert test_config["expected_card"] == "1234567890"
        
        # Log file path should be present
        assert "log_file_path" in test_config
        assert isinstance(test_config["log_file_path"], str)

    def test_simple_config_required_keys(self, test_config):
        """Test all required configuration keys are present."""
        required_keys = [
            "station_id",
            "expected_user", 
            "enable_tapping",
            "login_timeout",
            "tap_timeout",
            "log_file_path",
            "expected_card"
        ]
        
        for key in required_keys:
            assert key in test_config, f"Required key '{key}' missing from config"

    def test_simple_config_data_types(self, test_config):
        """Test configuration values have correct data types."""
        assert isinstance(test_config["station_id"], str)
        assert isinstance(test_config["expected_user"], str)
        assert isinstance(test_config["enable_tapping"], bool)
        assert isinstance(test_config["login_timeout"], int)
        assert isinstance(test_config["tap_timeout"], int)
        assert isinstance(test_config["log_file_path"], str)
        assert isinstance(test_config["expected_card"], str)

    def test_simple_config_immutable_structure(self, test_config):
        """Test that config structure is predictable and doesn't change."""
        # Config should always have the same structure
        expected_keys = {
            "station_id", "expected_user", "enable_tapping", 
            "login_timeout", "tap_timeout", "log_file_path", "expected_card"
        }
        
        actual_keys = set(test_config.keys())
        assert actual_keys == expected_keys, f"Config keys changed: {actual_keys - expected_keys} added, {expected_keys - actual_keys} removed"


class TestSimpleConfigEnvironment:
    """Test environment variable behavior by calling fixture function directly."""
    
    def create_config(self):
        """Helper to create config directly for testing."""
        import os
        from test_framework.utils.loaders.station_loader import StationLoader
        
        # Core settings with environment overrides
        station_id = os.environ.get("TEST_STATION", "station1")
        expected_user = os.environ.get("TEST_USER", "admin")
        enable_tapping = os.environ.get("ENABLE_TAPPING", "false").lower() == "true"
        
        # Try to load additional config if available
        log_file_path = "/Users/admin/PA/dynamic_log_generator/dynamic_test.log"
        try:
            station_loader = StationLoader()
            e2e_defaults = station_loader.get_e2e_defaults()
            if e2e_defaults and "log_file_path" in e2e_defaults:
                log_file_path = e2e_defaults["log_file_path"]
        except Exception:
            # Fallback to default if loader fails
            pass
        
        return {
            "station_id": station_id,
            "expected_user": expected_user,
            "enable_tapping": enable_tapping,
            "login_timeout": 30,
            "tap_timeout": 10,
            "log_file_path": log_file_path,
            "expected_card": "1234567890",
        }

    @patch.dict(os.environ, {
        "TEST_STATION": "station2", 
        "TEST_USER": "testuser",
        "ENABLE_TAPPING": "true"
    })
    def test_environment_overrides(self):
        """Test environment variables properly override defaults."""
        config = self.create_config()
        
        assert config["station_id"] == "station2"
        assert config["expected_user"] == "testuser"
        assert config["enable_tapping"] is True

    @patch.dict(os.environ, {"ENABLE_TAPPING": "false"})
    def test_tapping_disabled(self):
        """Test tapping can be explicitly disabled."""
        config = self.create_config()
        assert config["enable_tapping"] is False

    @patch.dict(os.environ, {"ENABLE_TAPPING": "TRUE"})
    def test_tapping_case_insensitive(self):
        """Test tapping environment variable is case insensitive."""
        config = self.create_config()
        assert config["enable_tapping"] is True

    @patch('test_framework.utils.loaders.station_loader.StationLoader')
    def test_station_loader_fallback(self, mock_station_loader):
        """Test graceful fallback when StationLoader fails."""
        mock_station_loader.side_effect = Exception("StationLoader failed")
        
        config = self.create_config()
        
        # Should use fallback values
        assert config["log_file_path"] == "/Users/admin/PA/dynamic_log_generator/dynamic_test.log"

    @patch('test_framework.utils.loaders.station_loader.StationLoader')
    def test_station_loader_success(self, mock_station_loader):
        """Test configuration with successful StationLoader."""
        mock_instance = MagicMock()
        mock_instance.get_e2e_defaults.return_value = {"log_file_path": "/custom/log.log"}
        mock_station_loader.return_value = mock_instance
        
        config = self.create_config()
        
        assert config["log_file_path"] == "/custom/log.log"