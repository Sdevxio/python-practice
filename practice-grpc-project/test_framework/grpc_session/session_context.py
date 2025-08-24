"""
SessionContext class to hold test session information and scoped gRPC clients service contexts.
"""
from test_framework.grpc_session.service_context import ServiceContext


class SessionContext:
    """
    Holds test session information and scoped gRPC clients service contexts.
    This class encapsulates the context for a test session, including user details,
    agent port, and service contexts for both root and user levels.

    Attributes:
        username (str): The username associated with the session.
        agent_port (int): The port number where the agent is running.
        root_context (ServiceContext): Service context for root-level services.
        user_context (ServiceContext): Service context for user-level services.

    Example:
        session = SessionContext(
            username="test_user",
            agent_port=50051,
            root_context=root_service_context,
            user_context=user_service_context
        )
        print(session.username)  # Output: test_user
        print(session.root_context.command.run("ls -la"))
    """

    def __init__(self, username: str, agent_port: int, root_context: ServiceContext, user_context: ServiceContext):
        """Initialize the SessionContext with user details and service contexts."""
        self.username = username
        self.agent_port = agent_port
        self.root_context = root_context
        self.user_context = user_context