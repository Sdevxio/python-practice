"""
🧪 ServiceManager Fixtures - Clean Pytest Integration

Clean, simple fixtures using ServiceManager for efficient testing.
These fixtures replace complex session management with direct service access.
"""

import pytest
from typing import Dict, Any
from test_framework.grpc_service_manager.service_manager import ServiceManager, create_service_manager
from test_framework.utils import get_logger


# =============================================================================
# 🎯 Main ServiceManager Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def service_manager():
    """
    🎯 Main ServiceManager fixture - Use this for most tests!
    
    Provides session-scoped ServiceManager with auto-cleanup.
    All services are cached and reused within the test session.
    
    Usage:
        def test_command(service_manager):
            result = service_manager.command("user").run_command("whoami")
            assert result.exit_code == 0
    """
    manager = create_service_manager()
    yield manager
    manager.disconnect_all()


@pytest.fixture
def fresh_service_manager():
    """
    🔄 Fresh ServiceManager fixture - New instance per test.
    
    Use this when you need a clean ServiceManager for each test.
    Slightly slower but guarantees fresh connections.
    
    Usage:
        def test_fresh_connection(fresh_service_manager):
            # Each test gets a completely fresh ServiceManager
            result = fresh_service_manager.command("user").run_command("whoami")
    """
    manager = create_service_manager()
    yield manager
    manager.disconnect_all()


@pytest.fixture
def service_manager_custom_target():
    """
    🎛️ Custom target ServiceManager fixture.
    
    Factory fixture for custom gRPC targets.
    
    Usage:
        def test_custom_target(service_manager_custom_target):
            manager = service_manager_custom_target("localhost:50052")
            result = manager.command("user").run_command("whoami")
    """
    created_managers = []
    
    def _create_manager(root_target: str, user_target: str = None):
        manager = ServiceManager(root_target=root_target, user_target=user_target)
        created_managers.append(manager)
        return manager
    
    yield _create_manager
    
    # Cleanup all created managers
    for manager in created_managers:
        manager.disconnect_all()


# =============================================================================
# 🚀 Convenience Service Fixtures - Direct Service Access
# =============================================================================

@pytest.fixture
def command_service(service_manager):
    """
    📋 Command service fixture - Direct access to command service.
    
    Usage:
        def test_command(command_service):
            # Default user context
            result = command_service("user").run_command("whoami")
            
            # Root context
            result = command_service("root").run_command("whoami")
    """
    return service_manager.command


@pytest.fixture
def apple_script_service(service_manager):
    """
    🍎 AppleScript service fixture - Direct access to AppleScript service.
    
    Usage:
        def test_applescript(apple_script_service):
            result = apple_script_service("user").run_applescript('return "hello"')
    """
    return service_manager.apple_script


@pytest.fixture
def file_transfer_service(service_manager):
    """
    📁 File transfer service fixture - Direct access to file transfer.
    
    Usage:
        def test_file_transfer(file_transfer_service):
            service = file_transfer_service("root")
            service.download_file("/remote/path", "/local/path")
    """
    return service_manager.file_transfer


@pytest.fixture
def screen_capture_service(service_manager):
    """
    🖥️ Screen capture service fixture - Direct access to screen capture.
    
    Usage:
        def test_screen_capture(screen_capture_service):
            service = screen_capture_service("user")
            service.capture_screen("/path/to/screenshot.png")
    """
    return service_manager.screen_capture


@pytest.fixture
def logs_monitor_service(service_manager):
    """
    📋 Logs monitoring service fixture - Direct access to log monitoring.
    
    Usage:
        def test_logs_monitor(logs_monitor_service):
            service = logs_monitor_service("user")
            stream_id = service.stream_log_entries("/var/log/system.log")
    """
    return service_manager.logs_monitor_stream


# =============================================================================
# 🎯 Context-Specific Fixtures - Pre-configured Contexts
# =============================================================================

@pytest.fixture
def user_services(service_manager):
    """
    👤 User context services - All services pre-configured for user context.
    
    Returns object with all services ready to use in user context.
    
    Usage:
        def test_user_operations(user_services):
            result = user_services.command.run_command("whoami")
            script = user_services.apple_script.run_applescript('return "test"')
    """
    class UserServices:
        def __init__(self, manager: ServiceManager):
            self.command = manager.command("user")
            self.apple_script = manager.apple_script("user") 
            self.file_transfer = manager.file_transfer("user")
            self.screen_capture = manager.screen_capture("user")
            self.logs_monitor = manager.logs_monitor_stream("user")
    
    return UserServices(service_manager)


@pytest.fixture
def root_services(service_manager):
    """
    🔒 Root context services - All services pre-configured for root context.
    
    Returns object with all services ready to use in root context.
    
    Usage:
        def test_root_operations(root_services):
            result = root_services.command.run_command("whoami")
            files = root_services.file_transfer.download_file("/system/file")
    """
    class RootServices:
        def __init__(self, manager: ServiceManager):
            self.command = manager.command("root")
            self.apple_script = manager.apple_script("root")
            self.file_transfer = manager.file_transfer("root") 
            self.screen_capture = manager.screen_capture("root")
            self.logs_monitor = manager.logs_monitor_stream("root")
    
    return RootServices(service_manager)


