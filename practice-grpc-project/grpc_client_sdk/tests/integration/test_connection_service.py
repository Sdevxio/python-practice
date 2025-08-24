from grpc_client_sdk.core.grpc_client_manager import GrpcClientManager
from grpc_client_sdk.services.connection_service_client import ConnectionServiceClient


def test_get_server_info(setup):
    """
    Test the ConnectionServiceClient for retrieving server information.
    get_server_info() method is used to fetch system-level metadata such as hostname,
    OS version, uptime, available services, and IP address.

    :param setup: Fixture that sets up the gRPC client and server.
    """
    # Register the client with the GrpcClientManager
    target = setup
    GrpcClientManager.register_clients(name="root", target=target)

    # Get the registered client
    client = GrpcClientManager.get_client("root")
    assert client is not None, "Client should be registered and connected"
    #
    # # Create a CommandServiceClient instance
    connection_client = ConnectionServiceClient(client_name="root")
    # Connect to the gRPC server
    connection_client.connect()

    # Test if the client can retrieve server information
    server_info = connection_client.get_server_info()
    print(f"Server info: {server_info}")
    assert server_info is not None, "Failed to retrieve server information"
    assert "hostname" in server_info, "Hostname not found in server information"
    assert "os_version" in server_info, "OS version not found in server information"
    assert "ip_address" in server_info, "IP address not found in server information"
    assert "available_services" in server_info, "Available services not found in server information"

    expected_services = [
        "ConnectionService",
        "ScreenCaptureService",
        "AppleScriptService",
        "FileTransferService",
        "RegistryServiceService",
    ]
    assert sorted(server_info["available_services"]) == sorted(expected_services), (
        "Available services do not match the expected services"
    )


def test_get_logged_in_username(setup):
    """
    Test the ConnectionServiceClient for retrieving the logged-in username.
    get_logged_in_username() method is used to fetch the current logged-in user
    via hostname resolution.

    :param setup: Fixture that sets up the gRPC client and server.
    """
    # Register the client with the GrpcClientManager
    target = setup
    GrpcClientManager.register_clients(name="root", target=target)

    # Get the registered client
    client = GrpcClientManager.get_client("root")
    assert client is not None, "Client should be registered and connected"

    # Create a CommandServiceClient instance
    connection_client = ConnectionServiceClient(client_name="root")
    # Connect to the gRPC server
    connection_client.connect()

    # Test if the client can retrieve the logged-in username
    logged_in_username = connection_client.get_logged_in_username()
    print(f"Logged-in username: {logged_in_username}")
    assert logged_in_username is not None, "Failed to retrieve logged-in username"