"""
Pytest fixtures for LoginManager integration

This module provides proper pytest fixtures following pytest design patterns:
- Clean dependency injection
- Proper fixture scoping
- Automatic setup and teardown
- Integration with existing test infrastructure
"""

import pytest
from test_framework.grpc_session.session_manager import GrpcSessionManager
from test_framework.loging_manager.grpc_session_login_adapter import create_login_adapter
from test_framework.loging_manager.login_manager import create_login_manager
from test_framework.utils import get_logger


@pytest.fixture(scope="function")
def grpc_session_manager(test_config):
    """
    Create GrpcSessionManager for use in login fixtures.
    
    This fixture creates a session manager that can be used independently
    of the services fixture to avoid circular dependencies.
    
    Args:
        test_config: Test configuration fixture
        
    Returns:
        GrpcSessionManager instance
        
    Usage:
        def test_something(grpc_session_manager):
            # Direct access to session manager
            pass
    """
    session_mgr = GrpcSessionManager(test_config["station_id"])
    expected_user = test_config["expected_user"]
    
    # Setup user session
    session_mgr.setup_user(expected_user, timeout=test_config["login_timeout"])
    
    return session_mgr


@pytest.fixture(scope="function")
def login_adapter(grpc_session_manager):
    """
    Create LoginServiceProvider adapter from session manager.
    
    Args:
        grpc_session_manager: GrpcSessionManager fixture
        
    Returns:
        GrpcSessionLoginAdapter that implements LoginServiceProvider interface
        
    Usage:
        def test_something(login_adapter):
            # login_adapter is ready to use with LoginManager
            pass
    """
    adapter = create_login_adapter(grpc_session_manager)
    return adapter


@pytest.fixture(scope="function") 
def login_manager(login_adapter, test_config):
    """
    Create LoginManager with proper configuration and cleanup.
    
    This fixture provides a fully configured LoginManager that:
    1. Uses the login_adapter for gRPC operations
    2. Configures station and tapping based on test configuration
    3. Handles automatic cleanup after tests
    
    Args:
        login_adapter: LoginServiceProvider adapter fixture
        test_config: Test configuration fixture
        
    Returns:
        Configured LoginManager instance
        
    Usage:
        def test_login_operations(login_manager):
            # LoginManager is ready for login/logout operations
            current_user = login_manager.get_current_user()
            assert login_manager.health_check()
    """
    logger = get_logger("login_manager_fixture")
    
    # Create LoginManager with proper configuration
    login_mgr = create_login_manager(
        service_manager=login_adapter,
        station_id=test_config.get("station_id"),
        enable_tapping=test_config.get("enable_tapping", True)
    )
    
    logger.info(f"✅ LoginManager created: {login_mgr}")
    
    yield login_mgr
    
    # Cleanup: Ensure no user is left logged in after test
    try:
        current_user = login_mgr.get_current_user()
        if current_user:
            logger.info(f"🧹 Cleaning up logged in user: {current_user}")
            login_mgr.ensure_logged_out(current_user)
    except Exception as e:
        logger.warning(f"Cleanup warning: {e}")


@pytest.fixture(scope="function")
def clean_logout_state(login_manager):
    """
    Ensure clean logout state before and after test.
    
    This fixture:
    1. Logs out any current user before the test starts
    2. Yields the login_manager for test use
    3. Logs out any current user after the test finishes
    
    Use this when you need a guaranteed clean state for your test.
    
    Args:
        login_manager: LoginManager fixture
        
    Returns:
        LoginManager with guaranteed clean logout state
        
    Usage:
        def test_clean_state(clean_logout_state):
            # Test starts with no user logged in
            login_mgr = clean_logout_state
            assert not login_mgr.is_anyone_logged_in()
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
def logged_in_user(login_manager, request):
    """
    Ensure a specific user is logged in during test.
    
    This fixture:
    1. Logs in the specified user before the test
    2. Yields the username to the test
    3. Logs out the user after the test finishes
    
    Usage with parametrize:
        @pytest.mark.parametrize("logged_in_user", ["testuser"], indirect=True)
        def test_with_logged_in_user(logged_in_user):
            # Test runs with 'testuser' logged in
            assert logged_in_user == "testuser"
    
    Args:
        login_manager: LoginManager fixture
        request: Pytest request object for parameterization
        
    Returns:
        Username of the logged in user
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
def logged_in_testuser(login_manager):
    """
    Convenience fixture for tests that need 'testuser' logged in.
    
    This is equivalent to using logged_in_user with 'testuser' parameter.
    
    Args:
        login_manager: LoginManager fixture
        
    Returns:
        The string 'testuser'
        
    Usage:
        def test_with_testuser(logged_in_testuser):
            # Test runs with 'testuser' logged in
            assert logged_in_testuser == "testuser"
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
def login_state_manager(login_manager):
    """
    Advanced fixture that provides full control over login state during test.
    
    This fixture yields the login_manager directly and handles cleanup,
    but gives the test full control over login/logout operations.
    
    Use this for complex tests that need to switch between users or
    test login/logout functionality directly.
    
    Args:
        login_manager: LoginManager fixture
        
    Returns:
        LoginManager instance with automatic cleanup
        
    Usage:
        def test_complex_login_flow(login_state_manager):
            login_mgr = login_state_manager
            
            # Manual control over login/logout
            login_mgr.ensure_logged_in("user1") 
            login_mgr.ensure_logged_out("user1")
            login_mgr.ensure_logged_in("user2")
            # Automatic cleanup after test
    """
    logger = get_logger("login_state_manager_fixture")
    
    yield login_manager
    
    # Teardown: Ensure clean state after test
    current_user = login_manager.get_current_user()
    if current_user:
        logger.info(f"🧹 Cleaning up logged in user '{current_user}' after test")
        login_manager.ensure_logged_out(current_user)


@pytest.fixture(scope="session")
def login_health_check(login_manager):
    """
    Session-scoped health check for LoginManager functionality.
    
    This runs once per test session to verify LoginManager is working.
    Tests will be skipped if health check fails.
    
    Args:
        login_manager: LoginManager fixture
        
    Returns:
        True if health check passed
        
    Usage:
        def test_requires_working_login(login_health_check):
            # Test only runs if LoginManager is healthy
            assert login_health_check
    """
    logger = get_logger("login_health_check")
    
    if not login_manager.health_check():
        pytest.skip("LoginManager health check failed - skipping login/logout tests")
    
    logger.info("✅ LoginManager health check passed")
    return True


@pytest.fixture(scope="function")
def require_tapping(login_manager):
    """
    Fixture that skips tests if tapping is not available.
    
    Use this for tests that specifically require physical tapping functionality.
    
    Args:
        login_manager: LoginManager fixture
        
    Returns:
        LoginManager instance (only if tapping is available)
        
    Usage:
        def test_needs_tapping(require_tapping):
            login_mgr = require_tapping
            # Test only runs if tapping is available
            assert login_mgr.enable_tapping
    """
    if not login_manager.enable_tapping:
        pytest.skip("Test requires tapping functionality which is not available")
    
    return login_manager