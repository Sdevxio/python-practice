"""
🎯 LoginManager Pytest Fixtures - Clean Login/Logout for Tests

This provides clean pytest fixtures for login/logout functionality using
the simplified LoginManager architecture.

Key Features:
- Uses ServiceManager for all gRPC operations
- Automatic test setup/teardown for login state
- Configurable station targeting
- Clean integration with existing test patterns

Usage in tests:
    def test_something_with_user_login(login_manager, logged_in_user):
        # Test runs with user already logged in
        # Automatic logout happens after test
        pass
        
    def test_something_with_clean_state(login_manager):
        # Test runs with clean logout state
        # Manual login control if needed
        pass
"""

import pytest
from typing import Optional
from test_framework.grpc_service_manager.service_manager import ServiceManager
from test_framework.loging_manager.login_manager import LoginManager, create_login_manager
from test_framework.utils import get_logger


@pytest.fixture(scope="session")
def login_manager(service_manager: ServiceManager) -> LoginManager:
    """
    Session-scoped LoginManager fixture.
    
    Provides a LoginManager instance that can be used throughout test sessions.
    Uses the ServiceManager fixture for gRPC operations.
    
    Returns:
        LoginManager instance
    """
    # Get station configuration from environment or config
    # For now, using None (tapping disabled) - can be configured later
    station_id = None  # TODO: Get from test configuration
    enable_tapping = False  # TODO: Get from test configuration
    
    login_mgr = create_login_manager(
        service_manager=service_manager,
        station_id=station_id,
        enable_tapping=enable_tapping
    )
    
    yield login_mgr
    
    # Cleanup: Ensure we don't leave anyone logged in
    try:
        current_user = login_mgr.get_current_user()
        if current_user:
            login_mgr.ensure_logged_out(current_user)
    except Exception as e:
        logger = get_logger("login_manager_fixture")
        logger.warning(f"Failed to cleanup login state: {e}")


@pytest.fixture(scope="function")
def clean_logout_state(login_manager: LoginManager):
    """
    Function-scoped fixture that ensures clean logout state before and after test.
    
    This fixture:
    1. Logs out any current user before the test starts
    2. Yields control to the test
    3. Logs out any current user after the test finishes
    
    Use this when you need a guaranteed clean state for your test.
    """
    logger = get_logger("clean_logout_fixture")
    
    # Setup: Ensure clean logout state before test
    current_user = login_manager.get_current_user()
    if current_user:
        logger.info(f"🧹 Cleaning up logged in user '{current_user}' before test")
        login_manager.ensure_logged_out(current_user)
    
    yield login_manager
    
    # Teardown: Ensure clean logout state after test
    current_user = login_manager.get_current_user()
    if current_user:
        logger.info(f"🧹 Cleaning up logged in user '{current_user}' after test")
        login_manager.ensure_logged_out(current_user)


@pytest.fixture(scope="function")
def logged_in_user(login_manager: LoginManager, request):
    """
    Function-scoped fixture that ensures a specific user is logged in.
    
    This fixture:
    1. Logs in the specified user before the test
    2. Yields the username to the test
    3. Logs out the user after the test finishes
    
    Usage:
        @pytest.mark.parametrize("logged_in_user", ["testuser"], indirect=True)
        def test_with_logged_in_user(logged_in_user):
            # Test runs with 'testuser' logged in
            assert logged_in_user == "testuser"
    
    Or use the helper fixtures below for common users.
    """
    logger = get_logger("logged_in_user_fixture")
    
    # Get target user from test parameter
    target_user = getattr(request, 'param', 'testuser')  # Default to 'testuser'
    
    # Setup: Ensure target user is logged in
    logger.info(f"🔐 Ensuring user '{target_user}' is logged in for test")
    if not login_manager.ensure_logged_in(target_user):
        pytest.skip(f"Failed to log in user '{target_user}' - skipping test")
    
    yield target_user
    
    # Teardown: Ensure user is logged out
    logger.info(f"🚪 Logging out user '{target_user}' after test")
    login_manager.ensure_logged_out(target_user)


