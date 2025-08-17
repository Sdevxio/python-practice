#!/usr/bin/env python3
"""
Simple Login UI Performance Test - Following your proven pattern

Single simple test following your desktop_agent_ui_process_performance_simple pattern.
No complex test classes, just one method that does everything simply.
"""

from test_framework.utils.handlers.log_monitoring.criteria import LogCriteria


def test_desktop_agent_ui_performance_streaming(streaming_monitor, session_config, test_logger):
    """Simple streaming test following your proven pattern."""
    
    test_logger.info(f"Starting simple streaming UI performance monitoring for user: {session_config['expected_user']}")
    
    # Use simple helper methods (like your LogCriteria.ui_timing_pair)
    start_criteria, end_criteria = LogCriteria.ui_timing_pair(session_config["expected_user"])
    
    # One method call does everything (like your monitor.measure_timing)
    streaming_monitor.measure_timing_hybrid(
        session_config=session_config,
        start_criteria=start_criteria,
        end_criteria=end_criteria,
        test_name="desktop_agent_ui_performance_streaming"
    )
    
    test_logger.info("Simple streaming UI performance monitoring completed")