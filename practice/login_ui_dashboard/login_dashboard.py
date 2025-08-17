#!/usr/bin/env python3
"""
Login Timing Performance Dashboard

Creates an HTML dashboard showing login timing performance from tap to UI appearance.
Focuses on actual timing data, not test pass/fail status.
"""

import json
import glob
import os
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path


def create_login_timing_dashboard(artifacts_dir: str = "/Users/admin/PA/artifacts", test_logger=None) -> str:
    """Create an interactive HTML dashboard for login timing performance."""
    
    # Collect JSON files
    pattern = f"{artifacts_dir}/**/desktop_agent_ui_performance_*.json"
    json_files = glob.glob(pattern, recursive=True)
    
    if not json_files:
        if test_logger:
            test_logger.info("No performance data found")
        else:
            print("No performance data found")
        return ""
    
    # Parse timing data
    timing_data = []
    for file_path in json_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
                timestamp_str = data.get('test_run_timestamp', '')
                # Check for both field names (hybrid monitor uses 'duration_seconds', old format uses 'ui_switch_duration_seconds')
                duration = data.get('duration_seconds') or data.get('ui_switch_duration_seconds')
                
                if timestamp_str and duration is not None and duration >= 0:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    timing_data.append({
                        'timestamp': timestamp,
                        'duration': duration,
                        'formatted_time': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        'duration_ms': round(duration * 1000, 1)  # Convert to milliseconds
                    })
        except Exception as e:
            continue
    
    if not timing_data:
        if test_logger:
            test_logger.info("No valid timing data found")
        else:
            print("No valid timing data found")
        return ""
    
    # Sort by timestamp and keep only the most recent 15 tests for trend analysis
    timing_data.sort(key=lambda x: x['timestamp'])
    timing_data = timing_data[-15:]  # Keep only last 15 tests
    
    # Calculate statistics
    durations = [d['duration'] for d in timing_data]
    avg_duration = sum(durations) / len(durations)
    min_duration = min(durations)
    max_duration = max(durations)
    latest_duration = durations[-1]
    
    # Determine trend using moving average comparison
    if len(durations) >= 6:
        # Compare recent half vs earlier half for more balanced analysis
        mid_point = len(durations) // 2
        recent_half = durations[mid_point:]
        earlier_half = durations[:mid_point]
        
        recent_avg = sum(recent_half) / len(recent_half)
        earlier_avg = sum(earlier_half) / len(earlier_half)
        
        # Calculate percentage change for more nuanced analysis
        percent_change = ((recent_avg - earlier_avg) / earlier_avg) * 100
        
        if percent_change < -5:  # 5% improvement threshold
            trend = "improving"
            trend_icon = ""
        elif percent_change > 5:  # 5% degradation threshold
            trend = "degrading" 
            trend_icon = ""
        else:
            trend = "stable"
            trend_icon = "➖"
    else:
        trend = "stable"
        trend_icon = "➖"
    
    # Prepare data for chart
    chart_labels = [d['formatted_time'] for d in timing_data]
    chart_values = [d['duration'] for d in timing_data]
    
    # Load HTML template
    template_path = Path(__file__).parent / "dashboard.html"
    with open(template_path, 'r', encoding='utf-8') as f:
        html_template = f.read()
    
    # Generate table rows for recent tests (last 10)
    table_rows = ""
    for test in timing_data[-10:]:
        duration = test['duration']
        if duration <= 1.5:
            status_class = "duration-good"
            status_text = "🟢 Excellent"
        elif duration <= 3.0:
            status_class = "duration-warning"
            status_text = "🟡 Good"
        else:
            status_class = "duration-bad"
            status_text = "🔴 Slow"
            
        table_rows += f"""
                    <tr>
                        <td>{test['formatted_time']}</td>
                        <td class="{status_class}">{duration:.3f}s</td>
                        <td>{test['duration_ms']}ms</td>
                        <td>{status_text}</td>
                    </tr>"""
    
    # Fill template with data
    html_content = html_template.format(
        latest_duration=latest_duration,
        avg_duration=avg_duration,
        min_duration=min_duration,
        max_duration=max_duration,
        total_tests=len(timing_data),
        trend_title=trend.title(),
        trend_icon=trend_icon,
        table_rows=table_rows,
        last_updated=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )
    
    # Replace JavaScript placeholders (after .format() to avoid conflicts)
    html_content = html_content.replace('CHART_LABELS_PLACEHOLDER', str(chart_labels))
    html_content = html_content.replace('CHART_VALUES_PLACEHOLDER', str(chart_values))
    
    # Save HTML file - single file instead of timestamped files
    html_path = f"{artifacts_dir}/login_timing_dashboard.html"
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    if test_logger:
        test_logger.info(f"Login timing dashboard updated: {html_path}")
    else:
        print(f"Login timing dashboard updated: {html_path}")
    return html_path


def auto_generate_dashboard(test_logger=None):
    """Auto-generate dashboard - called from performance tests."""
    try:
        dashboard_path = create_login_timing_dashboard(test_logger=test_logger)
        return dashboard_path
    except Exception as e:
        import traceback
        error_msg = f"Dashboard generation failed: {e}"
        if test_logger:
            test_logger.error(error_msg)
            test_logger.debug(f"Full error: {traceback.format_exc()}")
        else:
            print(error_msg)
            print(f"Full error: {traceback.format_exc()}")
        return ""


if __name__ == "__main__":
    auto_generate_dashboard()