@pytest.fixture(scope="function")
def logged_in_testuser(login_manager: LoginManager):
    """
    Convenience fixture for tests that need 'testuser' logged in.
    
    This is equivalent to using logged_in_user with 'testuser' parameter.
    """
    logger = get_logger("logged_in_testuser_fixture")
    target_user = "testuser"
    
    # Setup: Ensure testuser is logged in
    logger.info(f"🔐 Ensuring user '{target_user}' is logged in for test")
    if not login_manager.ensure_logged_in(target_user):
        pytest.skip(f"Failed to log in user '{target_user}' - skipping test")
    
    yield target_user
    
    # Teardown: Ensure testuser is logged out
    logger.info(f"🚪 Logging out user '{target_user}' after test")
    login_manager.ensure_logged_out(target_user)


@pytest.fixture(scope="function")
def login_state_manager(login_manager: LoginManager):
    """
    Advanced fixture that provides full control over login state during test.
    
    This fixture yields the login_manager directly and handles cleanup,
    but gives the test full control over login/logout operations.
    
    Use this for complex tests that need to switch between users or
    test login/logout functionality directly.
    """
    logger = get_logger("login_state_manager_fixture")
    
    yield login_manager
    
    # Teardown: Ensure clean state after test
    current_user = login_manager.get_current_user()
    if current_user:
        logger.info(f"🧹 Cleaning up logged in user '{current_user}' after test")
        login_manager.ensure_logged_out(current_user)


# =============================================================================
# Helper Fixtures for Test Configuration
# =============================================================================

@pytest.fixture(scope="session")
def login_health_check(login_manager: LoginManager):
    """
    Session-scoped health check for LoginManager functionality.
    
    This runs once per test session to verify LoginManager is working.
    Tests will be skipped if health check fails.
    """
    logger = get_logger("login_health_check")
    
    if not login_manager.health_check():
        pytest.skip("LoginManager health check failed - skipping login/logout tests")
    
    logger.info("✅ LoginManager health check passed")
    return True


@pytest.fixture(scope="function")
def require_tapping(login_manager: LoginManager):
    """
    Fixture that skips tests if tapping is not available.
    
    Use this for tests that specifically require physical tapping functionality.
    """
    if not login_manager.enable_tapping:
        pytest.skip("Test requires tapping functionality which is not available")
    
    return login_manager


# =============================================================================
# Utility Functions for Test Helpers
# =============================================================================

def get_login_manager_info(login_manager: LoginManager) -> dict:
    """
    Get diagnostic information about LoginManager for debugging tests.
    
    Args:
        login_manager: LoginManager instance
        
    Returns:
        Dict with diagnostic information
    """
    return {
        "station_id": login_manager.station_id,
        "tapping_enabled": login_manager.enable_tapping,
        "current_user": login_manager.get_current_user(),
        "anyone_logged_in": login_manager.is_anyone_logged_in(),
        "health_status": login_manager.health_check()
    }


def assert_user_logged_in(login_manager: LoginManager, expected_user: str):
    """
    Test helper to assert a specific user is logged in.
    
    Args:
        login_manager: LoginManager instance
        expected_user: Username that should be logged in
        
    Raises:
        AssertionError: If user is not logged in
    """
    current_user = login_manager.get_current_user()
    assert current_user == expected_user, f"Expected user '{expected_user}' to be logged in, but found '{current_user}'"


def assert_no_user_logged_in(login_manager: LoginManager):
    """
    Test helper to assert no user is logged in.
    
    Args:
        login_manager: LoginManager instance
        
    Raises:
        AssertionError: If a user is logged in
    """
    current_user = login_manager.get_current_user()
    assert current_user is None, f"Expected no user to be logged in, but found '{current_user}'"