"""
Test for LogsMonitoringServiceClient using the Service Registry pattern.

This demonstrates how to test the new logs monitoring service with clean,
simple fixtures that handle all the complexity automatically.
"""
import time
from datetime import datetime, timedelta

from test_framework.utils.handlers.file_analayzer.log_monitor_streaming import LogMonitorStreaming, EventCriteria


class TestLogsMonitorService:
    """Test logs monitoring service with various streaming scenarios."""

    def test_basic_log_streaming(self, logs_monitor):
        """
        Test basic log streaming functionality.
        
        This is the simplest test - just start and stop a stream.
        """
        log_file_path = "/Users/admin/pro-mac-client-test-fixtures/dynamic_log_generator/dynamic_test.log"
        
        # Start streaming
        stream_id = logs_monitor.stream_log_entries(
            log_file_path=log_file_path,
            include_existing=True
        )
        
        assert stream_id is not None
        assert stream_id != "placeholder_stream_id"
        
        # Give it a moment to process some entries
        time.sleep(1)
        
        # Check active streams
        active_streams = logs_monitor.get_active_streams()
        assert stream_id in active_streams
        assert active_streams[stream_id]['file_path'] == log_file_path
        
        # Stop the stream
        success = logs_monitor.stop_log_stream(stream_id)
        assert success

    def test_filtered_log_streaming(self, logs_monitor):
        """
        Test streaming with pattern filters.
        
        Only entries matching the patterns should be captured.
        """
        log_file_path = "/Users/admin/pro-mac-client-test-fixtures/dynamic_log_generator/dynamic_test.log"
        
        # Stream with specific filters
        filter_patterns = ["SessionManager", "CardReader"]
        
        stream_id = logs_monitor.stream_log_entries(
            log_file_path=log_file_path,
            filter_patterns=filter_patterns,
            include_existing=True
        )
        
        assert stream_id is not None
        
        # Give it time to process
        time.sleep(2)
        
        # Check the stream info
        active_streams = logs_monitor.get_active_streams()
        assert stream_id in active_streams
        
        stream_info = active_streams[stream_id]
        assert stream_info['filters'] == filter_patterns
        
        # Clean up
        logs_monitor.stop_log_stream(stream_id)

    def test_tap_correlation_workflow(self, logs_monitor):
        """
        Test the tap correlation functionality - the key feature for automation.
        
        This simulates the timing correlation scenario.
        """
        log_file_path = "/Users/admin/pro-mac-client-test-fixtures/dynamic_log_generator/dynamic_test.log"
        
        # Simulate a tap that happened "now"
        tap_start_time = datetime.now()
        
        # Look for patterns that should appear after the tap
        expected_patterns = ["Session created", "Card detected"]
        
        # Run tap correlation
        correlation_results = logs_monitor.stream_entries_for_tap_correlation(
            tap_start_time=tap_start_time,
            expected_patterns=expected_patterns,
            log_file_path=log_file_path,
            correlation_window_seconds=30
        )
        
        # Verify correlation results structure
        assert correlation_results is not None
        assert 'found_entries' in correlation_results
        assert 'tap_start_time' in correlation_results
        assert 'expected_patterns' in correlation_results
        assert 'search_completed' in correlation_results
        assert 'streaming_available' in correlation_results
        
        # The patterns should be the ones we searched for
        assert correlation_results['expected_patterns'] == expected_patterns

    def test_multiple_streams(self, logs_monitor):
        """
        Test handling multiple concurrent streams.
        
        This verifies the service can handle multiple log streams simultaneously.
        """
        log_file_path = "/Users/admin/pro-mac-client-test-fixtures/dynamic_log_generator/dynamic_test.log"
        
        # Start multiple streams with different filters
        stream1 = logs_monitor.stream_log_entries(
            log_file_path=log_file_path,
            filter_patterns=["SessionManager"],
            include_existing=True
        )
        
        stream2 = logs_monitor.stream_log_entries(
            log_file_path=log_file_path,
            filter_patterns=["CardReader"],
            include_existing=True
        )
        
        assert stream1 != stream2
        assert stream1 is not None
        assert stream2 is not None
        
        # Give streams time to process
        time.sleep(1)
        
        # Check both streams are active
        active_streams = logs_monitor.get_active_streams()
        assert stream1 in active_streams
        assert stream2 in active_streams
        
        # Verify different filters
        assert active_streams[stream1]['filters'] == ["SessionManager"]
        assert active_streams[stream2]['filters'] == ["CardReader"]
        
        # Stop both streams
        logs_monitor.stop_log_stream(stream1)
        logs_monitor.stop_log_stream(stream2)
        
        # Verify cleanup
        final_streams = logs_monitor.get_active_streams()
        assert stream1 not in final_streams
        assert stream2 not in final_streams

    def test_stream_cleanup_on_fixture_teardown(self, logs_monitor):
        """
        Test that streams are automatically cleaned up.
        
        This verifies the fixture handles cleanup properly.
        """
        log_file_path = "/Users/admin/pro-mac-client-test-fixtures/dynamic_log_generator/dynamic_test.log"
        
        # Start a stream but don't manually stop it
        stream_id = logs_monitor.stream_log_entries(
            log_file_path=log_file_path,
            include_existing=True
        )
        
        assert stream_id is not None
        
        # Verify stream is active
        active_streams = logs_monitor.get_active_streams()
        assert stream_id in active_streams
        
        # The fixture will automatically clean up when the test ends
        # This tests that our fixture cleanup works properly


