"""
Pure gRPC session management without tapping concerns.
"""
import logging
import time
from typing import Optional, Dict, Any

from grpc_client_sdk.core.grpc_client_manager import GrpcClientManager
from grpc_client_sdk.services.registry_service_client import RegistryServiceClient
from grpc_client_sdk.services.command_service_client import CommandServiceClient
from test_framework.grpc_session.context_builder import SessionContextBuilder
from test_framework.grpc_session.session_context import SessionContext
from test_framework.utils import get_logger
from test_framework.utils.loaders.station_loader import StationLoader


class GrpcSessionManager:
    """
    Enhanced gRPC session management with simple service access API.

    Provides both the original SessionContext approach and a new simple API:
    
    Original approach (still works):
        session = manager.create_session("admin")
        result = session.root_context.command.run_command("whoami")
    
    New simple API:
        manager.setup_user("admin") 
        result = manager.command("root").run_command("whoami")  # root-grpc-server
        result = manager.command("admin").run_command("whoami") # user-agent server
    
    Responsibilities:
    - Register root gRPC client based on station configs
    - Wait for expected user to log in
    - Discover the agent's gRPC port via RegistryService
    - Construct and return a fully connected SessionContext
    - Provide direct service access with simple API
    - Provide logged-in user information via command service
    """

    def __init__(self, station_id: str, logger: Optional[logging.Logger] = None):
        self.station_id = station_id
        self.logger = logger or get_logger(f"grpc_session_manager [{station_id}]")
        self.root_target = StationLoader().get_grpc_target(station_id)
        GrpcClientManager.register_clients(name="root", target=self.root_target)
        self.root_registry = RegistryServiceClient(client_name="root", logger=self.logger)
        self.root_command = CommandServiceClient(client_name="root", logger=self.logger)
        self._session_context: Optional[SessionContext] = None

    def create_session(self, expected_user: str, timeout: int = 30) -> SessionContext:
        """
        Create a gRPC session for the expected user.

        :param expected_user: Username expected to log in
        :param timeout: Time in seconds to wait for login
        :return: Fully initialized SessionContext
        """
        self.logger.info(f"Creating gRPC session for user '{expected_user}'")

        # Step 1: Connect to root registry and command service
        self._connect_to_root_services()

        # Step 2: Wait for user login
        agent_port = self._wait_for_agent_login(expected_user, timeout)

        # Step 3: Build session context
        session_context = self._build_session_context(expected_user, agent_port)
        self._session_context = session_context

        self.logger.info(f"gRPC session established for '{expected_user}'")
        return session_context

    def get_logged_in_users(self) -> Dict[str, Any]:
        """
        Get current logged-in users via root context command service.

        This is the correct way to get actual console user and logged-in users.
        """
        try:
            if self._session_context and self._session_context.root_context:
                # Use the session's root context if available
                result = self._session_context.root_context.command.get_logged_in_users()
                return result
            else:
                # Fallback to direct command service
                if not self.root_command.stub:
                    self.root_command.connect()
                result = self.root_command.get_logged_in_users()
                return result
        except Exception as e:
            self.logger.error(f"Failed to get logged in users: {e}")
            # Return empty result to avoid breaking verification
            return {"console_user": "", "logged_in_users": []}

    def _connect_to_root_services(self):
        """Connect to the root registry and command service."""
        self.logger.info("Connecting to root services...")
        self.root_registry.connect()
        self.root_command.connect()
        self.logger.info(f"Connected to root services: {self.root_target}")

    def _wait_for_agent_login(self, username: str, timeout: int, poll_interval: float = 1.0) -> int:
        """Wait for user login and return agent port."""
        self.logger.info(f"Waiting for user '{username}' to log in...")
        deadline = time.time() + timeout

        while time.time() < deadline:
            try:
                agents = self.root_registry.list_agents()
                usernames = [agent["username"] for agent in agents]

                if username in usernames:
                    agent_info = self.root_registry.get_agent(username)
                    if agent_info and "port" in agent_info:
                        self.logger.info(f"User '{username}' logged in on port {agent_info['port']}")
                        return agent_info["port"]

            except Exception as e:
                self.logger.warning(f"Error checking agent login: {e}")

            time.sleep(poll_interval)

        raise RuntimeError(f"Timeout: User '{username}' did not log in within {timeout}s")

    def _build_session_context(self, username: str, agent_port: int) -> SessionContext:
        """Build and return the session context."""
        self.logger.info(f"Building session context for '{username}'")

        session_context = SessionContextBuilder.build(
            username=username,
            agent_port=agent_port,
            host=self.root_target.split(":")[0],
            logger=self.logger
        )

        return session_context

    # =============================================================================
    # Simple API Methods - New Enhanced Interface
    # =============================================================================

    def setup_user(self, expected_user: str, timeout: int = 30) -> 'GrpcSessionManager':
        """
        Setup session for a specific user - simple API version.
        
        This is equivalent to create_session() but designed for method chaining
        and the simple API pattern.
        
        Args:
            expected_user: Username expected to log in
            timeout: Time in seconds to wait for login
            
        Returns:
            Self for method chaining
        """
        self.create_session(expected_user, timeout)
        return self

    def command(self, context: str):
        """
        Get command service for specified context.
        
        Args:
            context: Either "root" (system operations) or username (user operations)
            
        Returns:
            CommandServiceClient for the specified context
            
        Usage:
            result = manager.command("root").run_command("whoami")      # root-grpc-server
            result = manager.command("admin").run_command("whoami")     # user-agent server
        """
        if not self._session_context:
            raise RuntimeError("No session established. Call setup_user() first.")
        
        if context == "root":
            return self._session_context.root_context.command
        else:
            # For user contexts, use the user_context (user-agent server)
            return self._session_context.user_context.command

    def apple_script(self, context: str):
        """
        Get AppleScript service for specified context.
        
        Args:
            context: Either "root" (system operations) or username (user operations)
            
        Returns:
            AppleScriptServiceClient for the specified context
        """
        if not self._session_context:
            raise RuntimeError("No session established. Call setup_user() first.")
        
        if context == "root":
            return self._session_context.root_context.apple_script
        else:
            return self._session_context.user_context.apple_script

    def file_transfer(self, context: str):
        """
        Get file transfer service for specified context.
        
        Args:
            context: Either "root" (system operations) or username (user operations)
            
        Returns:
            FileTransferServiceClient for the specified context
        """
        if not self._session_context:
            raise RuntimeError("No session established. Call setup_user() first.")
        
        if context == "root":
            return self._session_context.root_context.file_transfer
        else:
            return self._session_context.user_context.file_transfer

    def screen_capture(self, context: str):
        """
        Get screen capture service for specified context.
        
        Args:
            context: Either "root" (system operations) or username (user operations)
            
        Returns:
            ScreenCaptureServiceClient for the specified context
        """
        if not self._session_context:
            raise RuntimeError("No session established. Call setup_user() first.")
        
        if context == "root":
            return self._session_context.root_context.screen_capture
        else:
            return self._session_context.user_context.screen_capture

    def logs_monitor_stream(self, context: str):
        """
        Get logs monitoring service for specified context.
        
        Args:
            context: Either "root" (system operations) or username (user operations)
            
        Returns:
            LogsMonitoringServiceClient for the specified context
        """
        if not self._session_context:
            raise RuntimeError("No session established. Call setup_user() first.")
        
        if context == "root":
            return self._session_context.root_context.logs_monitor
        else:
            return self._session_context.user_context.logs_monitor


    def grpc_connection(self, context: str):
        """
        Get connection service for specified context.

        Args:
            context: Either "root" (system operations) or username (user operations)

        Returns:
            ConnectionServiceClient for the specified context
        """
        if not self._session_context:
            raise RuntimeError("No session established. Call setup_user() first.")

        if context == "root":
            return self._session_context.root_context.connection
        else:
            return self._session_context.user_context.connection

    def gui_automation(self, context: str):
        """
        Get GUI automation service for specified context.
        
        Args:
            context: Either "root" (system operations) or username (user operations)
            
        Returns:
            GuiAutomationServiceClient for the specified context
        """
        if not self._session_context:
            raise RuntimeError("No session established. Call setup_user() first.")
        
        if context == "root":
            return self._session_context.root_context.gui_automation
        else:
            return self._session_context.user_context.gui_automation

    def registry(self, context: str):
        """
        Get registry service for specified context.
        
        Args:
            context: Either "root" (system operations) or username (user operations)
            
        Returns:
            RegistryServiceClient for the specified context
        """
        if not self._session_context:
            raise RuntimeError("No session established. Call setup_user() first.")
        
        if context == "root":
            return self._session_context.root_context.registry
        else:
            return self._session_context.user_context.registry

    def web_automation(self, context: str):
        """
        Get web automation service for specified context.
        
        Args:
            context: Either "root" (system operations) or username (user operations)
            
        Returns:
            WebAutomationClient for the specified context
        """
        if not self._session_context:
            raise RuntimeError("No session established. Call setup_user() first.")
        
        if context == "root":
            return self._session_context.root_context.web_automation
        else:
            return self._session_context.user_context.web_automation

    def health_check(self, context: str) -> bool:
        """
        Perform health check for specified context.
        
        Args:
            context: Either "root" or username
            
        Returns:
            True if context is healthy, False otherwise
        """
        try:
            if context == "root":
                # Test root connection
                if not self.root_command.stub:
                    self.root_command.connect()
                result = self.root_command.run_command("echo", ["test"])
                return result.exit_code == 0
            else:
                # Test user context if available
                if self._session_context:
                    result = self._session_context.user_context.command.run_command("echo", ["test"])
                    return result.exit_code == 0
                return False
        except Exception:
            return False

    def get_current_user(self) -> Optional[str]:
        """
        Get the currently logged in console user.
        
        Returns:
            Username of console user, or None if no user or error
        """
        user_info = self.get_logged_in_users()
        console_user = user_info.get("console_user", "")
        return console_user if console_user and console_user != "root" else None

    # =============================================================================
    # Compatibility and Utility Methods
    # =============================================================================

    def get_session_info(self) -> Dict[str, Any]:
        """
        Get information about current session state.
        
        Returns:
            Dictionary with session information
        """
        if not self._session_context:
            return {
                "session_active": False,
                "username": None,
                "agent_port": None,
                "root_target": self.root_target
            }
        
        return {
            "session_active": True,
            "username": self._session_context.username,
            "agent_port": self._session_context.agent_port,
            "root_target": self.root_target,
            "available_contexts": ["root", self._session_context.username]
        }