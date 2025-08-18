import os
import threading
import time
import uuid
from datetime import datetime
from typing import Dict, Optional, List

import grpc
from generated import log_streaming_service_pb2
from generated import log_streaming_service_pb2_grpc
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from grpc_client.test_framework.utils import get_logger


class LogFileHandler(FileSystemEventHandler):
    """File system event handler for monitoring log file changes."""

    def __init__(self, log_file_path: str, stream_callback, filter_patterns: List[str], logger):
        """
        Initialize the log file handler.

        Args:
            log_file_path: Path to the log file to monitor
            stream_callback: Callback function to call when new entries are found
            filter_patterns: List of patterns to filter log entries
            logger: Logger instance
        """
        self.log_file_path = log_file_path
        self.stream_callback = stream_callback
        self.filter_patterns = filter_patterns
        self.logger = logger
        self.last_position = self._get_file_size()
        self.lock = threading.Lock()

    def _get_file_size(self) -> int:
        """Get current file size."""
        try:
            return os.path.getsize(self.log_file_path) if os.path.exists(self.log_file_path) else 0
        except OSError:
            return 0

    def on_modified(self, event):
        """Handle file modification events."""
        if event.src_path == self.log_file_path and not event.is_directory:
            self._process_new_content()

    def _process_new_content(self):
        """Process new content added to the log file."""
        with self.lock:
            try:
                current_size = self._get_file_size()
                if current_size <= self.last_position:
                    return  # No new content

                with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(self.last_position)
                    new_content = f.read()
                    self.last_position = f.tell()

                # Process new lines
                for line_num, line in enumerate(new_content.splitlines(),
                                                start=self._estimate_line_number()):
                    if line.strip() and self._matches_filters(line):
                        response = self._create_stream_response(line, line_num, "pending", self.last_position)
                        if response:
                            self.stream_callback(response)

            except Exception as e:
                self.logger.error(f"Error processing new log content: {e}")

    def _estimate_line_number(self) -> int:
        """Estimate current line number based on file position."""
        try:
            with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(0, 0)
                content_to_position = f.read(self.last_position)
                return content_to_position.count('\n') + 1
        except Exception:
            return 1

    def _matches_filters(self, line: str) -> bool:
        """Check if line matches any of the filter patterns."""
        if not self.filter_patterns:
            return True

        for pattern in self.filter_patterns:
            if pattern.lower() in line.lower():
                return True
        return False

    def _create_stream_response(self, line: str, line_number: int, stream_id: str,
                                file_position: int) -> Optional[log_streaming_service_pb2.LogStreamResponse]:
        """Create a simple stream response with raw line data."""
        try:
            # Simple timestamp detection (optional, for client convenience)
            detected_timestamp = ""
            import re
            timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\.\d{3})', line)
            if timestamp_match:
                detected_timestamp = timestamp_match.group(1)

            return log_streaming_service_pb2.LogStreamResponse(
                raw_line=line.strip(),
                line_number=line_number,
                stream_id=stream_id,
                file_position=file_position,
                detected_timestamp=detected_timestamp
            )

        except Exception as e:
            self.logger.warning(f"Failed to create stream response for line {line_number}: {e}")
            return None


