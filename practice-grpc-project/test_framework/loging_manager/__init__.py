"""
LoginManager Module - Clean Tap-to-Login Architecture

This module provides a simplified, efficient approach to login/logout management
for macOS test automation, replacing the complex login_logout architecture.

Key Components:
- LoginManager: Core class for login/logout operations
- fixtures: Pytest fixtures for test integration
- Uses LoginServiceProvider for all gRPC operations
- Integrates with existing tapper hardware

Migration from old login_logout module:
- Replace TappingManager -> LoginManager
- Replace complex session-based approach -> simple ensure_logged_in/out methods
- Use LoginServiceProvider via adapter instead of grpc_session_manager
- Simplified pytest fixtures

Usage:
    from test_framework.loging_manager import LoginManager, create_login_manager
    
    # In tests
    def test_something(login_manager, logged_in_testuser):
        # Test runs with testuser logged in
        pass
"""

from .login_manager import LoginManager, create_login_manager

__all__ = [
    'LoginManager',
    'create_login_manager'
]