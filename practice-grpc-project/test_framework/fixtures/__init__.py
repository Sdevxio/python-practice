"""
Fixtures package for the test framework.

This package contains all pytest fixtures organized by domain:
- logging_fixtures: Global logging infrastructure
- config_fixtures: Test configuration  
- login_fixtures: LoginManager pytest fixtures

The fixtures are designed to be:
- Modular and focused on specific concerns
- Easy to import and use in tests
- Well-documented with clear usage examples
- Following proper pytest fixture patterns
"""

# Import logging fixtures
from .logging_fixtures import *

# Import configuration fixtures
from .config_fixtures import test_config

# Import login fixtures (following pytest patterns)
from .login_fixtures import (
    grpc_session_manager,
    login_adapter,
    login_manager, 
    clean_logout_state,
    logged_in_user,
    logged_in_testuser,
    login_state_manager,
    login_health_check,
    require_tapping
)

__all__ = [
    # Logging fixtures (from logging_fixtures.py)
    'setup_logging',
    'test_logger', 
    'debug_logger',
    
    # Configuration fixtures (from config_fixtures.py)
    'test_config',
    
    # Login fixtures (from login_fixtures.py)
    'grpc_session_manager',
    'login_adapter',
    'login_manager',
    'clean_logout_state',
    'logged_in_user',
    'logged_in_testuser', 
    'login_state_manager',
    'login_health_check',
    'require_tapping',
]