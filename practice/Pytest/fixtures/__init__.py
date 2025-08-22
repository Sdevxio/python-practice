# Import main fixtures for easy access
from test_framework.fixtures.service_fixtures import (
    service_manager,
    fresh_service_manager,
    command_service,
    apple_script_service,
    file_transfer_service,
    screen_capture_service,
    logs_monitor_service,
    user_services,
    root_services,
    service_health_check,
    service_info,
    multi_context_test_helper,
    custom_context_manager
)
from test_framework.grpc_service_manager.service_manager import ServiceManager, create_service_manager, \
    get_quick_command_service
from .service_fixtures import service_health_check

__all__ = [
    # Core classes
    'ServiceManager',
    'create_service_manager',
    'get_quick_command_service',

    # Main fixtures
    'service_manager',
    'fresh_service_manager',

    # Direct service fixtures
    'command_service',
    'apple_script_service',
    'file_transfer_service',
    'screen_capture_service',
    'logs_monitor_service',

    # Context-specific fixtures
    'user_services',
    'root_services',

    # Utility fixtures
    'service_health_check',
    'service_info',
    'multi_context_test_helper',
    'custom_context_manager'
]

# Version info
__version__ = "1.0.0"
__author__ = "Test Framework Team"
__description__ = "Simple gRPC service management without session complexity"
