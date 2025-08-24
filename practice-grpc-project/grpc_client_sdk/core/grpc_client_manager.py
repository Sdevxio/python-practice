from typing import Dict, Any, Optional

from grpc_client_sdk.core.grpc_client import GrpcClient
from test_framework.utils import get_logger


class GrpcClientManager:
    """
    Registry and accessor for global gRPC clients.
    This class manages the lifecycle of gRPC clients, allowing for
    registration, retrieval, and stub creation for different services.
    It is designed to be a singleton.
    The class is thread-safe and ensures that each client is only registered once.
    Clients are stored in a dictionary.

    Attributes:
        _clients (Dict[str, GrpcClient]): Dictionary mapping client names to GrpcClient instances.
        _logger (Logger): Logger instance for logging messages.

    Example usage:
        GrpcClientManager.register_clients("root", "localhost:50051")
        root_client = GrpcClientManager.get_client("root")
        stub = GrpcClientManager.get_stub("root", SomeServiceStub)
    """
    _clients: Dict[str, GrpcClient] = {}
    _logger = get_logger('grpc_client_manager')

    @classmethod
    def register_clients(cls, name: str, target: str) -> bool:
        """
        Register a new gRPC client with specified name and target.

        :param name: Logical name of the client (e.g., "root", "username")
        :param target: host:port of the gRPC server (e.g., "localhost:50051")
        :return: True if the client was successfully registered, False otherwise.
        """
        if name in cls._clients:
            cls._logger.info(f"Client '{name}' already registered.")
            return True

        host, port = target.split(":")
        client = GrpcClient(host=host, port=int(port))

        # Try to connect
        if not client.connect():
            cls._logger.error(f"Failed to connect client {name} at: '{target}'")
            if name == "root":
                cls._logger.critical("Root service unavailable. Tests may fail.")
            return False

        # Store the connected client
        cls._clients[name] = client
        cls._logger.info(f"Successfully registered client '{name}' at {host}:{client.actual_port}.")
        return True

    @classmethod
    def get_client(cls, name: str) -> Optional[GrpcClient]:
        """
        Retrieve the gRPC client instance by name.

        :param name: Logical name of the client (e.g., 'root', 'username').
        :return: GrpcClient instance associated with the name, or None if not found.
        """
        if name not in cls._clients:
            cls._logger.error(f"gRPC client '{name}' is not registered")
            return None

        return cls._clients[name]

    @classmethod
    def get_stub(cls, name: str, stub_class: Any) -> Any:
        """
        Retrieve a gRPC service stub from the registered client.

        :param name: Registered client name.
        :param stub_class: gRPC-generated stub class.
        :return: Instantiated stub for the specified service.
        :raises RuntimeError: If client is not registered or not connected

        Example:
            stub = GrpcClientManager.get_stub("root", SomeServiceStub)
            response = stub.SomeMethod(request)
        """
        client = cls.get_client(name)
        if not client:
            raise RuntimeError(f"gRPC client '{name}' is not registered")
        try:
            # Check if client is still connected, attempt reconnect if not
            if not client.is_connected():
                cls._logger.warning(f"Client '{name}' disconnected, attempting to reconnect...")
                if not client.connect():
                    raise RuntimeError(f"Failed to reconnect client '{name}'")
                cls._logger.info(f"Successfully reconnected client '{name}'")

            return client.get_stubs(stub_class)
        except RuntimeError as e:
            cls._logger.error(f"Failed to get stub {stub_class.__name__} for client '{name}': {e}")
            raise

    @classmethod
    def remove_client(cls, name: str) -> bool:
        """
        Remove a specific client by name.
        
        :param name: Name of the client to remove
        :return: True if client was removed, False if not found
        """
        if name in cls._clients:
            client = cls._clients[name]
            try:
                # Close the connection gracefully
                if hasattr(client, 'channel') and client.channel:
                    client.channel.close()
            except Exception as e:
                cls._logger.warning(f"Error closing connection for client '{name}': {e}")
            
            del cls._clients[name]
            cls._logger.info(f"Removed client '{name}'")
            return True
        else:
            cls._logger.warning(f"Client '{name}' not found for removal")
            return False

    @classmethod
    def clear(cls) -> None:
        """
        Clear all registered clients (mainly) for test teardown.
        """
        cls._clients.clear()
        cls._logger.info("Cleared all registered clients")