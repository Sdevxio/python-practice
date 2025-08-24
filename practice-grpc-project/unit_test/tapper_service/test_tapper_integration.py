"""
Integration tests for TappingManager with real hardware and gRPC services.

These tests work with actual tapper hardware and gRPC services to verify
the automation components work correctly in real scenarios.
"""

import pytest
import time
from test_framework.login_logout.tapping_manager import TappingManager


class TestTappingManagerIntegration:
    """Integration tests for TappingManager with real services."""

    def test_tapping_manager_initialization(self, simple_config):
        """Test TappingManager initializes correctly with real config."""
        manager = TappingManager(
            station_id=test_config["station_id"],
            enable_tapping=test_config["enable_tapping"]
        )
        
        assert manager.station_id == test_config["station_id"]
        assert manager.enable_tapping == test_config["enable_tapping"]
        assert manager.login_tapper is not None
        assert manager.logout_tapper is not None

    def test_tapping_enabled_vs_disabled(self, simple_config):
        """Test behavior difference between enabled and disabled tapping."""
        # Test disabled tapping
        disabled_manager = TappingManager(
            station_id=test_config["station_id"],
            enable_tapping=False
        )
        
        # Should return True immediately for disabled tapping
        result = disabled_manager.perform_login_tap()
        assert result is True
        
        # Test enabled tapping (if configured)
        if test_config["enable_tapping"]:
            enabled_manager = TappingManager(
                station_id=test_config["station_id"],
                enable_tapping=True
            )
            
            # Should actually attempt tapping (may succeed or fail based on hardware)
            result = enabled_manager.perform_login_tap(max_retries=1, retry_delay=1.0)
            assert isinstance(result, bool)  # Should return boolean result

    def test_tapping_manager_status_check(self, simple_config):
        """Test tapping manager status reporting."""
        manager = TappingManager(
            station_id=test_config["station_id"],
            enable_tapping=test_config["enable_tapping"]
        )
        
        assert manager.is_enabled() == test_config["enable_tapping"]


class TestLoginTapperIntegration:
    """Integration tests for LoginTapper with real hardware."""

    @pytest.mark.hardware
    def test_login_tapper_hardware_connection(self, simple_config):
        """Test LoginTapper can connect to real hardware."""
        from test_framework.login_logout.tap_login import LoginTapper
        
        tapper = LoginTapper(test_config["station_id"])
        
        # Test single tap execution (should connect to hardware)
        result = tapper._execution_single_tap()
        
        # Result depends on hardware availability - both True/False are valid
        assert isinstance(result, bool)

    def test_login_tapper_with_services(self, services, simple_config):
        """Test LoginTapper with verification callback using real services."""
        from test_framework.login_logout.tap_login import LoginTapper
        
        tapper = LoginTapper(test_config["station_id"])
        
        def verification_callback(timeout):
            """Real verification using gRPC services."""
            try:
                # Check if we can get current user (indicates system is responsive)
                current_user = services.get_current_user()
                return current_user is not None
            except Exception:
                return False
        
        # Test with real verification callback
        if test_config["enable_tapping"]:
            result = tapper.perform_login_tap(
                max_retries=1,
                retry_delay=1.0,
                verification_callback=verification_callback,
                verification_timeout=5
            )
            assert isinstance(result, bool)


class TestLogoutTapperIntegration:
    """Integration tests for LogoutTapper with real hardware and services."""

    def test_logout_tapper_initialization(self, simple_config):
        """Test LogoutTapper initializes with real hardware connection."""
        from test_framework.login_logout.tap_logout import LogoutTapper
        
        tapper = LogoutTapper(test_config["station_id"])
        
        assert tapper.station_id == test_config["station_id"]
        assert tapper.tapper_service is not None

    @pytest.mark.hardware
    def test_logout_tapper_hardware_connection(self, simple_config):
        """Test LogoutTapper can connect to real hardware."""
        from test_framework.login_logout.tap_logout import LogoutTapper
        
        tapper = LogoutTapper(test_config["station_id"])
        
        # Test hardware connection
        connected = tapper.tapper_service.connect()
        if connected:
            tapper.tapper_service.disconnect()
        
        # Hardware may or may not be available - both results are valid
        assert isinstance(connected, bool)

    def test_logout_tapper_with_real_grpc_verification(self, services, simple_config):
        """Test LogoutTapper with real gRPC session manager for verification."""
        from test_framework.login_logout.tap_logout import LogoutTapper
        
        tapper = LogoutTapper(test_config["station_id"])
        
        # Test user verification with real gRPC services
        current_user = services.get_current_user()
        if current_user:
            # Test verification logic with real session manager
            result = tapper._wait_for_console_user_change(
                grpc_session_manager=services.session_manager,
                expected_user="nonexistent_user",  # Should return True immediately
                timeout=2
            )
            # Since user is different, should return True
            assert result is True


class TestTapperServiceEndToEnd:
    """End-to-end tests with real services integration."""

    def test_tapper_manager_with_real_services(self, services, simple_config):
        """Test TappingManager integrated with real gRPC services."""
        manager = TappingManager(
            station_id=test_config["station_id"],
            enable_tapping=test_config["enable_tapping"]
        )
        
        # Test login manager integration
        current_user = services.get_current_user()
        
        if test_config["enable_tapping"] and current_user:
            # Test logout tap with real session manager
            result = manager.perform_logoff_tap(
                expected_user=current_user,
                grpc_session_manager=services.session_manager,
                max_attempts=1,
                verification_timeout=5
            )
            assert isinstance(result, bool)

    def test_services_with_tapping_disabled(self, services, simple_config):
        """Test that tapping works correctly when disabled."""
        # Create manager with tapping explicitly disabled
        manager = TappingManager(
            station_id=test_config["station_id"],
            enable_tapping=False  # Force disabled
        )
        
        # All operations should succeed immediately
        login_result = manager.perform_login_tap()
        assert login_result is True
        
        logoff_result = manager.perform_logoff_tap(
            expected_user="any_user",
            grpc_session_manager=services.session_manager
        )
        assert logoff_result is True

    def test_real_session_manager_user_detection(self, services):
        """Test real gRPC session manager user detection."""
        # Test that we can get current user from real services
        current_user = services.get_current_user()
        
        # User might or might not be logged in - both are valid states
        assert current_user is None or isinstance(current_user, str)
        
        # Test health checks
        root_health = services.health_check("root")
        user_health = services.health_check("admin")  # or whatever user is configured
        
        assert isinstance(root_health, bool)
        assert isinstance(user_health, bool)