"""
LogMonitorStreaming - High-level event detection using streaming backend.

This provides automated event detection with sophisticated filtering and timing
correlation, built on top of the LogsMonitoringServiceClient streaming service.
"""

import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass

from test_framework.utils.handlers.file_analayzer.entry import LogEntry
from test_framework.utils import get_logger


@dataclass
class EventCriteria:
    """Criteria for automated event detection with streaming."""
    start_time: datetime
    target_patterns: List[str]
    required_components: List[str] = None
    message_contains: List[str] = None
    message_excludes: List[str] = None
    entry_types: List[str] = None
    process_names: List[str] = None
    timeout_seconds: int = 30
    min_entries_required: int = 1


class LogMonitorStreaming:
    """
    High-level automated event detection using streaming backend.
    
    Provides a simple blocking interface for waiting until specific log events
    occur, with sophisticated filtering and automatic timeout/cleanup handling.
    """
    
    def __init__(self, logs_monitor_service, log_file_path: str, test_logger=None):
        """
        Initialize streaming-based log monitor.
        
        Args:
            logs_monitor_service: LogsMonitoringServiceClient instance
            log_file_path: Path to log file to monitor
            test_logger: Logger instance (optional)
        """
        self.logs_monitor = logs_monitor_service
        self.log_file_path = log_file_path
        self.logger = test_logger or get_logger(f"LogMonitorStreaming")
        
    def wait_for_events(self, criteria: EventCriteria) -> Optional[List[LogEntry]]:
        """
        Wait for events matching criteria using streaming.
        
        This is the main method - it blocks until events are found or timeout occurs.
        
        Args:
            criteria: EventCriteria specifying what events to wait for
            
        Returns:
            List[LogEntry]: Matching entries if found, None if timeout
        """
        self.logger.info(f"Starting streaming event detection for patterns: {criteria.target_patterns}")
        
        # Build structured criteria from EventCriteria
        structured_criteria = self._build_structured_criteria(criteria)
        
        try:
            # Start streaming with all criteria
            stream_id = self.logs_monitor.stream_log_entries(
                log_file_path=self.log_file_path,
                filter_patterns=criteria.target_patterns,
                include_existing=True,
                structured_criteria=structured_criteria
            )
            
            if not stream_id or stream_id == "placeholder_stream_id":
                self.logger.warning("Streaming service not available")
                return None
            
            # Wait for events with timeout
            matching_entries = self._wait_for_matching_entries(stream_id, criteria)
            
            return matching_entries
            
        except Exception as e:
            self.logger.error(f"Error in streaming event detection: {e}")
            return None
        finally:
            # Always clean up stream
            if 'stream_id' in locals():
                self.logs_monitor.stop_log_stream(stream_id)
    
    def _build_structured_criteria(self, criteria: EventCriteria) -> Dict:
        """Build structured criteria dict from EventCriteria object."""
        structured = {}
        
        if criteria.required_components:
            # Use first component for filtering (streaming limitation)
            structured["component"] = criteria.required_components[0]
            
        if criteria.entry_types:
            # Use first entry type for filtering
            structured["type"] = criteria.entry_types[0]
            
        if criteria.process_names:
            # Use first process name for filtering
            structured["process_name"] = criteria.process_names[0]
            
        return structured if structured else None
    
    def _wait_for_matching_entries(self, stream_id: str, criteria: EventCriteria) -> Optional[List[LogEntry]]:
        """
        Wait for entries matching criteria with timeout.
        
        Monitors the stream until we find enough matching entries or timeout.
        """
        start_time = time.time()
        check_interval = 0.5  # Check every 500ms
        
        while time.time() - start_time < criteria.timeout_seconds:
            # Get current entries from stream
            active_streams = self.logs_monitor.get_active_streams()
            
            if stream_id not in active_streams:
                self.logger.warning(f"Stream {stream_id} no longer active")
                break
                
            stream_info = active_streams[stream_id]
            all_entries = stream_info.get('entries', [])
            
            if not all_entries:
                time.sleep(check_interval)
                continue
            
            # Filter entries by start time
            relevant_entries = self._filter_by_time_range(all_entries, criteria.start_time)
            
            if not relevant_entries:
                time.sleep(check_interval)
                continue
            
            # Apply additional filtering
            matching_entries = self._apply_additional_filtering(relevant_entries, criteria)
            
            # Check if we have enough matches
            if len(matching_entries) >= criteria.min_entries_required:
                elapsed = time.time() - start_time
                self.logger.info(f"Found {len(matching_entries)} matching entries after {elapsed:.2f}s")
                return matching_entries
            
            time.sleep(check_interval)
        
        # Timeout reached
        elapsed = time.time() - start_time
        self.logger.warning(f"Timeout after {elapsed:.2f}s - found {len(matching_entries) if 'matching_entries' in locals() else 0} entries (needed {criteria.min_entries_required})")
        return None
    
    def _filter_by_time_range(self, entries: List[LogEntry], start_time: datetime) -> List[LogEntry]:
        """Filter entries to only those after start_time."""
        relevant_entries = []
        
        for entry in entries:
            if not entry.timestamp:
                continue
                
            try:
                # Parse entry timestamp
                entry_time = self._parse_timestamp(entry.timestamp)
                
                # Only include entries after start time
                if entry_time >= start_time:
                    relevant_entries.append(entry)
            except Exception as e:
                self.logger.debug(f"Could not parse timestamp '{entry.timestamp}': {e}")
                continue
        
        return relevant_entries
    
    def _apply_additional_filtering(self, entries: List[LogEntry], criteria: EventCriteria) -> List[LogEntry]:
        """Apply additional filtering criteria that weren't handled by structured criteria."""
        filtered_entries = entries
        
        # Additional component filtering (if multiple components specified)
        if criteria.required_components and len(criteria.required_components) > 1:
            component_filtered = []
            for entry in filtered_entries:
                if any(comp.lower() in entry.component.lower() for comp in criteria.required_components):
                    component_filtered.append(entry)
            filtered_entries = component_filtered
        
        # Message contains filtering
        if criteria.message_contains:
            message_filtered = []
            for entry in filtered_entries:
                if all(pattern.lower() in entry.message.lower() for pattern in criteria.message_contains):
                    message_filtered.append(entry)
            filtered_entries = message_filtered
        
        # Message excludes filtering
        if criteria.message_excludes:
            exclude_filtered = []
            for entry in filtered_entries:
                if not any(pattern.lower() in entry.message.lower() for pattern in criteria.message_excludes):
                    exclude_filtered.append(entry)
            filtered_entries = exclude_filtered
        
        # Additional entry type filtering (if multiple types specified)
        if criteria.entry_types and len(criteria.entry_types) > 1:
            type_filtered = []
            for entry in filtered_entries:
                if any(entry_type.lower() in entry.type.lower() for entry_type in criteria.entry_types):
                    type_filtered.append(entry)
            filtered_entries = type_filtered
        
        # Additional process name filtering (if multiple names specified)
        if criteria.process_names and len(criteria.process_names) > 1:
            process_filtered = []
            for entry in filtered_entries:
                if any(proc.lower() in entry.process_name.lower() for proc in criteria.process_names):
                    process_filtered.append(entry)
            filtered_entries = process_filtered
        
        return filtered_entries
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp string to datetime object."""
        timestamp_formats = [
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%d %H:%M:%S.%f",
            "%d %H:%M:%S"
        ]
        
        for fmt in timestamp_formats:
            try:
                parsed_time = datetime.strptime(timestamp_str, fmt)
                
                # For day-only timestamps, assume current year/month
                if fmt.startswith("%d"):
                    current_time = datetime.now()
                    parsed_time = parsed_time.replace(
                        year=current_time.year,
                        month=current_time.month
                    )
                
                return parsed_time
            except ValueError:
                continue
        
        # If all parsing fails, return current time
        self.logger.warning(f"Could not parse timestamp: {timestamp_str}")
        return datetime.now()