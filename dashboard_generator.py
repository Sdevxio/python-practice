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


def create_login_timing_dashboard(artifacts_dir: str = "/Users/admin/PA/artifacts") -> str:
    """Create an interactive HTML dashboard for login timing performance."""
    
    # Collect JSON files
    pattern = f"{artifacts_dir}/**/desktop_agent_ui_performance_*.json"
    json_files = glob.glob(pattern, recursive=True)
    
    if not json_files:
        print("No performance data found")
        return ""
    
    # Parse timing data
    timing_data = []
    for file_path in json_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
                timestamp_str = data.get('test_run_timestamp', '')
                duration = data.get('ui_switch_duration_seconds')
                
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
        print("No valid timing data found")
        return ""
    
    # Sort by timestamp
    timing_data.sort(key=lambda x: x['timestamp'])
    
    # Calculate statistics
    durations = [d['duration'] for d in timing_data]
    avg_duration = sum(durations) / len(durations)
    min_duration = min(durations)
    max_duration = max(durations)
    latest_duration = durations[-1]
    
    # Determine trend
    if len(durations) >= 3:
        recent_avg = sum(durations[-3:]) / 3
        earlier_avg = sum(durations[:3]) / 3
        trend = "improving" if recent_avg < earlier_avg else "degrading"
        trend_icon = "📈" if trend == "improving" else "📉"
    else:
        trend = "stable"
        trend_icon = "➖"
    
    # Prepare data for chart
    chart_labels = [d['formatted_time'] for d in timing_data]
    chart_values = [d['duration'] for d in timing_data]
    
    # Load HTML template
    template_path = Path(__file__).parent / "dashboard.html"
    with open(template_path, 'r') as f:
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
    
    # Save HTML file
    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    html_path = f"{artifacts_dir}/login_timing_dashboard_{timestamp_str}.html"
    
    with open(html_path, 'w') as f:
        f.write(html_content)
    
    print(f"📊 Login timing dashboard created: {html_path}")
    return html_path


def auto_generate_dashboard():
    """Auto-generate dashboard - called from performance tests."""
    try:
        dashboard_path = create_login_timing_dashboard()
        if dashboard_path:
            return dashboard_path
    except Exception as e:
        import traceback
        print(f"Dashboard generation failed: {e}")
        print(f"Full error: {traceback.format_exc()}")
        return ""


if __name__ == "__main__":
    auto_generate_dashboard()
