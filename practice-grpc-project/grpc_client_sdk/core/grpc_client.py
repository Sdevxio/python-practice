from logging import Logger
from typing import Optional, Any, Dict

import grpc

from test_framework.utils import get_logger


class GrpcClient:
    """
    Core gRPC client class for managing channels and services stubs.
    This class is responsible for creating and managing gRPC channels and service stubs.
    It provides methods to create channels, get service stubs, and manage the lifecycle of the client.
    It also handles connection retries and fallback ports for gRPC connections.
    Attributes:
        host (str): The hostname or IP address of the gRPC server.
        port (int): The port number of the gRPC server.
        logger (Logger): Logger instance for logging.
        channel (grpc.Channel): gRPC channel for communication with the server.
        stubs (Dict[str, Any]): Dictionary to hold service stubs.
        connected (bool): Flag indicating if the client is connected to the server.
        actual_port (int): The actual port used for connection.
    """

    DEFAULT_FALLBACK_PORTS = [50051, 50052, 50053, 55000, 55001]

    def __init__(self, host: str, port: int, logger: Optional[Logger] = None):
        """
        Initialize the gRPC client with the specified host and port.
        :param host: The hostname or IP address of the gRPC server.
        :param port: The port number of the gRPC server.
        :param logger: Optional logger instance for logging.

        If not provided, a default logger will be created.
        """
        self.host = host
        self.port = port
        self.logger = logger or get_logger('grpc_client')
        self.target = f"{self.host}:{self.port}"
        self.channel: Optional[grpc.Channel] = None
        self.stubs: Dict[str, Any] = {}
        self.connected = False
        self.actual_port = port

    def connect(self) -> bool:
        """
        Attempt to connect to the gRPC server.
        This method tries to establish a connection to the gRPC server using the specified host and port.
        If the connection fails, it will attempt to connect using a list of fallback ports.

        :return: True if the connection was successful, False otherwise.
        :raises Exception: Raises an exception if the connection fails.
        """
        # Get a list of ports to try, ensuring the specified port is tried first
        ports_to_try = [self.port]

        # Add other default ports if they're not already in the list
        for port in self.DEFAULT_FALLBACK_PORTS:
            if port != self.port and port not in ports_to_try:
                ports_to_try.append(port)

        # Track connection errors for logging
        connection_errors = []

        # Try each port
        for port in ports_to_try:
            target = f"{self.host}:{port}"

            try:
                self.logger.info(f"Attempting to connect to {target}")
                self.channel = grpc.insecure_channel(
                    target,
                    options=[
                        ("grpc.max_send_message_length", 100 * 1024 * 1024),  # 100MB
                        ("grpc.max_receive_message_length", 100 * 1024 * 1024),
                        ("grpc.keepalive_time_ms", 10000),
                        ("grpc.keepalive_timeout_ms", 5000),
                        ("grpc.keepalive_permit_without_calls", True),
                        ("grpc.http2.max_pings_without_data", 0),
                        ("grpc.http2.min_time_between_pings_ms", 10000),
                        ("grpc.http2.min_ping_interval_without_data_ms", 300000)
                    ]
                )

                # Try to establish connection with a timeout
                grpc.channel_ready_future(self.channel).result(timeout=5)

                # Connection successful
                self.channel = self.channel
                self.actual_port = port
                self.connected = True

                # If we connected to a different port than originally specified, log it
                if port != self.port:
                    self.logger.info(f"Connected to fallback port {port} instead of requested port {self.port}")

                self.logger.info(f"Successfully connected to gRPC server at {target}")
                return True

            except Exception as e:
                error_msg = f"Failed to connect to {target}: {str(e)}"
                self.logger.warning(error_msg)
                connection_errors.append(error_msg)

        # If we get here, all connection attempts failed
        error_summary = "\n".join(connection_errors)
        self.logger.error(f"Failed to connect to gRPC server at {self.host} on any port:\n{error_summary}")
        self.connected = False
        return False

    def is_connected(self) -> bool:
        """
        Check if the client is currently connected to the gRPC server.

        :return: True if connected, False otherwise.
        """
        if not self.connected or not self.channel:
            return False

        try:
            # Test the connection with a quick connectivity check
            grpc.channel_ready_future(self.channel).result(timeout=1)
            return True
        except Exception:
            self.connected = False
            return False

    def disconnect(self) -> None:
        """
        Disconnect from the gRPC server and clean up resources.
        """
        if self.channel:
            try:
                self.channel.close()
            except Exception as e:
                self.logger.warning(f"Error closing channel: {e}")

        self.channel = None
        self.connected = False
        self.stubs.clear()
        self.logger.info(f"Disconnected from {self.host}:{self.actual_port}")

    def get_stubs(self, stubs_class: Any) -> Any:
        """
        Get or create a stubs instance for the specified service class.
        This method checks if the stubs instance already exists in the dictionary.
        If it does, it returns the existing instance. If not, it creates a new instance
        and stores it in the dictionary.

        :param stubs_class: The class of the service stub to create.
        :return: RuntimeError if not connected to gRPC server.

        Example:
            stub = client.get_stubs(SomeServiceStub)
            response = stub.SomeMethod(request)
        """
        if not self.connected:
            raise RuntimeError(f"Cannot create stub: Not connected to gRPC server at {self.host}")

        name = stubs_class.__name__
        if name in self.stubs:
            return self.stubs[name]

        self.stubs[name] = stubs_class(self.channel)
        return self.stubs[name]