# =============================================================================
# 🔧 Utility and Testing Fixtures
# =============================================================================

@pytest.fixture
def service_health_check(service_manager):
    """
    🏥 Service health check fixture - Skip tests if services unavailable.
    
    Automatically skips tests if gRPC services are not available.
    
    Usage:
        def test_requires_services(service_manager, service_health_check):
            # Test will be skipped if services are not healthy
            result = service_manager.command("user").run_command("whoami")
    """
    if not service_manager.health_check("user"):
        pytest.skip("gRPC services not available - skipping test")
    return True


@pytest.fixture
def service_info(service_manager):
    """
    📊 Service information fixture - Get service details.
    
    Returns information about available services and connections.
    
    Usage:
        def test_service_discovery(service_info):
            assert "command" in service_info["available_services"]
            assert len(service_info["cached_services"]) > 0
    """
    return service_manager.get_service_info()


@pytest.fixture
def multi_context_test_helper(service_manager):
    """
    🔄 Multi-context test helper - Easy context comparison testing.
    
    Provides helper for testing same operation across different contexts.
    
    Usage:
        def test_context_differences(multi_context_test_helper):
            results = multi_context_test_helper.run_command_in_all_contexts("whoami")
            assert results["user"].exit_code == 0
            assert results["root"].exit_code == 0
    """
    class MultiContextHelper:
        def __init__(self, manager: ServiceManager):
            self.manager = manager
        
        def run_command_in_all_contexts(self, command: str, args: list = None):
            """Run command in both user and root contexts."""
            return {
                "user": self.manager.command("user").run_command(command, args),
                "root": self.manager.command("root").run_command(command, args)
            }
        
        def run_applescript_in_all_contexts(self, script: str):
            """Run AppleScript in both user and root contexts."""
            return {
                "user": self.manager.apple_script("user").run_applescript(script),
                "root": self.manager.apple_script("root").run_applescript(script)
            }
    
    return MultiContextHelper(service_manager)


# =============================================================================
# 🎛️ Configuration and Setup Fixtures  
# =============================================================================

@pytest.fixture
def custom_context_manager(service_manager):
    """
    🎛️ Custom context manager - Add custom contexts for specialized testing.
    
    Factory for adding custom contexts during tests.
    
    Usage:
        def test_custom_context(custom_context_manager):
            custom_context_manager.add("admin", "localhost:50052")
            result = service_manager.command("admin").run_command("whoami")
    """
    class CustomContextManager:
        def __init__(self, manager: ServiceManager):
            self.manager = manager
            self.added_contexts = []
        
        def add(self, context_name: str, target: str) -> bool:
            """Add a custom context."""
            success = self.manager.add_custom_context(context_name, target)
            if success:
                self.added_contexts.append(context_name)
            return success
        
        def list_added(self) -> list:
            """List contexts added during this test."""
            return self.added_contexts.copy()
    
    return CustomContextManager(service_manager)


# =============================================================================
# 📝 Usage Examples and Documentation
# =============================================================================

"""
📝 FIXTURE USAGE EXAMPLES:

# Basic usage (recommended):
def test_basic_command(service_manager):
    result = service_manager.command("user").run_command("whoami")
    assert result.exit_code == 0

# Direct service access:
def test_command_service(command_service):
    result = command_service("user").run_command("ls", ["-la"])
    assert result.exit_code == 0

# Context-specific services:
def test_user_operations(user_services):
    result = user_services.command.run_command("whoami")
    script = user_services.apple_script.run_applescript('return "hello"')

def test_root_operations(root_services):
    result = root_services.command.run_command("whoami")
    # Should show root user

# Health check (auto-skip if services unavailable):
def test_with_health_check(service_manager, service_health_check):
    # Test automatically skipped if services are down
    result = service_manager.command("user").run_command("whoami")

# Multi-context testing:
def test_context_comparison(multi_context_test_helper):
    results = multi_context_test_helper.run_command_in_all_contexts("whoami")
    user_output = results["user"].stdout.strip()
    root_output = results["root"].stdout.strip()
    # Compare outputs...

# Custom contexts:
def test_custom_context(service_manager, custom_context_manager):
    custom_context_manager.add("test_user", "localhost:50053")
    result = service_manager.command("test_user").run_command("whoami")

# Fresh connections per test:
def test_fresh_connection(fresh_service_manager):
    # Completely fresh ServiceManager instance
    result = fresh_service_manager.command("user").run_command("whoami")

# Service information:
def test_service_info(service_info):
    assert "command" in service_info["available_services"]
    assert service_info["root_target"] == "localhost:50051"

# Custom targets:
def test_custom_target(service_manager_custom_target):
    manager = service_manager_custom_target("localhost:50052")
    result = manager.command("user").run_command("whoami")
"""