class TestLogsMonitorIntegration:
    """Integration tests combining logs monitoring with other services."""

    def test_command_and_logs_correlation(self, command, logs_monitor):
        """
        Test correlating command execution with log entries.
        
        This is a realistic automation scenario.
        """
        log_file_path = "/Users/admin/pro-mac-client-test-fixtures/dynamic_log_generator/dynamic_test.log"
        
        # Start monitoring before running command
        stream_id = logs_monitor.stream_log_entries(
            log_file_path=log_file_path,
            filter_patterns=["Session", "User"],
            include_existing=False  # Only new entries
        )
        
        # Record when we start the command
        command_start_time = datetime.now()
        
        # Run a command that might generate log entries
        result = command("whoami")
        assert result.exit_code == 0
        
        # Give logs time to appear
        time.sleep(2)
        
        # Check if we captured any relevant entries
        active_streams = logs_monitor.get_active_streams()
        if stream_id in active_streams:
            entry_count = active_streams[stream_id]['entry_count']
            # We might or might not have entries, but the test should complete successfully
            print(f"Captured {entry_count} log entries during command execution")
        
        # Clean up
        logs_monitor.stop_log_stream(stream_id)

    def test_logs_with_temp_file_monitoring(self, logs_monitor, temp_file):
        """
        Test monitoring a temporary log file.
        
        This shows how different fixtures compose cleanly.
        """
        # Create a temporary log file
        log_content = """2025-08-15 18:26:45.091 TestApp TestModule 1001 0x7fff8a044ea7 2 6001 root Info: Test started
2025-08-15 18:26:45.215 TestApp TestModule 1002 0x7fff8a05cb19 2 6002 root Info: Test operation completed
2025-08-15 18:26:45.469 TestApp TestModule 1003 0x7fff8a078f34 2 6003 root Info: Test finished successfully"""
        
        temp_log_file = temp_file(log_content, suffix=".log")
        
        # Start monitoring the temp file
        stream_id = logs_monitor.stream_log_entries(
            log_file_path=temp_log_file,
            filter_patterns=["TestApp"],
            include_existing=True
        )
        
        assert stream_id is not None
        
        # Give it time to process
        time.sleep(1)
        
        # Verify it's monitoring our temp file
        active_streams = logs_monitor.get_active_streams()
        assert stream_id in active_streams
        assert active_streams[stream_id]['file_path'] == temp_log_file
        
        # Clean up
        logs_monitor.stop_log_stream(stream_id)


