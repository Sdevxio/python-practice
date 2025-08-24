from typing import Optional

from generated import connection_service_pb2
from generated.connection_service_pb2_grpc import ConnectionServiceStub

from grpc_client_sdk.core.grpc_client_manager import GrpcClientManager
from test_framework.utils import get_logger


class ConnectionServiceClient:
    """
    ConnectionServiceClient is a gRPC client wrapper for interacting with the
    ConnectionService exposed by the macOS gRPC server (root or user agent).
    Supports operations:
    - Establishing a connection to the gRPC server.
    - Retrieving system-level metadata such as hostname, OS version, uptime.
    - Extracting the current logged-in user via hostname resolution.

    Typical use cases:
    - Confirming the gRPC server is live.
    - Validating the user session post-login.
    - Retrieving basic diagnostics from root or user gRPC context.

    Attributes:
        client_name (str): Logical name of the gRPC context ("root" or "username").
        logger (Logger): Instance-specific logger for structured outputs.
        stub (ConnectionServiceStub): gRPC stub generated from proto.

    Usage:
        client = ConnectionServiceClient(client_name="root")
        client.connect()
        logged_in_user = client.get_logged_in_username()
        print(logged_in_user)  # Should print the logged-in username
    """

    def __init__(self, client_name: str = 'root', logger: Optional[object] = None):
        """
        Initializes the ConnectionServiceClient.

        :param client_name: Name of the gRPC client in GrpcClientManager.
        :param logger: Custom logger instance. If None, a default logger is created.
        :raises RuntimeError: If the underlying client is not registered in GrpcClientManager.
        """
        self.client_name = client_name
        self.logger = logger or get_logger(f"ConnectionServiceClient-{client_name}")
        self.stub: Optional[ConnectionServiceStub] = None

    def connect(self):
        """
        Establishes the gRPC connection and stub for ConnectionService.
        """
        self.stub = GrpcClientManager.get_stub(self.client_name, ConnectionServiceStub)

    def get_logged_in_username(self) -> Optional[str]:
        """
        Extracts system information from the server, such as hostname, OS version, and uptime,
        available services, and IP address.
        This method is typically used to confirm the gRPC server is live and to validate the user session post-login.

        :return: The logged-in username or None if not available.

        Example:
            client = ConnectionServiceClient(client_name="root")
            client.connect()
            logged_in_user = client.get_logged_in_username()
            print(logged_in_user)
        """
        try:
            info = self.get_server_info()
            return info.get("logged_in_user")
        except Exception as e:
            self.logger.error("Failed to get logged-in username: %s", e)
            return None

    def get_server_info(self) -> Optional[dict]:
        """
        Retrieve system information from the server, such as hostname, OS version, and uptime,
        available services, and IP address.
        This is a non-intrusive way to validate server readiness, health and metadata.

        :return: A dictionary containing system information or None if retrieval failed.

        Example:
            client = ConnectionServiceClient(client_name="root")
            client.connect()
            server_info = client.get_server_info()
            print(server_info)
        """
        if not self.stub:
            raise RuntimeError("ConnectionServiceClient not connected. Call connect() first.")
        try:
            response = self.stub.GetServerInfo(connection_service_pb2.ServerInfoRequest())
            return {
                "hostname": response.hostname,
                "os_version": response.os_version,
                "ip_address": response.ip_address,
                "logged_in_user": response.logged_in_user,
                "username": response.username,
                "available_services": response.available_services,
            }
        except Exception as e:
            self.logger.error("Failed to get server info: %s", e)
            return None