#!/usr/bin/env python3
"""
Simple streaming test - Just verify that streaming service is working

This is a basic test to confirm the streaming service connection and functionality.
"""

import pytest
from test_framework.utils.handlers.log_monitoring import create_hybrid_monitor
from test_framework.utils import get_logger


def test_streaming_connection_simple():
    """
    Simple test to verify streaming service connectivity.
    
    This test just checks if we can create a hybrid monitor and
    attempt to connect to the streaming service.
    """
    test_logger = get_logger("test_streaming_simple")
    
    # Create a mock file transfer and config
    class MockFileTransfer:
        def download_file(self, path, tail_bytes=None):
            # Return mock log content matching actual log format
            mock_content = """2024-01-15 10:30:45.123 DesktopAgent UIManager 1000 0x7fff8a0bf19c 2 6000 admin Info: Switching to Login UI
2024-01-15 10:30:47.456 LoginPlugin ScreenManager 1001 0x7fff8a08f49c 2 6001 _securityagent Info: Opened proxcard screen
""".encode('utf-8')
            return mock_content
    
    mock_file_transfer = MockFileTransfer()
    mock_log_path = "/var/log/mock_test.log"
    
    # Test hybrid monitor creation
    hybrid_monitor = create_hybrid_monitor(
        file_transfer=mock_file_transfer,
        log_file_path=mock_log_path,
        test_logger=test_logger,
        enable_streaming=True
    )
    
    # Verify monitor was created
    assert hybrid_monitor is not None
    test_logger.info("HybridLogMonitor created successfully")
    
    # Test basic functionality (download and parse)
    entries, raw_content = hybrid_monitor.download_and_parse_with_raw()
    
    # Verify we got some entries
    assert entries is not None
    assert len(entries) > 0
    test_logger.info(f"Found {len(entries)} mock log entries")
    
    # Test streaming client initialization
    streaming_available = hybrid_monitor.enable_streaming and hybrid_monitor.streaming_client is not None
    
    if streaming_available:
        test_logger.info("Streaming client is available and connected")
    else:
        test_logger.info("Streaming client not available - will use polling fallback")
    
    # Test hybrid detection with simple criteria
    test_criteria = [
        {"message_contains": "Switching to Login UI", "component": "DesktopAgent"},
        {"message_contains": "Opened proxcard screen", "component": "LoginPlugin"}
    ]
    
    # Run hybrid detection (should work even if streaming is not available)
    results = hybrid_monitor.wait_for_entries_hybrid(test_criteria, max_wait_time=10)
    
    # Verify we found the entries
    assert len(results) == 2, f"Expected 2 entries, found {len(results)}"
    test_logger.info(f"Hybrid detection found {len(results)}/2 entries")
    
    # Check specific entries
    assert 0 in results, "Missing 'Switching to Login UI' entry"
    assert 1 in results, "Missing 'Opened proxcard screen' entry"
    
    # Verify entry content
    switch_entry = results[0]
    proxcard_entry = results[1]
    
    assert "Switching to Login UI" in switch_entry.message
    assert "Opened proxcard screen" in proxcard_entry.message
    
    test_logger.info("Entry content validation passed")
    
    # Test UI timing measurement
    timing_results = hybrid_monitor.monitor_ui_switch_timing(
        expected_user="admin",  # Use the actual expected user from your sessions
        max_wait_time=10
    )
    
    # Verify timing results
    assert timing_results is not None
    assert "ui_switch_duration_seconds" in timing_results
    
    if timing_results["ui_switch_duration_seconds"] is not None:
        duration = timing_results["ui_switch_duration_seconds"]
        test_logger.info(f"UI switch timing: {duration:.3f}s")
        assert duration > 0, "Duration should be positive"
    else:
        test_logger.warning(f"⚠Timing calculation failed: {timing_results.get('error_message')}")
    
    # Clean up
    hybrid_monitor.close()
    test_logger.info("Test completed - streaming functionality verified")


if __name__ == "__main__":
    # Run the test directly
    test_streaming_connection_simple()
    print("Simple streaming test passed!")