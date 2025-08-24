
import pytest


def test_login_flow_basic(test_logger, services):
    """
    Basic test login flow with default configuration.
    
    This test uses the simple configuration approach without complex markers.
    Configuration is handled through environment variables and test_config fixture.
    """
    test_logger.info("Starting basic login flow test")
    
    # Access the configuration through services
    login_mgr = services.login_manager
    expected_user = services.expected_user
    
    test_logger.info(f"Testing with user: {expected_user}")
    test_logger.info(f"Station: {login_mgr.station_id}")
    test_logger.info(f"Tapping enabled: {login_mgr.enable_tapping}")
    
    # Verify current user matches expected
    current_user = login_mgr.get_current_user()
    assert current_user == expected_user, f"Expected {expected_user}, got {current_user}"
    
    # Test basic functionality
    assert services.health_check("root")
    assert services.health_check(expected_user)
    
    test_logger.info("✅ Basic login flow test completed")


def test_login_flow_with_tapping(test_logger, services, require_tapping):
    """
    Test login flow specifically requiring tapping functionality.
    
    Uses the require_tapping fixture to ensure tapping is available.
    """
    test_logger.info("Starting login flow test with tapping enabled")
    
    login_mgr = require_tapping  # This fixture ensures tapping is available
    expected_user = services.expected_user
    
    test_logger.info(f"Testing tapping-enabled flow with user: {expected_user}")
    test_logger.info(f"Station: {login_mgr.station_id}")
    test_logger.info(f"Tapping enabled: {login_mgr.enable_tapping}")
    
    # Verify tapping is actually enabled
    assert login_mgr.enable_tapping, "Tapping should be enabled for this test"
    
    # Test tapping-specific functionality
    current_user = login_mgr.get_current_user()
    if current_user != expected_user:
        # Demonstrate tapping login capability
        test_logger.info(f"Current user {current_user} != expected {expected_user}, testing login")
        success = login_mgr.ensure_logged_in(expected_user)
        assert success, f"Failed to log in {expected_user} using tapping"
    
    test_logger.info("✅ Tapping-enabled login flow test completed")


def test_login_flow(test_logger, services):
    """Original test with default configuration."""
    test_logger.info("Starting default login flow test")


