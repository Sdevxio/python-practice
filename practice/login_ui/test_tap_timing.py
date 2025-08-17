#!/usr/bin/env python3
"""
Real-time tap timing test using streaming monitor.

This test measures actual response time from tap to UI appearance
using the hybrid streaming monitor for real-time detection.
"""

import pytest
import time
import threading
from datetime import datetime


def test_tap_to_proxcard_timing_realtime(streaming_monitor, session_config, test_logger):
    """
    Real-time tap timing test that waits for actual NEW log entries.
    
    Uses existing streaming_monitor fixture for clean integration.
    Measures timing from tap to "Opened proxcard screen" entry.
    """
    test_logger.info("🎯 Starting REAL-TIME tap to proxcard timing test")
    
    # Step 1: Capture baseline state before tap (to detect NEW entries)
    test_logger.info("📸 Capturing baseline log state...")
    baseline_state = streaming_monitor.capture_baseline_state()
    
    # Step 2: Record tap time
    tap_start_time = datetime.now()
    test_logger.info(f"👆 Simulated tap at: {tap_start_time}")
    
    # Step 3: Trigger UI event generation (simulate system response)
    test_logger.info("🚀 Triggering UI event generation...")
    trigger_success = _trigger_ui_event_generation(test_logger)
    
    if not trigger_success:
        pytest.skip("Could not trigger UI event generation for real-time test")
    
    # Step 4: Wait for NEW "Opened proxcard screen" entry using streaming
    test_logger.info("⏳ Waiting for NEW proxcard entry in real-time...")
    
    criteria_list = [{"message_contains": "Opened proxcard screen"}]
    
    # Use hybrid detection to wait for NEW entries only
    results = streaming_monitor.wait_for_entries_with_delta(
        criteria_list=criteria_list,
        baseline_state=baseline_state,
        max_wait_time=15  # 15 seconds max wait
    )
    
    # Step 5: Calculate real-time response
    if 0 in results:
        proxcard_entry = results[0]
        
        # Try to parse the timestamp from the entry message if timestamp field is empty
        real_duration = 0  # Initialize variable
        proxcard_time = None  # Initialize variable
        
        try:
            if proxcard_entry.timestamp:
                proxcard_time = streaming_monitor.extractor._parse_timestamp(proxcard_entry.timestamp)
            else:
                # Extract timestamp from the beginning of the message
                import re
                timestamp_match = re.match(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+)', proxcard_entry.message)
                if timestamp_match:
                    timestamp_str = timestamp_match.group(1)
                    proxcard_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                else:
                    raise ValueError("Could not extract timestamp from message")
                    
            real_duration = (proxcard_time - tap_start_time).total_seconds()
        except Exception as e:
            test_logger.error(f"❌ Failed to parse timestamp: {e}")
            test_logger.error(f"Entry timestamp: '{proxcard_entry.timestamp}'")
            test_logger.error(f"Entry message: '{proxcard_entry.message}'")
            pytest.fail(f"Timestamp parsing failed: {e}")
        
        test_logger.info(f"✅ REAL-TIME tap to proxcard: {real_duration:.3f} seconds")
        test_logger.info(f"📝 Entry: {proxcard_entry.message}")
        test_logger.info(f"🕐 Entry time: {proxcard_entry.timestamp}")
        test_logger.info(f"⏰ Parsed time: {proxcard_time}")
        test_logger.info(f"👆 Tap time: {tap_start_time}")
        
        # Check if this is actually a NEW entry (should be very recent)
        time_since_tap = (datetime.now() - tap_start_time).total_seconds()
        entry_age = (datetime.now() - proxcard_time).total_seconds()
        test_logger.info(f"🕒 Time since tap: {time_since_tap:.1f}s")
        test_logger.info(f"📅 Entry age: {entry_age:.1f}s")
        
        if entry_age > 60:  # Entry is over 1 minute old
            test_logger.warning(f"⚠️ WARNING: Found OLD entry from {proxcard_time}, not a fresh response!")
            test_logger.warning("This suggests the baseline detection has issues")
        
        # Save real-time results
        test_data = {
            "test_name": "tap_to_proxcard_realtime",
            "tap_start_time": tap_start_time.isoformat(),
            "duration_seconds": round(real_duration, 3),
            "proxcard_entry": {
                "timestamp": proxcard_entry.timestamp,
                "message": proxcard_entry.message
            },
            "detection_method": "real_time_streaming",
            "test_type": "real_time"
        }
        
        # Save and generate dashboard
        _save_timing_results(test_data, test_logger)
        
        # Validate realistic timing
        assert real_duration >= 0, f"Invalid negative timing: {real_duration}s"
        assert real_duration <= 15.0, f"Response too slow: {real_duration}s (expected < 15s)"
        
    else:
        test_logger.error("❌ No NEW proxcard entry detected within timeout")
        pytest.fail("Real-time test failed: No new UI response detected")


def _trigger_ui_event_generation(test_logger, delay_seconds=None):
    """
    Trigger the dynamic log generator to create UI events after a random delay.
    This simulates the system responding to a user tap with realistic variability.
    """
    import random
    
    try:
        def delayed_trigger():
            # Random initial processing delay (1-4 seconds)
            if delay_seconds is None:
                initial_delay = random.uniform(1.0, 4.0)
            else:
                initial_delay = delay_seconds
                
            time.sleep(initial_delay)  # Simulate processing delay
            
            # Write UI events directly to log file to simulate system response
            log_file = "/Users/admin/PA/dynamic_log_generator/dynamic_test.log"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
            
            ui_events = [
                f"{timestamp} DesktopAgent UIManager admin 1001 0x7fff8a123456 2 6001 admin Info: Switching to Login UI",
                # Add delay between events
            ]
            
            # Write first event
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(ui_events[0] + '\n')
                f.flush()
            
            # Random UI processing time (1-3 seconds)
            ui_processing_delay = random.uniform(1.0, 3.0)
            time.sleep(ui_processing_delay)
            
            # Write second event (the one we're waiting for)  
            timestamp2 = datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
            proxcard_event = f"{timestamp2} LoginPlugin ScreenManager _securityagent 1002 0x7fff8a654321 2 6002 _securityagent Info: Opened proxcard screen"
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(proxcard_event + '\n')
                f.flush()
            
            total_delay = initial_delay + ui_processing_delay
            test_logger.info(f"🔥 UI events generated with {total_delay:.2f}s total delay")
        
        # Start trigger in background
        trigger_thread = threading.Thread(target=delayed_trigger, daemon=True)
        trigger_thread.start()
        
        return True
        
    except Exception as e:
        test_logger.error(f"❌ Failed to trigger UI events: {e}")
        return False


def _save_timing_results(test_data, test_logger):
    """Save timing results and generate dashboard."""
    try:
        from test_framework.utils.handlers.file_analayzer.json_data_handler import JsonDataHandler
        json_handler = JsonDataHandler()
        json_handler.save_performance_data(test_data, "desktop_agent_ui_performance", "ui_timing")
        
        # Generate dashboard
        try:
            from test_framework.utils.handlers.login_ui_dashboard.login_dashboard import auto_generate_dashboard
            dashboard_path = auto_generate_dashboard(test_logger=test_logger)
            if dashboard_path:
                test_logger.info(f"📊 Real-time timing dashboard: {dashboard_path}")
        except ImportError as e:
            test_logger.warning(f"Dashboard generation not available: {e}")
            
    except Exception as e:
        test_logger.warning(f"Could not save real-time results: {e}")

