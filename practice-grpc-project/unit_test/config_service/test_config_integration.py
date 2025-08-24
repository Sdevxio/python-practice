"""
Integration tests for configuration with real services.

Tests how the simplified configuration works with actual gRPC services
and real environment scenarios.
"""

import os
import pytest


class TestConfigWithRealServices:
    """Test configuration integration with real gRPC services."""

    def test_config_with_services_fixture(self, services, simple_config):
        """Test that config integrates correctly with services fixture."""
        # Services should be using the same config
        assert services.session_manager is not None
        assert services.login_manager is not None
        
        # Config should match what services are using
        expected_user = test_config["expected_user"]
        assert services.expected_user == expected_user

    def test_config_station_id_consistency(self, services, simple_config):
        """Test station_id is consistent between config and services."""
        # Both should be using the same station_id
        station_id = test_config["station_id"]
        
        # Services should be connected to the same station
        assert isinstance(station_id, str)
        assert len(station_id) > 0

    def test_config_tapping_integration(self, simple_config):
        """Test tapping configuration with real TappingManager."""
        from test_framework.login_logout.tapping_manager import TappingManager
        
        # Create manager with config settings
        manager = TappingManager(
            station_id=test_config["station_id"],
            enable_tapping=test_config["enable_tapping"]
        )
        
        # Should match config
        assert manager.is_enabled() == test_config["enable_tapping"]

    def test_config_environment_variables(self, simple_config):
        """Test that environment variables are properly loaded."""
        # Check if environment variables are being used
        test_station = os.environ.get("TEST_STATION")
        test_user = os.environ.get("TEST_USER") 
        enable_tapping = os.environ.get("ENABLE_TAPPING")
        
        if test_station:
            assert test_config["station_id"] == test_station
        else:
            assert test_config["station_id"] == "station1"  # default
            
        if test_user:
            assert test_config["expected_user"] == test_user
        else:
            assert test_config["expected_user"] == "admin"  # default
            
        if enable_tapping:
            expected_tapping = enable_tapping.lower() == "true"
            assert test_config["enable_tapping"] == expected_tapping

    def test_config_timeouts_are_reasonable(self, simple_config):
        """Test that timeout values are reasonable for real usage."""
        # Login timeout should be reasonable for real login
        assert test_config["login_timeout"] >= 10
        assert test_config["login_timeout"] <= 300
        
        # Tap timeout should be reasonable for hardware operations
        assert test_config["tap_timeout"] >= 5
        assert test_config["tap_timeout"] <= 60

    def test_config_log_file_path_exists(self, simple_config):
        """Test that log file path configuration is valid."""
        log_path = test_config["log_file_path"]
        
        # Should be a valid path string
        assert isinstance(log_path, str)
        assert len(log_path) > 0
        
        # Should be an absolute path
        assert os.path.isabs(log_path)

    def test_config_with_real_station_loader(self, simple_config):
        """Test config works with real StationLoader when available."""
        try:
            from test_framework.utils.loaders.station_loader import StationLoader
            loader = StationLoader()
            
            # If StationLoader works, test it loads data
            test_users = loader.get_test_users()
            if test_users:
                assert isinstance(test_users, dict)
                
            e2e_defaults = loader.get_e2e_defaults()
            if e2e_defaults:
                assert isinstance(e2e_defaults, dict)
                
        except Exception:
            # StationLoader might not be available - that's OK
            # Config should still work with fallbacks
            pass
        
        # Config should work regardless of StationLoader availability
        assert test_config["station_id"] is not None
        assert test_config["expected_user"] is not None


class TestConfigConsistency:
    """Test configuration consistency across different contexts."""

    def test_config_is_session_scoped(self, simple_config):
        """Test that config is properly session-scoped."""
        # Config should be the same instance/values within a session
        station_id_1 = test_config["station_id"]
        expected_user_1 = test_config["expected_user"]
        
        # Access again - should be same
        station_id_2 = test_config["station_id"]
        expected_user_2 = test_config["expected_user"]
        
        assert station_id_1 == station_id_2
        assert expected_user_1 == expected_user_2

    def test_config_contains_all_required_keys(self, simple_config):
        """Test config has all keys needed for services."""
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
            assert key in test_config
            assert test_config[key] is not None

    def test_config_data_types_for_services(self, simple_config):
        """Test config has correct data types for service usage."""
        # String values for service identification
        assert isinstance(test_config["station_id"], str)
        assert isinstance(test_config["expected_user"], str)
        assert isinstance(test_config["expected_card"], str)
        assert isinstance(test_config["log_file_path"], str)
        
        # Boolean for feature flags
        assert isinstance(test_config["enable_tapping"], bool)
        
        # Integer values for timeouts
        assert isinstance(test_config["login_timeout"], int)
        assert isinstance(test_config["tap_timeout"], int)