from typing import Optional, Dict, List

from generated import agent_registry_service_pb2
from generated.agent_registry_service_pb2_grpc import RegistryServiceStub

from grpc_client_sdk.core.grpc_client_manager import GrpcClientManager
from test_framework.utils import get_logger


class RegistryServiceClient:
    """
    RegistryServiceClient is a gRPC wrapper for querying agent registration status
    from the macOS root-level gRPC server.

    This client is used during session bootstrapping to:
    - Look up an active agent by username
    - Retrieve available agents registered on the system
    This client is **read-only** — it does NOT support registration, deregistration,
    or heartbeat mechanisms. It is intended for test controller-side lookup only.

    Attributes:
        client_name (str): Logical name of the gRPC client ("root" expected).
        logger (Logger): Scoped logger instance.
        stub (RegistryServiceStub): gRPC stub for the RegistryService.
        host (str): Optional IP or hostname this client is resolving against.

    Usage:
        client = RegistryServiceClient(client_name="root")
        client.connect()
        agent_info = client.get_agent(username="test_user")
        all_agents = client.list_agents()
    """

    def __init__(self, client_name: str = "root", logger: Optional[object] = None):
        """
        Initialize RegistryServiceClient.

        :param client_name: Name registered in GrpcClientManager.
        :param logger: Custom logger instance. If
        None, a default logger is created.
        """
        self.client_name = client_name
        self.logger = logger or get_logger(f"RegistryServiceClient[{client_name}]")
        self.stub: Optional[RegistryServiceStub] = None
        self.host: Optional[str] = None  # Used in SessionContextBuilder if needed

    def connect(self) -> None:
        """
        Establishes the gRPC connection and stub for RegistryService.
        """
        self.stub = GrpcClientManager.get_stub(self.client_name, RegistryServiceStub)

    def get_agent(self, username: str) -> Optional[Dict[str, any]]:
        """
        Query the registry for a registered agent by username.
        This method returns the agent information if found, or None if not.

        :param username: macOS username associated with the agent.
        :return:
        dict: {
                "username": str,
                "uid": int,
                "port": int,
                "timestamp": int
            }
            or None if agent is not found.

        Example:
            client = RegistryServiceClient(client_name="root")
            client.connect()
            agent_info = client.get_agent(username="test_user")
            if agent_info:
                print(f"Agent found: {agent_info}")
            else:
                print("Agent not found.")
        """
        if not self.stub:
            raise RuntimeError("RegistryServiceClient not connected.")

        try:
            request = agent_registry_service_pb2.AgentIdentifier(username=username)
            response = self.stub.GetAgent(request)
            return {
                "username": response.username,
                "uid": response.uid,
                "port": response.port,
                "timestamp": response.timestamp
            }
        except Exception as e:
            self.logger.warning(f"Agent not found for '{username}': {e}")
            return None

    def list_agents(self) -> List[Dict[str, any]]:
        """
        Retrieves all active agents currently registered.
        :return:
        List of dicts: [
            {
                "username": str,
                "uid": int,
                "port": int,
                "timestamp": int
            }
        ]

        Example:
            client = RegistryServiceClient(client_name="root")
            client.connect()
            all_agents = client.list_agents()
            print(f"All registered agents: {all_agents}")
        """
        if not self.stub:
            raise RuntimeError("RegistryServiceClient not connected.")

        try:
            response = self.stub.ListAgents(agent_registry_service_pb2.Empty())
            return [
                {
                    "username": agent.username,
                    "uid": agent.uid,
                    "port": agent.port,
                    "timestamp": agent.timestamp
                }
                for agent in response.agents
            ]
        except Exception as e:
            self.logger.error(f"Failed to list agents: {e}")
            return []