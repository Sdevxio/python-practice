"""
🎯 ServiceManager - Clean Service Access Without Session Complexity

This replaces session_manager.py with a simple, efficient approach:
- Uses existing grpc_client_manager.py for connection management
- Uses existing service clients in grpc_client_sdk/services/  
- Provides clean context switching (user/root)
- Auto-connection and caching
- No session creation overhead

Key Benefits:
- Fast service addition - just add to ServiceManager
- Quick test creation - simple fixture usage
- Leverages existing infrastructure
- User/Root context flexibility
"""

from typing import Dict, Any, Optional
from grpc_client_sdk.core.grpc_client_manager import GrpcClientManager
from grpc_client_sdk.services.command_service_client import CommandServiceClient
from grpc_client_sdk.services.apple_script_service_client import AppleScriptServiceClient
from grpc_client_sdk.services.file_transfer_service_client import FileTransferServiceClient
from grpc_client_sdk.services.screen_capture_service_client import ScreenCaptureServiceClient
from grpc_client_sdk.services.logs_monitor_stream_service_client import LogsMonitoringServiceClient
from test_framework.utils import get_logger


class ServiceManager:
    """
    🎯 Simple Service Manager - Clean interface for all gRPC services.
    
    This class provides a clean, context-aware interface for accessing
    all gRPC services without complex session management.
    
    Key Features:
    - Auto-registration of standard contexts (root, user)
    - Auto-connection of service clients
    - Service client caching for performance
    - Clean API: services.command("user").run_command("whoami")
    - Uses 100% existing infrastructure
    
    Usage:
        services = ServiceManager()
        
        # Context-aware service access
        result = services.command("user").run_command("whoami")
        result = services.command("root").run_command("whoami")
        
        # Multiple services
        script_result = services.apple_script("user").run_applescript("return 'hello'")
        files = services.file_transfer("root")
    """
    
    def __init__(self, root_target: str = "localhost:50051", user_target: str = None):
        """
        Initialize ServiceManager with connection targets.
        
        Args:
            root_target: gRPC target for root context (e.g., "localhost:50051")
            user_target: gRPC target for user context (defaults to same as root)
        """
        self.root_target = root_target
        self.user_target = user_target or root_target
        self.logger = get_logger(self.__class__.__name__)
        
        # Cache for connected service clients
        self._service_cache: Dict[str, Any] = {}
        
        # Auto-register standard contexts
        self._register_standard_contexts()
        
        self.logger.info(f"🎯 ServiceManager initialized - root: {self.root_target}, user: {self.user_target}")
    
    def _register_standard_contexts(self):
        """Register standard gRPC client contexts."""
        try:
            # Register root context
            if not GrpcClientManager.register_clients("root", self.root_target):
                self.logger.warning(f"Failed to register root client at {self.root_target}")
            
            # Register user context (might be same target, different logical client)
            if not GrpcClientManager.register_clients("user", self.user_target):
                self.logger.warning(f"Failed to register user client at {self.user_target}")
                
            self.logger.info("✅ Standard contexts (root, user) registered successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to register standard contexts: {e}")
            # Continue anyway - services will handle connection failures gracefully
    
    def _get_or_create_service(self, service_type: str, context: str, service_class):
        """
        Get cached service client or create and connect new one.
        
        Args:
            service_type: Type of service (e.g., "command", "apple_script")
            context: Context name ("user" or "root")
            service_class: Service client class to instantiate
            
        Returns:
            Connected service client instance
        """
        cache_key = f"{service_type}_{context}"
        
        # Return cached service if available
        if cache_key in self._service_cache:
            return self._service_cache[cache_key]
        
        try:
            # Create new service client
            service_client = service_class(client_name=context, logger=self.logger)
            
            # Auto-connect
            service_client.connect()
            
            # Cache for reuse
            self._service_cache[cache_key] = service_client
            
            self.logger.debug(f"✅ Connected and cached {service_type} service for {context} context")
            return service_client
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create {service_type} service for {context}: {e}")
            raise
    
    def command(self, context: str = "user") -> CommandServiceClient:
        """
        Get command service for specified context.
        
        Args:
            context: Context to use ("user" or "root")
            
        Returns:
            Connected CommandServiceClient
            
        Usage:
            result = services.command("user").run_command("whoami")
            result = services.command("root").run_command("sudo whoami")
        """
        return self._get_or_create_service("command", context, CommandServiceClient)
    
    def apple_script(self, context: str = "user") -> AppleScriptServiceClient:
        """
        Get AppleScript service for specified context.
        
        Args:
            context: Context to use ("user" or "root")
            
        Returns:
            Connected AppleScriptServiceClient
            
        Usage:
            result = services.apple_script("user").run_applescript('return "hello"')
        """
        return self._get_or_create_service("apple_script", context, AppleScriptServiceClient)
    
    def file_transfer(self, context: str = "user") -> FileTransferServiceClient:
        """
        Get file transfer service for specified context.
        
        Args:
            context: Context to use ("user" or "root")
            
        Returns:
            Connected FileTransferServiceClient
            
        Usage:
            service = services.file_transfer("root")
            service.download_file("/path/to/remote", "/path/to/local")
        """
        return self._get_or_create_service("file_transfer", context, FileTransferServiceClient)
    
    def screen_capture(self, context: str = "user") -> ScreenCaptureServiceClient:
        """
        Get screen capture service for specified context.
        
        Args:
            context: Context to use ("user" or "root")
            
        Returns:
            Connected ScreenCaptureServiceClient
            
        Usage:
            service = services.screen_capture("user")
            service.capture_screen("/path/to/output.png")
        """
        return self._get_or_create_service("screen_capture", context, ScreenCaptureServiceClient)
    
    def logs_monitor_stream(self, context: str = "user") -> LogsMonitoringServiceClient:
        """
        Get logs monitoring service for specified context.
        
        Args:
            context: Context to use ("user" or "root")
            
        Returns:
            Connected LogsMonitoringServiceClient
            
        Usage:
            service = services.logs_monitor_stream("user")
            stream_id = service.stream_log_entries("/var/log/system.log")
        """
        return self._get_or_create_service("logs_monitor", context, LogsMonitoringServiceClient)
    
    def get_service_info(self) -> Dict[str, Any]:
        """
        Get information about available services and connections.
        
        Returns:
            Dict with service and connection information
        """
        return {
            "available_services": ["command", "apple_script", "file_transfer", "screen_capture", "logs_monitor_stream"],
            "available_contexts": ["user", "root"],
            "root_target": self.root_target,
            "user_target": self.user_target,
            "cached_services": list(self._service_cache.keys()),
            "active_connections": len(self._service_cache)
        }
    
    def health_check(self, context: str = "user") -> bool:
        """
        Perform a health check on services.
        
        Args:
            context: Context to test ("user" or "root")
            
        Returns:
            True if services are healthy, False otherwise
        """
        try:
            # Try a simple command to test connectivity
            command_service = self.command(context)
            result = command_service.run_command("echo", ["health_check"])
            
            # Check if command executed successfully
            is_healthy = result.exit_code == 0
            self.logger.info(f"🏥 Health check for {context}: {'✅ Healthy' if is_healthy else '❌ Unhealthy'}")
            return is_healthy
            
        except Exception as e:
            self.logger.error(f"❌ Health check failed for {context}: {e}")
            return False
    
    def disconnect_all(self):
        """
        Disconnect all cached service clients and clear cache.
        
        Call this during test teardown to clean up connections.
        """
        disconnected_count = 0
        
        for cache_key, service_client in self._service_cache.items():
            try:
                # Most service clients don't have explicit disconnect,
                # but the underlying gRPC clients will be managed by GrpcClientManager
                self.logger.debug(f"Cleaning up cached service: {cache_key}")
                disconnected_count += 1
            except Exception as e:
                self.logger.warning(f"Error cleaning up service {cache_key}: {e}")
        
        # Clear the cache
        self._service_cache.clear()
        
        # Clear the underlying gRPC clients
        GrpcClientManager.clear()
        
        self.logger.info(f"🔌 Disconnected {disconnected_count} services and cleared connections")
    
    def add_custom_context(self, context_name: str, target: str) -> bool:
        """
        Add a custom context for specialized testing.
        
        Args:
            context_name: Name for the custom context (e.g., "test_user", "admin")
            target: gRPC target for this context (e.g., "localhost:50052")
            
        Returns:
            True if context was registered successfully
            
        Usage:
            services.add_custom_context("admin", "localhost:50052")
            admin_result = services.command("admin").run_command("whoami")
        """
        try:
            if GrpcClientManager.register_clients(context_name, target):
                self.logger.info(f"✅ Custom context '{context_name}' registered at {target}")
                return True
            else:
                self.logger.warning(f"⚠️ Failed to register custom context '{context_name}' at {target}")
                return False
        except Exception as e:
            self.logger.error(f"❌ Error registering custom context '{context_name}': {e}")
            return False
    
    def __repr__(self):
        cached_services = len(self._service_cache)
        return f"ServiceManager(root={self.root_target}, user={self.user_target}, cached={cached_services})"
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure cleanup."""
        self.disconnect_all()


# =============================================================================
# Convenience Functions for Quick Access
# =============================================================================

def create_service_manager(root_target: str = "localhost:50051", user_target: str = None) -> ServiceManager:
    """
    Create a ServiceManager with standard configuration.
    
    Args:
        root_target: gRPC target for root context
        user_target: gRPC target for user context (defaults to same as root)
        
    Returns:
        Configured ServiceManager instance
    """
    return ServiceManager(root_target=root_target, user_target=user_target)


def get_quick_command_service(context: str = "user") -> CommandServiceClient:
    """
    Quick access to command service for simple use cases.
    
    Args:
        context: Context to use ("user" or "root")
        
    Returns:
        Connected CommandServiceClient
        
    Note: Creates a new ServiceManager each time - use main ServiceManager for efficiency
    """
    manager = create_service_manager()
    return manager.command(context)