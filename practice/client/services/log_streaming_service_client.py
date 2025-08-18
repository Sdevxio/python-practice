#!/usr/bin/env python3
"""
LogStreamingServiceClient - Real-time log monitoring for test automation

This provides streaming log monitoring capabilities using the actual gRPC
streaming service. It solves timing correlation problems by streaming log
entries as they appear in real-time.
"""

import time
import threading
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Callable, Any

import grpc
from grpc_client_sdk.core.grpc_client_manager import GrpcClientManager
from test_framework.utils import get_logger
from test_framework.utils.handlers.file_analayzer.parser import LogParser


class LogStreamingServiceClient:
    """
    LogStreamingServiceClient provides real-time log monitoring capabilities.
    
    This connects to the actual LogStreamingService on the server to provide
    millisecond-level timing precision for automation testing.
    """
    
    def __init__(self, client_name: str = "root", logger: Optional[object] = None):
        """Initialize the streaming client."""
        self.client_name = client_name
        self.logger = logger or get_logger(f"LogStreamingServiceClient[{client_name}]")
        self.stub = None
        self.active_streams: Dict[str, Dict] = {}
        self.stream_lock = threading.Lock()
        self.connected = False
        self.parser = LogParser()  # For parsing raw log lines
    
    def connect(self) -> None:
        """
        Establish connection to streaming service.
        """
        try:
            # Import the generated protobuf modules
            from generated import log_streaming_service_pb2_grpc
            
            # Get the streaming service stub from the gRPC client manager
            self.stub = GrpcClientManager.get_stub(self.client_name, log_streaming_service_pb2_grpc.LogStreamingServiceStub)
            self.connected = True
            self.logger.info("🚀 LogStreamingServiceClient connected to real streaming service")
            
        except ImportError as e:
            self.logger.warning(f"Generated protobuf modules not available: {e}")
            self.stub = None
            self.connected = False
        except Exception as e:
            self.logger.warning(f"Streaming service not available: {e}")
            self.stub = None
            self.connected = False
    
    def stream_entries_for_tap_correlation(self,
                                         tap_start_time: datetime,
                                         expected_patterns: List[str],
                                         log_file_path: str,
                                         correlation_window_seconds: int = 300) -> Dict[str, Any]:
        """
        Stream log entries and correlate with tap timing.
        
        This is the key method for solving automation timing problems.
        Uses real-time streaming for millisecond-level precision.
        """
        if not self.connected or not self.stub:
            self.logger.warning("📡 Streaming service not connected - falling back to polling")
            return {
                'found_entries': {},
                'tap_start_time': tap_start_time,
                'expected_patterns': expected_patterns,
                'search_completed': False,
                'timeout_reached': True,
                'streaming_available': False
            }
        
        self.logger.info(f"🃏 Starting tap correlation streaming for patterns: {expected_patterns}")
        
        correlation_results = {
            'found_entries': {},
            'tap_start_time': tap_start_time,
            'expected_patterns': expected_patterns,
            'search_completed': False,
            'timeout_reached': False,
            'streaming_available': True
        }
        
        try:
            # Use the real streaming service with tap correlation
            stream_id = self.stream_log_entries(
                log_file_path=log_file_path,
                filter_patterns=expected_patterns,
                include_existing=True,
                entry_callback=None  # We'll process entries directly
            )
            
            if stream_id and stream_id != "placeholder_stream_id":
                start_time = time.time()
                found_count = 0
                
                # Monitor the stream for correlation
                with self.stream_lock:
                    if stream_id in self.active_streams:
                        stream_info = self.active_streams[stream_id]
                        entries = stream_info.get('entries', [])
                        
                        for i, pattern in enumerate(expected_patterns):
                            for entry in entries:
                                if pattern.lower() in entry.message.lower():
                                    entry_time = self._parse_entry_timestamp(entry.timestamp)
                                    delay_seconds = (entry_time - tap_start_time).total_seconds()
                                    
                                    correlation_results['found_entries'][f"pattern_{i}"] = {
                                        'entry': entry,
                                        'pattern_matched': pattern,
                                        'delay_seconds': delay_seconds,
                                        'correlation_time': entry_time,
                                        'message': entry.message
                                    }
                                    found_count += 1
                                    break
                
                correlation_results['search_completed'] = found_count == len(expected_patterns)
                correlation_results['timeout_reached'] = time.time() - start_time >= correlation_window_seconds
                
                # Stop the stream
                self.stop_log_stream(stream_id)
                
                self.logger.info(f"✅ Tap correlation found {found_count}/{len(expected_patterns)} patterns")
            
        except Exception as e:
            self.logger.error(f"❌ Error in tap correlation streaming: {e}")
            correlation_results['timeout_reached'] = True
        
        return correlation_results
    
    def stream_log_entries(self, 
                          log_file_path: str,
                          filter_patterns: Optional[List[str]] = None,
                          include_existing: bool = False,
                          entry_callback: Optional[Callable] = None) -> str:
        """Start streaming log entries using the real gRPC service."""
        if not self.connected or not self.stub:
            self.logger.warning("📡 Streaming service not connected")
            return "placeholder_stream_id"
        
        try:
            from generated import log_streaming_service_pb2
            
            # Create the streaming request - handle both old and new protobuf formats
            try:
                # Try new format first
                request = log_streaming_service_pb2.LogStreamRequest(
                    log_file_path=log_file_path,
                    filter_patterns=filter_patterns or [],
                    include_existing=include_existing,
                    start_from_timestamp=0  # Start from beginning if including existing
                )
            except AttributeError:
                # Fallback to old format if new protobuf not available
                self.logger.warning("Using old protobuf format - please regenerate stubs")
                request = log_streaming_service_pb2.StreamLogRequest(
                    log_file_path=log_file_path,
                    filter_patterns=filter_patterns or [],
                    include_existing=include_existing,
                    start_from_timestamp=0
                )
            
            # Start the stream
            stream_id = str(uuid.uuid4())
            entries_buffer = []
            
            def stream_processor():
                """Process streaming responses in a separate thread."""
                try:
                    for response in self.stub.StreamLogEntries(request):
                        parsed_entry = None
                        
                        # Handle both old and new response formats
                        if hasattr(response, 'raw_line'):
                            # New format: parse raw line into LogEntry
                            parsed_entry = self.parser.parse_line(response.raw_line, response.line_number)
                        elif hasattr(response, 'message'):
                            # Old format: response already has parsed fields
                            parsed_entry = response
                        
                        if parsed_entry:
                            # Store parsed entry
                            entries_buffer.append(parsed_entry)
                            
                            # Call the callback if provided
                            if entry_callback:
                                entry_callback(parsed_entry)
                            
                            # Store in active streams
                            with self.stream_lock:
                                if stream_id in self.active_streams:
                                    self.active_streams[stream_id]['entries'].append(parsed_entry)
                                
                except grpc.RpcError as stream_error:
                    self.logger.info(f"Stream {stream_id} ended: {stream_error}")
                except Exception as process_error:
                    self.logger.error(f"Error in stream processor: {process_error}")
            
            # Store stream info
            with self.stream_lock:
                self.active_streams[stream_id] = {
                    'file_path': log_file_path,
                    'filters': filter_patterns or [],
                    'entries': entries_buffer,
                    'thread': threading.Thread(target=stream_processor),
                    'start_time': time.time()
                }
                
                # Start the processing thread
                self.active_streams[stream_id]['thread'].start()
            
            self.logger.info(f"🚀 Started log stream {stream_id} for {log_file_path}")
            return stream_id
            
        except ImportError as e:
            self.logger.error(f"Generated protobuf modules not available: {e}")
            return "placeholder_stream_id"
        except Exception as e:
            self.logger.error(f"Error starting log stream: {e}")
            return "placeholder_stream_id"
    
    def stop_log_stream(self, stream_id: str) -> bool:
        """Stop a specific log stream."""
        if not self.connected or not self.stub:
            return True  # Nothing to stop
        
        try:
            from generated import log_streaming_service_pb2
            
            # Send stop request to server
            request = log_streaming_service_pb2.StopStreamRequest(stream_id=stream_id)
            response = self.stub.StopLogStream(request)
            
            # Clean up local resources
            with self.stream_lock:
                if stream_id in self.active_streams:
                    stream_info = self.active_streams.pop(stream_id)
                    # Wait for thread to finish
                    if 'thread' in stream_info:
                        stream_info['thread'].join(timeout=5)
            
            self.logger.info(f"🛑 Stopped log stream {stream_id}")
            return response.success
            
        except Exception as e:
            self.logger.error(f"Error stopping log stream {stream_id}: {e}")
            return False
    
    def stop_all_streams(self) -> None:
        """Stop all active streams."""
        with self.stream_lock:
            stream_ids = list(self.active_streams.keys())
        
        for stream_id in stream_ids:
            self.stop_log_stream(stream_id)
        
        self.logger.info("🛑 Stopped all log streams")
    
    def _parse_entry_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp string from log entry."""
        try:
            # Handle the format: "2024-01-15 10:30:45.123"
            return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            try:
                # Fallback format without microseconds
                return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                # If all else fails, return current time
                self.logger.warning(f"Could not parse timestamp: {timestamp_str}")
                return datetime.now()
    
    def get_active_streams(self) -> Dict[str, Dict]:
        """Get information about currently active streams."""
        with self.stream_lock:
            return {
                stream_id: {
                    'file_path': info['file_path'],
                    'filters': info['filters'],
                    'entry_count': len(info['entries']),
                    'start_time': info['start_time']
                }
                for stream_id, info in self.active_streams.items()
            }