class LogStreamingServicer(log_streaming_service_pb2_grpc.LogStreamingServiceServicer):
    """gRPC service for streaming log entries in real-time."""

    def __init__(self):
        """Initialize the log streaming service."""
        self.logger = get_logger(__name__)
        self.active_streams: Dict[str, Dict] = {}  # stream_id -> stream_info
        self.observers: Dict[str, Observer] = {}  # stream_id -> observer
        self.lock = threading.Lock()

    def StreamLogEntries(self, request, context):
        """Stream log entries in real-time as they're written to the file."""
        stream_id = str(uuid.uuid4())
        log_file_path = request.log_file_path
        filter_patterns = list(request.filter_patterns)
        start_from_timestamp = request.start_from_timestamp
        include_existing = request.include_existing

        self.logger.info(f"Starting log stream {stream_id} for file: {log_file_path}")

        # Validate file path
        if not os.path.exists(log_file_path):
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Log file not found: {log_file_path}")
            return

        if not os.access(log_file_path, os.R_OK):
            context.set_code(grpc.StatusCode.PERMISSION_DENIED)
            context.set_details(f"Cannot read log file: {log_file_path}")
            return

        # Queue for streaming responses
        response_queue = []
        queue_lock = threading.Lock()
        stream_active = True

        def stream_entry(entry):
            """Callback to add entries to the stream queue."""
            with queue_lock:
                if stream_active:
                    entry.stream_id = stream_id
                    response_queue.append(entry)

        try:
            # Process existing entries if requested
            if include_existing:
                self._process_existing_entries(log_file_path, filter_patterns,
                                               start_from_timestamp, stream_entry)

            # Set up file monitoring
            handler = LogFileHandler(log_file_path, stream_entry, filter_patterns, self.logger)
            observer = Observer()
            observer.schedule(handler, os.path.dirname(log_file_path), recursive=False)
            observer.start()

            # Store stream info
            with self.lock:
                self.active_streams[stream_id] = {
                    'file_path': log_file_path,
                    'filters': filter_patterns,
                    'context': context,
                    'start_time': time.time()
                }
                self.observers[stream_id] = observer

            self.logger.info(f"Log stream {stream_id} started successfully")

            # Stream entries to client
            try:
                while context.is_active() and stream_active:
                    # Send queued entries
                    entries_to_send = []
                    with queue_lock:
                        entries_to_send = response_queue.copy()
                        response_queue.clear()

                    for entry in entries_to_send:
                        if context.is_active():
                            yield entry
                        else:
                            break

                    # Small sleep to prevent busy waiting
                    time.sleep(0.1)

            except grpc.RpcError as e:
                self.logger.info(f"Client disconnected from stream {stream_id}: {e}")

        except Exception as e:
            self.logger.error(f"Error in log stream {stream_id}: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")

        finally:
            # Cleanup
            stream_active = False
            self._cleanup_stream(stream_id)
            self.logger.info(f"Log stream {stream_id} ended")

    def StopLogStream(self, request, context):
        """Stop a specific log stream."""
        stream_id = request.stream_id

        try:
            success = self._cleanup_stream(stream_id)
            message = f"Stream {stream_id} stopped successfully" if success else f"Stream {stream_id} not found"

            return log_streaming_service_pb2.StopStreamResponse(
                success=success,
                message=message
            )

        except Exception as e:
            self.logger.error(f"Error stopping stream {stream_id}: {e}")
            return log_streaming_service_pb2.StopStreamResponse(
                success=False,
                message=f"Error stopping stream: {str(e)}"
            )

    def _process_existing_entries(self, log_file_path: str, filter_patterns: List[str],
                                  start_from_timestamp: int, stream_callback):
        """Process existing entries in the log file."""
        try:
            with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                line_number = 1
                for line in f:
                    if line.strip():
                        # Simple timestamp filtering (can be enhanced)
                        if start_from_timestamp > 0:
                            # Basic timestamp extraction and comparison
                            # This is a simplified version - can be enhanced with proper parsing
                            pass

                        # Check filters
                        if not filter_patterns or any(pattern.lower() in line.lower()
                                                      for pattern in filter_patterns):
                            # Create simple response for existing entries
                            import re
                            detected_timestamp = ""
                            timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\.\d{3})', line)
                            if timestamp_match:
                                detected_timestamp = timestamp_match.group(1)

                            response = log_streaming_service_pb2.LogStreamResponse(
                                raw_line=line.strip(),
                                line_number=line_number,
                                stream_id="existing",  # Will be updated by callback
                                file_position=0,
                                detected_timestamp=detected_timestamp
                            )
                            stream_callback(response)

                    line_number += 1

        except Exception as e:
            self.logger.error(f"Error processing existing entries: {e}")

    def _cleanup_stream(self, stream_id: str) -> bool:
        """Clean up resources for a stream."""
        try:
            with self.lock:
                # Stop observer
                if stream_id in self.observers:
                    observer = self.observers.pop(stream_id)
                    observer.stop()
                    observer.join(timeout=5)

                # Remove stream info
                if stream_id in self.active_streams:
                    self.active_streams.pop(stream_id)
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Error cleaning up stream {stream_id}: {e}")
            return False

    def get_active_streams(self) -> Dict[str, Dict]:
        """Get information about currently active streams."""
        with self.lock:
            return self.active_streams.copy()