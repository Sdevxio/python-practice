from grpc_client_sdk.core.grpc_client_manager import GrpcClientManager
from grpc_client_sdk.services.registry_service_client import RegistryServiceClient


def test_get_agent(setup):
    """
    Test the get_agent method of RegistryServiceClient.
    """
    # Register the client with the GrpcClientManager
    target = setup
    GrpcClientManager.register_clients(name="root", target=target)

    # Create a RegistryServiceClient instance
    registry_client = RegistryServiceClient(client_name="root")
    # # Connect to the gRPC server
    registry_client.connect()
    username = "admin"

    # Test if the client can get an agent by username
    client = registry_client.get_agent(username=username)
    assert client is not None, f"Failed to get agent info for username: {username}"

def test_registry_list_agents(setup):
    """
    Test the list_agents method of RegistryServiceClient.
    """
    # Register the client with the GrpcClientManager
    target = setup
    GrpcClientManager.register_clients(name="root", target=target)

    # Create a RegistryServiceClient instance
    registry_client = RegistryServiceClient(client_name="root")
    # Connect to the gRPC server
    registry_client.connect()

    # Test if the client can list all agents
    agents = registry_client.list_agents()
    assert agents is not None, "Failed to list agents"

    expected_users = [
        "admin",
    ]
    usernames = [agent['username'] for agent in agents]
    assert usernames == sorted(expected_users), (
        "Available services do not match the expected services"
    )