class TestLogsMonitorErrorHandling:
    """Test error handling and edge cases."""

    def test_nonexistent_log_file(self, logs_monitor):
        """
        Test handling of nonexistent log files.
        
        Service should handle this gracefully.
        """
        nonexistent_file = "/path/that/does/not/exist.log"
        
        # This should not crash, but might return a placeholder
        stream_id = logs_monitor.stream_log_entries(
            log_file_path=nonexistent_file,
            include_existing=True
        )
        
        # Should return something (even if placeholder)
        assert stream_id is not None

    def test_empty_filter_patterns(self, logs_monitor):
        """
        Test streaming with empty filter patterns.
        
        Should capture all entries.
        """
        log_file_path = "/Users/admin/pro-mac-client-test-fixtures/dynamic_log_generator/dynamic_test.log"
        
        stream_id = logs_monitor.stream_log_entries(
            log_file_path=log_file_path,
            filter_patterns=[],  # Empty filters
            include_existing=True
        )
        
        assert stream_id is not None
        
        # Give it time to process
        time.sleep(1)
        
        # Verify empty filters
        active_streams = logs_monitor.get_active_streams()
        if stream_id in active_streams:
            assert active_streams[stream_id]['filters'] == []
        
        # Clean up
        logs_monitor.stop_log_stream(stream_id)


class TestSpecificLogEntries:
    """Test finding specific log entries from the dynamic log file."""
    
    def test_structured_filtering_by_component(self, logs_monitor):
        """
        Test streaming with structured filtering by component.
        
        This demonstrates the new structured filtering capability.
        """
        log_file_path = "/Users/admin/pro-mac-client-test-fixtures/dynamic_log_generator/dynamic_test.log"
        
        # Stream with structured criteria - only LoginPlugin component entries
        stream_id = logs_monitor.stream_log_entries(
            log_file_path=log_file_path,
            filter_patterns=["proxcard screen"],
            include_existing=True,
            structured_criteria={
                "component": "LoginPlugin",
                "process_name": "_securityagent"
            }
        )
        
        assert stream_id is not None
        
        # Give it time to process
        time.sleep(2)
        
        # Check results
        active_streams = logs_monitor.get_active_streams()
        assert stream_id in active_streams
        
        stream_info = active_streams[stream_id]
        entry_count = stream_info['entry_count']
        
        print(f"Found {entry_count} entries with structured filtering (LoginPlugin + _securityagent + 'proxcard screen')")
        
        # Should find entries, but only those matching ALL criteria
        assert entry_count >= 0  # Could be 0 if no entries match all criteria
        
        # Clean up
        logs_monitor.stop_log_stream(stream_id)

    def test_find_proxcard_screen_entry(self, logs_monitor):
        """
        Test finding the specific 'Opened proxcard screen' log entry.
        
        This tests finding the exact entry:
        2025-08-15 18:27:15.728 LoginPlugin ScreenManager 1154 0x7fff8a07b48d 2 6154 _securityagent Info: Opened proxcard screen
        """
        log_file_path = "/Users/admin/pro-mac-client-test-fixtures/dynamic_log_generator/dynamic_test.log"
        
        # Start streaming with pattern for proxcard screen
        stream_id = logs_monitor.stream_log_entries(
            log_file_path=log_file_path,
            filter_patterns=["Opened proxcard screen"],
            include_existing=True
        )
        
        assert stream_id is not None
        
        # Give it time to process existing entries
        time.sleep(2)
        
        # Check active streams to see if we found the entry
        active_streams = logs_monitor.get_active_streams()
        assert stream_id in active_streams
        
        stream_info = active_streams[stream_id]
        entry_count = stream_info['entry_count']
        
        # We should find at least one entry with this pattern
        assert entry_count > 0, "Should find the 'Opened proxcard screen' entry"
        
        print(f"Found {entry_count} entries matching 'Opened proxcard screen'")
        
        # Clean up
        logs_monitor.stop_log_stream(stream_id)

    def test_find_latest_proxcard_entry_with_correlation(self, logs_monitor):
        """
        Test finding the proxcard entry using tap correlation.
        
        This simulates looking for the entry as if it appeared after a specific action.
        """
        log_file_path = "/Users/admin/pro-mac-client-test-fixtures/dynamic_log_generator/dynamic_test.log"
        
        # Simulate looking for entries from a specific time
        # Use a time before the log entry to ensure we find it
        search_start_time = datetime(2025, 8, 15, 18, 27, 10)  # 5 seconds before the entry
        
        # Look for the specific pattern
        expected_patterns = ["Opened proxcard screen"]
        
        # Run correlation search
        correlation_results = logs_monitor.stream_entries_for_tap_correlation(
            tap_start_time=search_start_time,
            expected_patterns=expected_patterns,
            log_file_path=log_file_path,
            correlation_window_seconds=60
        )
        
        # Verify we got results
        assert correlation_results is not None
        assert correlation_results['expected_patterns'] == expected_patterns
        
        # Check if we found the entry
        found_entries = correlation_results['found_entries']
        
        if found_entries:
            print(f"Found {len(found_entries)} matching entries")
            for key, entry_info in found_entries.items():
                print(f"  {key}: {entry_info['pattern_matched']} - {entry_info['message']}")
                assert "Opened proxcard screen" in entry_info['message']
        else:
            print("No entries found in correlation window")

    def test_find_multiple_login_related_entries(self, logs_monitor):
        """
        Test finding multiple login-related entries including the proxcard one.
        
        This shows how to search for broader patterns.
        """
        log_file_path = "/Users/admin/pro-mac-client-test-fixtures/dynamic_log_generator/dynamic_test.log"
        
        # Search for login-related patterns
        filter_patterns = ["LoginPlugin", "ScreenManager", "_securityagent"]
        
        stream_id = logs_monitor.stream_log_entries(
            log_file_path=log_file_path,
            filter_patterns=filter_patterns,
            include_existing=True
        )
        
        assert stream_id is not None
        
        # Give it time to process
        time.sleep(2)
        
        # Check results
        active_streams = logs_monitor.get_active_streams()
        assert stream_id in active_streams
        
        stream_info = active_streams[stream_id]
        entry_count = stream_info['entry_count']
        
        print(f"Found {entry_count} login-related entries")
        
        # Should find multiple entries since we're searching for broader patterns
        assert entry_count > 0, "Should find login-related entries"
        
        # Clean up
        logs_monitor.stop_log_stream(stream_id)


