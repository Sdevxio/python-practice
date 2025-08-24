"""
Service context for managing multiple services in a test framework.
This module provides a ServiceContext class that allows registering and accessing various services
dynamically. It is designed to facilitate interaction with different service clients in a structured manner.
"""
from typing import Type, Dict, Any

from test_framework.utils import get_logger


class ServiceContext:
    """
    Service context for managing multiple services.
    Encapsulates service clients available to a gRPC session context.
    This class allows for the registration and management of various service clients,
    enabling easy access to their functionalities.

    Attributes:
        client_name (str): Name of the client associated with this context.
        logger: Logger instance for logging.
        _services (Dict[str, Any]): Dictionary to hold registered services.

    Example:
        context = ServiceContext(client_name="example_client")
        context.register_service("command", CommandServiceClient)
        context.register_service("file_transfer", FileTransferServiceClient)
        command_service = context.get_service("command")
        command_service.run("ls -la")
        # Alternatively, access services as attributes
        command_service = context.command
        command_service.run("ls -la")
    """

    def __init__(self, client_name: str, logger=None):
        """
        Initialize the ServiceContext with a client name and an optional logger.

        :param client_name: The name of the client, typically the username or system context.
        :param logger: Optional logger instance for logging messages.
        """
        self.client_name = client_name
        self.logger = logger or get_logger(f"ServiceContext[{client_name}]")
        self._services: Dict[str, Any] = {}

    def register_service(self, name: str, service_class: Type):
        """
        Register a service with the context.
        This method instantiates the service class, connects it, and stores it in the context.

        :param name: The name to register the service under.
        :param service_class: The class of the service to instantiate and register.
        :raises KeyError: If the service name is already registered.
        """
        service = service_class(client_name=self.client_name, logger=self.logger)
        service.connect()
        self._services[name] = service

    def get_service(self, name: str):
        """Get a registered service by name."""
        if name in self._services:
            return self._services[name]
        raise KeyError(f"Service '{name}' not registered in context.")

    def __getattr__(self, item):
        """Allow access to services as attributes."""
        if item in self._services:
            return self._services[item]
        raise AttributeError(f"Service '{item}' not registered in context.")

    def __contains__(self, item):
        """Check if a service is registered in the context."""
        return item in self._services

    @property
    def services(self) -> Dict[str, Any]:
        """Get all registered services as a dictionary."""
        return self._services