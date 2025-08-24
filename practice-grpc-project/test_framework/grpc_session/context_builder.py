"""
Session Context Builder.
This module provides a builder for creating session contexts that manage gRPC clients
"""
from grpc_client_sdk.core.grpc_client_manager import GrpcClientManager
from grpc_client_sdk.services.apple_script_service_client import AppleScriptServiceClient
from grpc_client_sdk.services.command_service_client import CommandServiceClient
from grpc_client_sdk.services.connection_service_client import ConnectionServiceClient
from grpc_client_sdk.services.file_transfer_service_client import FileTransferServiceClient
from grpc_client_sdk.services.screen_capture_service_client import ScreenCaptureServiceClient
from grpc_client_sdk.services.logs_monitor_stream_service_client import LogsMonitoringServiceClient
from grpc_client_sdk.services.gui_automation_service_client import GuiAutomationServiceClient
from grpc_client_sdk.services.registry_service_client import RegistryServiceClient
from grpc_client_sdk.services.web_automation_client import WebAutomationClient
from test_framework.grpc_session.service_context import ServiceContext
from test_framework.grpc_session.session_context import SessionContext


class SessionContextBuilder:

    @staticmethod
    def build(username: str, agent_port: int, host, logger) -> SessionContext:
        """Builds a session context for a given user and agent port.
        This method registers gRPC clients and initializes service contexts for both root and user levels.

        :args: username: The username for the session.
        :args: agent_port: The port number where the agent is running.
        :args: host: The host address of the agent.
        :args: logger: Logger instance for logging.
        :returns: A SessionContext object containing root and user service contexts.
        """
        # Register the user gRPC client using the dynamic port
        GrpcClientManager.register_clients(name=username, target=f"{host}:{agent_port}")
        logger.debug(f"Registered user client '{username}' at {host}:{agent_port}")  # DEBUG not INFO

        # Register root context services
        root = ServiceContext(client_name="root", logger=logger)
        for name, cls in [
            ("file_transfer", FileTransferServiceClient),
            ("command", CommandServiceClient),
            ("apple_script", AppleScriptServiceClient),
            ("connection", ConnectionServiceClient),
            ("logs_monitor", LogsMonitoringServiceClient),
            ("gui_automation", GuiAutomationServiceClient),
            ("registry", RegistryServiceClient),
            ("web_automation", WebAutomationClient),
        ]:
            try:
                root.register_service(name, cls)
            except Exception as e:
                logger.warning(f"Failed to register {name} service: {e}")

        # Register user context services
        user = ServiceContext(client_name=username, logger=logger)
        for name, cls in [
            ("file_transfer", FileTransferServiceClient),
            ("command", CommandServiceClient),
            ("apple_script", AppleScriptServiceClient),
            ("connection", ConnectionServiceClient),
            ("screen_capture", ScreenCaptureServiceClient),
            ("logs_monitor", LogsMonitoringServiceClient),
            ("gui_automation", GuiAutomationServiceClient),
            ("registry", RegistryServiceClient),
            ("web_automation", WebAutomationClient),
        ]:
            try:
                user.register_service(name, cls)
            except Exception as e:
                logger.warning(f"Failed to register {name} service: {e}")

        # Return the complete session context
        return SessionContext(
            username=username,
            agent_port=agent_port,
            root_context=root,
            user_context=user,
        )