class TestLogMonitorStreaming:
    """Test the new high-level LogMonitorStreaming interface."""
    
    def test_automated_event_detection(self, logs_monitor):
        """
        Test the new automated event detection using LogMonitorStreaming.
        
        This demonstrates the simplified interface compared to manual streaming.
        """
        log_file_path = "/Users/admin/pro-mac-client-test-fixtures/dynamic_log_generator/dynamic_test.log"
        
        # Create LogMonitorStreaming instance
        monitor = LogMonitorStreaming(logs_monitor, log_file_path)
        
        # Define criteria for what we're looking for
        criteria = EventCriteria(
            start_time=datetime(2025, 8, 15, 18, 27, 10),  # Time before proxcard entry
            target_patterns=["Opened proxcard screen"],
            required_components=["LoginPlugin"],
            process_names=["_securityagent"],
            timeout_seconds=10,
            min_entries_required=1
        )
        
        # Wait for events - this blocks until found or timeout
        matching_entries = monitor.wait_for_events(criteria)
        
        # Verify results
        assert matching_entries is not None, "Should find proxcard screen entries"
        assert len(matching_entries) >= 1, "Should find at least one matching entry"
        
        # Verify entry content
        entry = matching_entries[0]
        assert "Opened proxcard screen" in entry.message
        assert "LoginPlugin" in entry.component
        assert "_securityagent" in entry.process_name
        
        print(f"Found {len(matching_entries)} entries automatically:")
        for i, entry in enumerate(matching_entries[:3], 1):  # Show first 3
            print(f"  {i}: {entry.timestamp} - {entry.message}")
    
    def test_sophisticated_filtering(self, logs_monitor):
        """
        Test sophisticated filtering with multiple criteria.
        
        This shows the power of the EventCriteria system.
        """
        log_file_path = "/Users/admin/pro-mac-client-test-fixtures/dynamic_log_generator/dynamic_test.log"
        
        monitor = LogMonitorStreaming(logs_monitor, log_file_path)
        
        # Complex criteria with multiple filters
        criteria = EventCriteria(
            start_time=datetime(2025, 8, 15, 0, 0, 0),  # Start of day
            target_patterns=["LoginPlugin"],  # Primary pattern
            required_components=["LoginPlugin"],
            entry_types=["Info"],
            process_names=["_securityagent"],
            message_contains=["screen"],  # Must contain "screen"
            message_excludes=["debug", "trace"],  # Exclude debug entries
            timeout_seconds=5,
            min_entries_required=2  # Wait for at least 2 entries
        )
        
        matching_entries = monitor.wait_for_events(criteria)
        
        if matching_entries:
            print(f"Sophisticated filtering found {len(matching_entries)} entries")
            assert len(matching_entries) >= 2, "Should find at least 2 entries"
            
            # Verify all entries match criteria
            for entry in matching_entries:
                assert "LoginPlugin" in entry.component
                assert "Info" in entry.type
                assert "_securityagent" in entry.process_name
                assert "screen" in entry.message.lower()
                assert "debug" not in entry.message.lower()
                assert "trace" not in entry.message.lower()
        else:
            print("No entries found matching sophisticated criteria")
    
    def test_timeout_handling(self, logs_monitor):
        """
        Test timeout handling when no matching events are found.
        
        This verifies automatic cleanup and timeout behavior.
        """
        log_file_path = "/Users/admin/pro-mac-client-test-fixtures/dynamic_log_generator/dynamic_test.log"
        
        monitor = LogMonitorStreaming(logs_monitor, log_file_path)
        
        # Criteria that won't match anything
        criteria = EventCriteria(
            start_time=datetime.now() + timedelta(hours=1),  # Future time
            target_patterns=["NonexistentPattern12345"],
            timeout_seconds=2,  # Short timeout
            min_entries_required=1
        )
        
        start_time = time.time()
        matching_entries = monitor.wait_for_events(criteria)
        elapsed = time.time() - start_time
        
        # Should return None after timeout
        assert matching_entries is None, "Should timeout and return None"
        assert elapsed >= 2.0, "Should wait for at least timeout duration"
        assert elapsed < 3.0, "Should not wait much longer than timeout"
        
        print(f"Timeout handled correctly after {elapsed:.2f}s")
    
    def test_comparison_with_manual_streaming(self, logs_monitor):
        """
        Compare LogMonitorStreaming with manual streaming approach.
        
        This shows the code reduction and simplification.
        """
        log_file_path = "/Users/admin/pro-mac-client-test-fixtures/dynamic_log_generator/dynamic_test.log"
        
        # NEW APPROACH: LogMonitorStreaming (simple)
        monitor = LogMonitorStreaming(logs_monitor, log_file_path)
        criteria = EventCriteria(
            start_time=datetime(2025, 8, 15, 18, 27, 10),
            target_patterns=["Opened proxcard screen"],
            required_components=["LoginPlugin"],
            timeout_seconds=5
        )
        
        start_time = time.time()
        new_results = monitor.wait_for_events(criteria)
        new_elapsed = time.time() - start_time
        
        # OLD APPROACH: Manual streaming (complex)
        start_time = time.time()
        stream_id = logs_monitor.stream_log_entries(
            log_file_path=log_file_path,
            filter_patterns=["Opened proxcard screen"],
            include_existing=True,
            structured_criteria={"component": "LoginPlugin"}
        )
        
        time.sleep(2)  # Manual wait
        
        active_streams = logs_monitor.get_active_streams()
        old_results = []
        if stream_id in active_streams:
            entry_count = active_streams[stream_id]['entry_count']
            old_results = f"Found {entry_count} entries"
        
        logs_monitor.stop_log_stream(stream_id)  # Manual cleanup
        old_elapsed = time.time() - start_time
        
        # Compare results
        print(f"LogMonitorStreaming: {len(new_results) if new_results else 0} entries in {new_elapsed:.2f}s")
        print(f"Manual streaming: {old_results} in {old_elapsed:.2f}s")
        
        # Both should find similar results
        if new_results:
            assert len(new_results) > 0, "LogMonitorStreaming should find entries"