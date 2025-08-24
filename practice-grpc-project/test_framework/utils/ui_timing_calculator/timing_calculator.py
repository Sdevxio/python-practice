"""
Simple Timing Calculator for log event analysis.

This class provides simple timestamp calculations between any two time points:
- Between two log entries
- Between test execution time and log entry
- Between any datetime objects

Keeps it simple with start_time/end_time approach.
"""

import time
from datetime import datetime
from typing import Union, Optional


class TimingCalculator:
    """
    Simple timing calculator for measuring delays between events.
    
    Can measure timing between:
    1. Two log entries
    2. Test execution time and log entry  
    3. Any datetime objects
    4. Current time and anything
    """
    
    def __init__(self):
        """Initialize timing calculator."""
        self.test_start_time = datetime.now()
        self.measurements = []
    
    def calculate_delay(self, start_time: Union[datetime, str, float, object], 
                       end_time: Union[datetime, str, float, object, None] = None) -> dict:
        """
        Calculate delay between start and end times.
        
        Args:
            start_time: Start timestamp (datetime, string, float, or log entry object)
            end_time: End timestamp (same types as start_time, or None for current time)
            
        Returns:
            dict: Timing information with delay in seconds, milliseconds, and formatted strings
        """
        # Convert start_time to datetime
        start_dt = self._convert_to_datetime(start_time)
        
        # Convert end_time to datetime (or use current time)
        if end_time is None:
            end_dt = datetime.now()
        else:
            end_dt = self._convert_to_datetime(end_time)
        
        # Calculate delay
        delay_timedelta = end_dt - start_dt
        delay_seconds = delay_timedelta.total_seconds()
        delay_milliseconds = delay_seconds * 1000
        
        # Create measurement result
        measurement = {
            'start_time': start_dt,
            'end_time': end_dt,
            'delay_seconds': delay_seconds,
            'delay_milliseconds': delay_milliseconds,
            'delay_formatted': self._format_delay(delay_seconds),
            'start_formatted': start_dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'end_formatted': end_dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        }
        
        # Store measurement
        self.measurements.append(measurement)
        
        return measurement
    
    def measure_from_test_start(self, end_time: Union[datetime, str, float, object]) -> dict:
        """
        Measure timing from when test started to the given end time.
        
        Args:
            end_time: End timestamp (datetime, string, float, or log entry object)
            
        Returns:
            dict: Timing measurement from test start
        """
        return self.calculate_delay(self.test_start_time, end_time)
    
    def measure_from_now(self, start_time: Union[datetime, str, float, object]) -> dict:
        """
        Measure timing from given start time to current time.
        
        Args:
            start_time: Start timestamp (datetime, string, float, or log entry object)
            
        Returns:
            dict: Timing measurement to current time
        """
        return self.calculate_delay(start_time, None)
    
    def measure_between_entries(self, entry1: object, entry2: object) -> dict:
        """
        Measure timing between two log entries.
        
        Args:
            entry1: First log entry (with timestamp attribute)
            entry2: Second log entry (with timestamp attribute)
            
        Returns:
            dict: Timing measurement between entries
        """
        return self.calculate_delay(entry1, entry2)
    
    def get_summary(self) -> dict:
        """
        Get summary of all measurements taken.
        
        Returns:
            dict: Summary statistics of all measurements
        """
        if not self.measurements:
            return {
                'total_measurements': 0,
                'average_delay_seconds': 0,
                'min_delay_seconds': 0,
                'max_delay_seconds': 0,
                'measurements': []
            }
        
        delays = [m['delay_seconds'] for m in self.measurements]
        
        return {
            'total_measurements': len(self.measurements),
            'average_delay_seconds': sum(delays) / len(delays),
            'min_delay_seconds': min(delays),
            'max_delay_seconds': max(delays),
            'measurements': self.measurements
        }
    
    def _convert_to_datetime(self, timestamp: Union[datetime, str, float, object]) -> datetime:
        """
        Convert various timestamp formats to datetime object.
        
        Args:
            timestamp: Timestamp in various formats
            
        Returns:
            datetime: Converted datetime object
        """
        # Already a datetime
        if isinstance(timestamp, datetime):
            return timestamp
        
        # Unix timestamp (float)
        if isinstance(timestamp, (int, float)):
            return datetime.fromtimestamp(timestamp)
        
        # String timestamp
        if isinstance(timestamp, str):
            return self._parse_string_timestamp(timestamp)
        
        # Log entry object (has timestamp attribute)
        if hasattr(timestamp, 'timestamp'):
            return self._parse_string_timestamp(timestamp.timestamp)
        
        # Fallback - try to convert to string and parse
        try:
            return self._parse_string_timestamp(str(timestamp))
        except:
            raise ValueError(f"Cannot convert timestamp: {timestamp} (type: {type(timestamp)})")
    
    def _parse_string_timestamp(self, timestamp_str: str) -> datetime:
        """
        Parse string timestamp to datetime.
        
        Args:
            timestamp_str: Timestamp string in various formats
            
        Returns:
            datetime: Parsed datetime object
        """
        # Common timestamp formats
        formats = [
            '%Y-%m-%d %H:%M:%S.%f',      # 2025-08-15 18:27:13.916
            '%Y-%m-%d %H:%M:%S',         # 2025-08-15 18:27:13
            '%d %H:%M:%S.%f',            # 15 18:27:13.916 (day only)
            '%d %H:%M:%S',               # 15 18:27:13 (day only)
            '%H:%M:%S.%f',               # 18:27:13.916 (time only)
            '%H:%M:%S',                  # 18:27:13 (time only)
        ]
        
        for fmt in formats:
            try:
                parsed_time = datetime.strptime(timestamp_str, fmt)
                
                # Handle day-only timestamps (add current year/month)
                if fmt.startswith('%d'):
                    current_time = datetime.now()
                    parsed_time = parsed_time.replace(
                        year=current_time.year,
                        month=current_time.month
                    )
                
                # Handle time-only timestamps (add current date)
                elif fmt.startswith('%H'):
                    current_time = datetime.now()
                    parsed_time = parsed_time.replace(
                        year=current_time.year,
                        month=current_time.month,
                        day=current_time.day
                    )
                
                return parsed_time
                
            except ValueError:
                continue
        
        # If all parsing fails, return current time
        raise ValueError(f"Could not parse timestamp: {timestamp_str}")
    
    def _format_delay(self, delay_seconds: float) -> str:
        """
        Format delay in human-readable format.
        
        Args:
            delay_seconds: Delay in seconds
            
        Returns:
            str: Human-readable delay format
        """
        if delay_seconds < 0:
            return f"-{self._format_delay(-delay_seconds)}"
        
        if delay_seconds < 1:
            return f"{delay_seconds * 1000:.1f}ms"
        elif delay_seconds < 60:
            return f"{delay_seconds:.3f}s"
        elif delay_seconds < 3600:
            minutes = int(delay_seconds // 60)
            seconds = delay_seconds % 60
            return f"{minutes}m {seconds:.1f}s"
        else:
            hours = int(delay_seconds // 3600)
            remaining = delay_seconds % 3600
            minutes = int(remaining // 60)
            seconds = remaining % 60
            return f"{hours}h {minutes}m {seconds:.1f}s"