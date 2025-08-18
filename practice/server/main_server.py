from concurrent import futures

import grpc

from grpc_server.eam_mac_grpc_server.main.registry.agent_registry import AgentRegistry
from grpc_server.eam_mac_grpc_server.main.services.agent_registry_service import RegistryServiceServicer
from grpc_server.eam_mac_grpc_server.main.services.apple_script_service import AppleScriptServicer
from grpc_server.eam_mac_grpc_server.main.services.command_service import CommandServicer
from grpc_server.eam_mac_grpc_server.main.services.connection_service import ConnectionServicer
from grpc_server.eam_mac_grpc_server.main.services.file_transfer_service import FileTransferServicer
from grpc_server.eam_mac_grpc_server.main.services.gui_automation_service import GuiAutomationServicer
from grpc_server.eam_mac_grpc_server.main.services.log_streaming_service import LogStreamingServicer
from grpc_server.eam_mac_grpc_server.main.services.screen_capture_service import ScreenCaptureServicer
from grpc_server.eam_mac_grpc_server.main.utils.port_checker import find_available_port


def serve():
    """Start the gRPC server and dynamically bind to an available port."""

    # Get an available port with retry logic - specify this is the root server
    port = find_available_port(is_root=True)

    if not port:
        print("ERROR: No available ports found. Server cannot start.")
        return

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Create registry for agent management
    registry = AgentRegistry()

    # Register all gRPC services (FIXED: No duplication)
    ConnectionServicer.add_to_server(server)
    FileTransferServicer.add_to_server(server)
    CommandServicer.add_to_server(server)
    LogStreamingServicer.add_to_server(server)

    # Registry service
    RegistryServiceServicer.add_to_server(server, registry)

    # Services that support agent routing (pass registry)
    AppleScriptServicer.add_to_server(server, registry)
    ScreenCaptureServicer.add_to_server(server, registry)
    GuiAutomationServicer.add_to_server(server, registry)

    server.add_insecure_port(f"[::]:{port}")
    server.start()

    print(f"🚀 gRPC ROOT Server started on port {port}")
    print(
        f"📋 Services registered: Connection, FileTransfer, Command, LogStreaming, Registry, AppleScript, ScreenCapture, GuiAutomation")
    print(f"🔗 Agent registry initialized for user agent routing")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("🛑 Server shutdown requested")


if __name__ == '__main__':
    serve()
