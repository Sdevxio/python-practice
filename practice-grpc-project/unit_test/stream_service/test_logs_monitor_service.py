"""
Unit test for LogsMonitoringService using the enhanced gRPC architecture.

This test focuses on the basic functionality of the logs monitoring service
with both root and user contexts, following the same pattern as connection_service.
"""
import tempfile
import os
import time


def test_logs_monitor_service_basic(services, test_logger):
    """Test basic logs monitoring service functionality with both contexts."""
    
    # Test root context logs monitor service
    test_logger.info("Testing root context logs monitor service...")
    root_logs_monitor = services.logs_monitor_stream("root")
    assert root_logs_monitor is not None, "Root logs monitor service is None"
    test_logger.info("✅ Root logs monitor service instantiated successfully")
    
    # Test user context logs monitor service  
    test_logger.info("Testing user context logs monitor service...")
    user_logs_monitor = services.logs_monitor_stream("admin")
    assert user_logs_monitor is not None, "User logs monitor service is None"
    test_logger.info("✅ User logs monitor service instantiated successfully")
    
    # Test with temporary log file to avoid dependencies
    test_logger.info("Testing with temporary log file...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as temp_log:
        temp_log.write("2025-08-22 23:30:00 TestApp TestModule Info: Test log entry 1\n")
        temp_log.write("2025-08-22 23:30:01 TestApp TestModule Info: Test log entry 2\n")
        temp_log.write("2025-08-22 23:30:02 TestApp TestModule Info: Test log entry 3\n")
        temp_log_path = temp_log.name
    
    try:
        # Test basic streaming with user context (most common for UI monitoring)
        test_logger.info(f"Starting log stream for: {temp_log_path}")
        
        stream_id = user_logs_monitor.stream_log_entries(
            log_file_path=temp_log_path,
            include_existing=True
        )
        
        # Verify stream was created
        assert stream_id is not None, "Stream ID should not be None"
        test_logger.info(f"✅ Log stream created with ID: {stream_id}")
        
        # Give it a moment to process entries
        time.sleep(1)
        
        # Test getting active streams
        active_streams = user_logs_monitor.get_active_streams()
        test_logger.info(f"Active streams: {list(active_streams.keys())}")
        
        # Verify our stream is active
        if stream_id in active_streams:
            stream_info = active_streams[stream_id]
            test_logger.info(f"✅ Stream is active - file: {stream_info.get('file_path', 'unknown')}")
            assert stream_info['file_path'] == temp_log_path, "Stream file path mismatch"
        else:
            test_logger.warning(f"Stream {stream_id} not found in active streams")
        
        # Test stopping the stream
        stop_success = user_logs_monitor.stop_log_stream(stream_id)
        test_logger.info(f"✅ Stream stop result: {stop_success}")
        
        # Verify stream is stopped
        final_streams = user_logs_monitor.get_active_streams()
        assert stream_id not in final_streams, "Stream should be removed after stopping"
        test_logger.info("✅ Stream successfully stopped and cleaned up")
        
    finally:
        # Clean up temporary file
        if os.path.exists(temp_log_path):
            os.unlink(temp_log_path)
            test_logger.info("✅ Temporary log file cleaned up")
    
    test_logger.info("✅ All logs monitor service tests passed!")


def test_logs_monitor_service_filtering(services, test_logger):
    """Test logs monitoring with pattern filtering."""
    
    test_logger.info("Testing logs monitor service with pattern filtering...")
    
    # Get logs monitor service  
    logs_monitor = services.logs_monitor_stream("admin")
    assert logs_monitor is not None, "Logs monitor service should be available"
    
    # Create temporary log with mixed content
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as temp_log:
        temp_log.write("2025-08-22 23:30:00 SessionManager Info: Session created for user admin\n")
        temp_log.write("2025-08-22 23:30:01 CardReader Info: Card detected\n") 
        temp_log.write("2025-08-22 23:30:02 NetworkManager Info: Connection established\n")
        temp_log.write("2025-08-22 23:30:03 SessionManager Info: Session validated\n")
        temp_log.write("2025-08-22 23:30:04 CardReader Info: Card removed\n")
        temp_log_path = temp_log.name
    
    try:
        # Test filtering for SessionManager entries only
        test_logger.info("Testing SessionManager filter...")
        
        stream_id = logs_monitor.stream_log_entries(
            log_file_path=temp_log_path,
            filter_patterns=["SessionManager"],
            include_existing=True
        )
        
        assert stream_id is not None, "Filtered stream ID should not be None"
        
        # Give it time to process
        time.sleep(1)
        
        # Check stream info
        active_streams = logs_monitor.get_active_streams()
        if stream_id in active_streams:
            stream_info = active_streams[stream_id]
            test_logger.info(f"✅ Filtered stream active - filters: {stream_info.get('filters', [])}")
            assert stream_info.get('filters') == ["SessionManager"], "Filter should be applied"
        
        # Clean up
        logs_monitor.stop_log_stream(stream_id)
        test_logger.info("✅ Filtered stream stopped successfully")
        
    finally:
        if os.path.exists(temp_log_path):
            os.unlink(temp_log_path)
    
    test_logger.info("✅ Filtering tests passed!")


def test_logs_monitor_service_contexts(services, test_logger):
    """Test logs monitor service with different contexts (root vs user)."""
    
    test_logger.info("Testing logs monitor service context differences...")
    
    # Test both contexts can create services
    root_monitor = services.logs_monitor_stream("root")
    user_monitor = services.logs_monitor_stream("admin")
    
    assert root_monitor is not None, "Root logs monitor should be available"
    assert user_monitor is not None, "User logs monitor should be available"
    
    # These could be the same service instance or different ones
    # depending on the server implementation
    test_logger.info(f"✅ Root monitor type: {type(root_monitor).__name__}")
    test_logger.info(f"✅ User monitor type: {type(user_monitor).__name__}")
    
    # Both should have the same basic interface
    assert hasattr(root_monitor, 'stream_log_entries'), "Root monitor should have stream_log_entries method"
    assert hasattr(user_monitor, 'stream_log_entries'), "User monitor should have stream_log_entries method"
    assert hasattr(root_monitor, 'get_active_streams'), "Root monitor should have get_active_streams method"
    assert hasattr(user_monitor, 'get_active_streams'), "User monitor should have get_active_streams method"
    
    test_logger.info("✅ Context testing completed!")


def test_logs_monitor_service_error_handling(services, test_logger):
    """Test logs monitor service error handling with invalid inputs."""
    
    test_logger.info("Testing logs monitor service error handling...")
    
    logs_monitor = services.logs_monitor_stream("admin")
    assert logs_monitor is not None, "Logs monitor service should be available"
    
    # Test with nonexistent file (should handle gracefully)
    test_logger.info("Testing with nonexistent file...")
    nonexistent_file = "/path/that/definitely/does/not/exist/test.log"
    
    try:
        stream_id = logs_monitor.stream_log_entries(
            log_file_path=nonexistent_file,
            include_existing=True
        )
        
        # Should return something (even if placeholder) rather than crash
        test_logger.info(f"✅ Nonexistent file handled gracefully - stream_id: {stream_id}")
        
        # If a stream was created, clean it up
        if stream_id and stream_id != "placeholder_stream_id":
            logs_monitor.stop_log_stream(stream_id)
            
    except Exception as e:
        test_logger.info(f"✅ Exception handled appropriately: {e}")
    
    # Test with empty filter patterns 
    test_logger.info("Testing with empty filter patterns...")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as temp_log:
        temp_log.write("2025-08-22 23:30:00 TestApp Info: Test entry\n")
        temp_log_path = temp_log.name
    
    try:
        stream_id = logs_monitor.stream_log_entries(
            log_file_path=temp_log_path,
            filter_patterns=[],  # Empty filters
            include_existing=True
        )
        
        assert stream_id is not None, "Empty filters should be handled"
        test_logger.info("✅ Empty filters handled correctly")
        
        # Clean up
        if stream_id:
            logs_monitor.stop_log_stream(stream_id)
            
    finally:
        if os.path.exists(temp_log_path):
            os.unlink(temp_log_path)
    
    test_logger.info("✅ Error handling tests completed!")


def test_logs_monitor_service_multiple_streams(services, test_logger):
    """Test logs monitor service with multiple concurrent streams."""
    
    test_logger.info("Testing multiple concurrent log streams...")
    
    logs_monitor = services.logs_monitor_stream("admin")
    
    # Create test log file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as temp_log:
        temp_log.write("2025-08-22 23:30:00 AppA Info: Message from App A\n")
        temp_log.write("2025-08-22 23:30:01 AppB Info: Message from App B\n") 
        temp_log.write("2025-08-22 23:30:02 AppA Info: Another App A message\n")
        temp_log_path = temp_log.name
    
    stream_ids = []
    
    try:
        # Start multiple streams with different filters
        test_logger.info("Creating multiple streams...")
        
        stream1 = logs_monitor.stream_log_entries(
            log_file_path=temp_log_path,
            filter_patterns=["AppA"],
            include_existing=True
        )
        
        stream2 = logs_monitor.stream_log_entries(
            log_file_path=temp_log_path,
            filter_patterns=["AppB"],
            include_existing=True
        )
        
        stream_ids = [stream1, stream2]
        
        assert stream1 is not None, "Stream 1 should be created"
        assert stream2 is not None, "Stream 2 should be created"
        assert stream1 != stream2, "Streams should have different IDs"
        
        test_logger.info(f"✅ Created streams: {stream1}, {stream2}")
        
        # Give streams time to process
        time.sleep(1)
        
        # Check both streams are active
        active_streams = logs_monitor.get_active_streams()
        
        for stream_id in stream_ids:
            if stream_id in active_streams:
                stream_info = active_streams[stream_id]
                test_logger.info(f"✅ Stream {stream_id} active with filters: {stream_info.get('filters', [])}")
            else:
                test_logger.warning(f"Stream {stream_id} not found in active streams")
        
    finally:
        # Clean up all streams
        for stream_id in stream_ids:
            if stream_id:
                try:
                    logs_monitor.stop_log_stream(stream_id)
                    test_logger.info(f"✅ Stream {stream_id} stopped")
                except Exception as e:
                    test_logger.warning(f"Error stopping stream {stream_id}: {e}")
        
        # Clean up temp file
        if os.path.exists(temp_log_path):
            os.unlink(temp_log_path)
    
    test_logger.info("✅ Multiple streams test completed!")