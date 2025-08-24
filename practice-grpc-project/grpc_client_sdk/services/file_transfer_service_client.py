import os
from typing import Optional, Generator

from generated import file_transfer_service_pb2
from generated.file_transfer_service_pb2_grpc import FileTransferServiceStub

from grpc_client_sdk.core.grpc_client_manager import GrpcClientManager
from test_framework.utils import get_logger


class FileTransferServiceClient:
    """
    FileTransferServiceClient is a gRPC client wrapper for the FileTransferService
    exposed by the macOS root gRPC server.
    Support operations:
    - Streaming file downloads from remote macOS to the test controller
    - Streaming file uploads from controller to remote macOS

    Typical use cases:
    - Downloading logs or plist files post-test
    - Uploading configs files or test assets before session starts

    Attributes:
        client_name (str): Logical gRPC context ('root').
        logger (Logger): Logger instance for structured output.
        stub (FileTransferServiceStub): gRPC stub from proto.

    Usage:
        client = FileTransferServiceClient(client_name="root")
        client.connect()
        file_content = client.download_file('/path/to/remote/file.txt')
        if file_content:
            with open('local_file.txt', 'wb') as f:
                f.write(file_content)
    """

    def __init__(self, client_name: str = "root", logger: Optional[object] = None):
        """
        Initializes the FileTransferServiceClient.
        This method sets up the client name and logger for structured output.
        It also initializes the gRPC stub for file transfer operations.

        :param client_name: Name of the gRPC client in GrpcClientManager.
        :param logger: Custom logger instance. If
        None, a default logger is created.
        """
        self.client_name = client_name
        self.logger = logger or get_logger(f"FileTransferServiceClient[{client_name}]")
        self.stub: Optional[FileTransferServiceStub] = None

    def connect(self) -> None:
        """
        Establishes the gRPC connection and stub for FileTransferService.
        """
        self.stub = GrpcClientManager.get_stub(self.client_name, FileTransferServiceStub)

    def download_file(self, remote_path: str, tail_bytes: Optional[str] = None) -> Optional[bytes]:
        """
        Downloads a file from the macOS server using chunked streaming.
        This method handles the streaming of file data from the server to the client.

        :param remote_path: Absolute path to the file on the macOS server.
        :param tail_bytes: Optional. If specified, only the last N bytes of the file will be downloaded.
        :return: The file content as bytes, or None if the download fails.

        Example:
            client = FileTransferServiceClient(client_name="root")
            client.connect()

            # Download entire file
            file_content = client.download_file('/path/to/remote/file.txt')

            # Download only the last 1000 bytes (e.g., for log files)
            tail_content = client.download_file('/path/to/remote/log.txt', tail_bytes='1000')

            if file_content:
                with open('local_file.txt', 'wb') as f:
                    f.write(file_content)
            else:
                print("File download failed.")
        """
        if not self.stub:
            raise RuntimeError("FileTransferServiceClient not connected.")

        try:
            # Create request with optional tail_bytes parameter
            request = file_transfer_service_pb2.DownloadFileRequest(server_file_path=remote_path)

            # Add tail_bytes if specified
            if tail_bytes:
                request.tail_bytes = tail_bytes
                self.logger.info(f"Requesting last {tail_bytes} bytes of {remote_path}")

            stream = self.stub.DownloadFile(request)

            content = bytearray()
            metadata_received = False

            for response in stream:
                if response.HasField("metadata"):
                    metadata = response.metadata
                    metadata_received = True

                    if not metadata.success:
                        self.logger.error(f"Server failed to provide file: {metadata.error_message}")
                        return None

                    download_type = f"tail ({tail_bytes} bytes)" if tail_bytes else "full file"
                    self.logger.info(
                        f"File metadata received: {metadata.filename} ({metadata.file_size} bytes) - {download_type}")

                elif response.HasField("chunk_data"):
                    content.extend(response.chunk_data)

            if not metadata_received:
                self.logger.error("No file metadata received during download.")
                return None

            # Log the actual received size
            actual_size = len(content)
            if tail_bytes and tail_bytes.isdigit():
                # Calculate expected size (for logging purposes)
                if metadata_received and hasattr(metadata, 'file_size'):
                    expected_size = min(int(tail_bytes), metadata.file_size)
                    self.logger.info(
                        f"Received {actual_size} bytes of tail data (requested: {tail_bytes}, expected: {expected_size})")
                else:
                    self.logger.info(f"Received {actual_size} bytes of tail data (requested: {tail_bytes})")
            else:
                self.logger.info(f"Received {actual_size} bytes of file data")

            return bytes(content)

        except Exception as e:
            self.logger.error(f"Download failed for '{remote_path}': {e}")
            return None

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """
        Uploads a file to the macOS server using chunked streaming.
        This method handles the streaming of file data from the client to the server.

        :param local_path: Absolute path to the file on the client.
        :param remote_path: Absolute path where the file will be saved on the macOS server.
        :return: True if the upload is successful, False otherwise.


        Example:
            client = FileTransferServiceClient(client_name="root")
            client.connect()
            success = client.upload_file('local_file.txt', '/path/to/remote/file.txt')
            if success:
                print("File upload successful.")
            else:
                print("File upload failed.")
        """

        if not self.stub:
            raise RuntimeError("FileTransferServiceClient not connected.")

        if not os.path.exists(local_path):
            self.logger.error(f"Local file not found: {local_path}")
            return False

        try:
            file_size = os.path.getsize(local_path)

            def request_generator() -> Generator[file_transfer_service_pb2.UploadFileRequest, None, None]:
                yield file_transfer_service_pb2.UploadFileRequest(
                    metadata=file_transfer_service_pb2.FileInfo(
                        filename=os.path.basename(local_path),
                        destination_path=remote_path,
                        file_size=file_size
                    )
                )
                with open(local_path, "rb") as file:
                    while chunk := file.read(4096):
                        yield file_transfer_service_pb2.UploadFileRequest(chunk_data=chunk)

            response = self.stub.UploadFile(request_generator())
            if response.success:
                self.logger.info(f"File uploaded: {remote_path} ({response.received_file_size} bytes)")
                return True
            else:
                self.logger.error(f"Upload failed: {response.error_message}")
                return False

        except Exception as e:
            self.logger.error(f"Upload exception for '{local_path}': {e}")
            return False