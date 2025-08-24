import os

from grpc_client_sdk.core.grpc_client_manager import GrpcClientManager
from grpc_client_sdk.services.file_transfer_service_client import FileTransferServiceClient
from test_framework.utils.handlers.artifacts.artifacts_handler import save_to_artifacts
from test_framework.utils.handlers.file_analayzer.extractor import LogExtractor
from test_framework.utils.handlers.file_analayzer.parser import LogParser


def test_extract_card_ids(setup, test_logger):
    """
    Test extracting card IDs from log files.

    This test efficiently downloads only the last 10MB of log data rather than
    the entire file, saving time and network resources.
    """
    # Setup
    target = setup
    GrpcClientManager.register_clients(name="root", target=target)
    file_transfer_client = FileTransferServiceClient(client_name="root")
    file_transfer_client.connect()

    # Define the size of log data to download (10MB should be sufficient for recent entries)
    # Adjust this value based on your needs - smaller for faster downloads, larger for more history
    LOG_TAIL_SIZE = "10485760"  # 10MB in bytes

    # Download just the tail of the log file
    remote_path = "/Library/Logs/imprivata.log"
    content = file_transfer_client.download_file(remote_path, tail_bytes=LOG_TAIL_SIZE)
    assert content is not None, f"Failed to download file: {remote_path}"

    # Log the size of the downloaded content
    test_logger.info(f"Downloaded {len(content) // 1024}KB of log data")

    # Save file to artifacts directory
    local_path = save_to_artifacts(content, "test_tail.log")
    assert os.path.exists(local_path), f"File not saved: {local_path}"
    test_logger.info(f"File downloaded and saved at: {local_path}")

    # Parse the log file
    parser = LogParser()
    entries = parser.parse_file(local_path)
    test_logger.info(f"Parsed {len(entries)} log entries")

    # Extract card IDs
    extractor = LogExtractor()
    card_ids = extractor.find_card_activity(entries)

    # Display results
    test_logger.info(f"Found {len(card_ids)} card ID entries")
    if card_ids:
        test_logger.info("First 5 card IDs:")
        for i, (card_id, entry) in enumerate(card_ids[:5]):
            test_logger.info(f"{i + 1}. [{entry.timestamp}] {card_id} - {entry.component}/{entry.subcomponent}")

    # Extract usernames
    usernames = extractor.find_card_activity(entries)
    test_logger.info(f"Found {len(usernames)} username entries")
    if usernames:
        test_logger.info("First 5 usernames:")
        for i, (username, entry) in enumerate(usernames[:5]):
            test_logger.info(f"{i + 1}. [{entry.timestamp}] {username} - {entry.component}/{entry.subcomponent}")

    # Success - we parsed the log file and extracted information
    test_logger.info("Log extraction completed successfully")