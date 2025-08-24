import os

from grpc_client_sdk.core.grpc_client_manager import GrpcClientManager
from grpc_client_sdk.services.file_transfer_service_client import FileTransferServiceClient
from test_framework.utils.consts.constants import REMOTE_LOG_PATH, REMOTE_LOG_NAME
from test_framework.utils.handlers.artifacts.artifacts_handler import save_to_artifacts


def test_download_files(setup):
    """
    Test the download_file method of FileTransferServiceClient.
    This test checks if a file can be downloaded successfully from the server.

    :param setup: Fixture that sets up the gRPC client and server.
    """
    # Register the client with the GrpcClientManager
    target = setup
    GrpcClientManager.register_clients(name="root", target=target)

    # Get the registered client
    client = GrpcClientManager.get_client("root")
    assert client is not None, "Client should be registered and connected"

    # Create a FileTransferServiceClient instance
    file_transfer_client = FileTransferServiceClient(client_name="root")
    # Connect to the gRPC server
    file_transfer_client.connect()

    # Test if the client can download a file
    remote_path = REMOTE_LOG_PATH
    LOG_TAIL_SIZE = "10485760"
    # Download file from macOS
    content = file_transfer_client.download_file(remote_path, tail_bytes=LOG_TAIL_SIZE)
    assert content is not None, f"Failed to download file: {remote_path}"
    assert len(content) > 0, "Downloaded file is empty"

    # Save file to artifacts directory
    local_path = save_to_artifacts(content, REMOTE_LOG_NAME)

    assert os.path.exists(local_path), f"File not saved: {local_path}"
    print(f"File downloaded and saved at: {local_path}")