#!/usr/bin/env python3
"""
Simple Login UI Test Configuration - Following your proven pattern

Single consolidated fixture following your recent_entries pattern.
No complex fixture chains, just one simple streaming monitor.
"""

import os
import pytest

from test_framework.utils.handlers.log_monitoring import create_hybrid_monitor
from grpc_client_sdk.services.file_transfer_service_client import FileTransferServiceClient


@pytest.fixture(scope="function")
def streaming_monitor(session_setup, session_config, test_logger):
    """
    Single consolidated fixture like your recent_entries pattern.
    
    Simple streaming monitor that handles everything:
    - File transfer setup
    - Hybrid monitor creation (streaming + polling fallback)
    - Automatic cleanup
    """
    log_file_path = session_config.get("log_file_path", "/var/log/system.log")
    enable_streaming = os.environ.get("ENABLE_LOG_STREAMING", "true").lower() == "true"
    
    test_logger.info(f"Setting up simple streaming monitor - streaming: {enable_streaming}")
    test_logger.info(f"Log file: {log_file_path}")
    
    # Simple file transfer setup
    file_transfer = FileTransferServiceClient(client_name="root", logger=test_logger)
    file_transfer.connect()
    
    # Create simple hybrid monitor
    monitor = create_hybrid_monitor(
        file_transfer=file_transfer,
        log_file_path=log_file_path,
        test_logger=test_logger,
        enable_streaming=enable_streaming
    )
    
    test_logger.info("Simple streaming monitor ready")
    
    yield monitor
    
    # Simple cleanup
    try:
        monitor.close()
        test_logger.debug("Streaming monitor closed")
    except Exception as e:
        test_logger.warning(f"Error closing monitor: {e}")


# Command line options (keeping it simple)
def pytest_addoption(parser):
    """Simple command line options for streaming control."""
    parser.addoption("--no-streaming", action="store_true", default=False, help="Disable streaming")


@pytest.fixture(autouse=True)
def apply_streaming_options(request):
    """Apply streaming options."""
    if request.config.getoption("--no-streaming"):
        os.environ["ENABLE_LOG_STREAMING"] = "false"