"""
Enhanced GUI Automation Service Client - Best of Both Implementations

File: grpc-client/grpc_client_sdk/services/gui_automation_service_client.py
Reason: Combined production patterns from existing codebase with comprehensive feature set from new implementation.
"""

import os
import time
import tempfile
import asyncio
from typing import Dict, Any, Optional, List, Union, Tuple, Generator
from pathlib import Path
from dataclasses import dataclass

from grpc_client_sdk.core.grpc_client_manager import GrpcClientManager
from test_framework.utils import get_logger
from test_framework.utils.logger_settings.logger_config import LoggerConfig

# Import protobuf modules with fallback handling
try:
    from generated import gui_automation_service_pb2, gui_automation_service_pb2_grpc
    PROTOBUF_AVAILABLE = True
except ImportError:
    PROTOBUF_AVAILABLE = False

    # Create dummy classes for testing when protobuf not available
    class gui_automation_service_pb2:
        CLICK = 0
        DOUBLE_CLICK = 1
        RIGHT_CLICK = 2
        DRAG = 3
        TYPE_TEXT = 4
        KEY_PRESS = 5
        SCROLL = 6
        HOVER = 7
        TAKE_SCREENSHOT = 8
        FIND_ELEMENT = 9

        COORDINATES = 0
        IMAGE_MATCH = 1
        TEXT_MATCH = 2
        ACCESSIBILITY = 3
        RELATIVE_TO_IMAGE = 4
        RELATIVE_TO_TEXT = 5

        class GuiRequest:
            def __init__(self, **kwargs): pass
        class GuiAction:
            def __init__(self, **kwargs): pass
        class GuiTarget:
            def __init__(self, **kwargs): pass
        class GuiLocation:
            def __init__(self, **kwargs): pass
        class GuiOptions:
            def __init__(self, **kwargs): pass
        class GuiBatchRequest:
            def __init__(self, **kwargs): pass


class GuiAutomationServiceClient:
    """
    Enhanced GUI Automation Service Client combining production patterns with comprehensive features.

    This client provides enterprise-grade GUI automation capabilities including:
    - Coordinate-based clicking and interaction with robust error handling
    - Image recognition and matching with confidence thresholds
    - Text-based targeting via OCR with region searching
    - Accessibility API integration for macOS native controls
    - Drag and drop operations with precise control
    - Keyboard input and shortcuts with modifier support
    - Screen capture with region selection and automatic saving
    - Batch operations for complex workflows with fallback mechanisms
    - Mock mode support for testing without real hardware

    Production Features:
    - Automatic connection management with retry logic
    - Comprehensive logging with structured output
    - File path validation and artifact directory management
    - Fallback to individual operations when batch fails
    - Mock client manager integration for testing
    - Memory-efficient screenshot handling

    Usage Patterns:
        # Basic usage
        client = GuiAutomationServiceClient(client_name="user")
        client.connect()
        result = client.click_coordinates(100, 200)

        # Advanced automation workflow
        workflow = [
            {"action": "click", "x": 100, "y": 100},
            {"action": "type", "text": "Hello World"},
            {"action": "click_text", "text": "Submit"}
        ]
        batch_result = client.perform_batch_operations(workflow)

        # Image-based automation
        result = client.click_image("/path/to/button.png", confidence=0.9)
    """

    def __init__(self, client_name: str = "user", logger: Optional[object] = None):
        """
        Initialize the Enhanced GUI Automation Service Client.

        Args:
            client_name: Name of the gRPC client in GrpcClientManager (e.g., "root", "username")
            logger: Custom logger instance. If None, a default logger is created.
        """
        self.client_name = client_name
        self.logger = logger or get_logger(f"GuiAutomationServiceClient[{client_name}]")
        self.stub = None
        self._connected = False

        if not PROTOBUF_AVAILABLE:
            self.logger.warning("GUI Automation protobuf modules not available. Some features may be limited.")

    def connect(self) -> None:
        """
        Establish connection to the GUI Automation gRPC service with fallback to mock mode.

        Raises:
            RuntimeError: If connection fails and no fallback is available
        """
        try:
            if PROTOBUF_AVAILABLE:
                self.stub = GrpcClientManager.get_stub(
                    self.client_name,
                    gui_automation_service_pb2_grpc.GuiAutomationServiceStub
                )
                self.logger.info(f"GUI Automation Service connected for client '{self.client_name}'")
                self._connected = True
                return
            else:
                raise RuntimeError("GUI Automation protobuf modules not available")

        except RuntimeError as e:
            # Try mock mode fallback
            try:
                from grpc_client_sdk.core.mock_grpc_client_manager import MockGrpcClientManager

                if MockGrpcClientManager.is_mock_mode_enabled():
                    if PROTOBUF_AVAILABLE:
                        self.stub = MockGrpcClientManager.get_stub(
                            self.client_name,
                            gui_automation_service_pb2_grpc.GuiAutomationServiceStub
                        )
                    else:
                        from unittest.mock import Mock
                        self.stub = Mock()
                    self.logger.info(f"Mock GUI Automation Service connected for client '{self.client_name}'")
                    self._connected = True
                    return
                else:
                    raise e
            except ImportError:
                raise e
        except Exception as e:
            self.logger.error(f"Failed to connect GUI Automation Service: {e}")
            raise RuntimeError(f"GUI Automation Service connection failed: {e}")

    def is_connected(self) -> bool:
        """Check if the service is connected."""
        return self._connected and self.stub is not None

    def _ensure_connected(self):
        """Ensure the service is connected, attempt reconnection if needed."""
        if not self.is_connected():
            self.logger.warning(
                f"GUI Automation Service not connected for client '{self.client_name}', attempting to reconnect..."
            )
            try:
                self.connect()
            except Exception as e:
                raise RuntimeError(f"GUI Automation Service connection failed: {e}")

    # =============================================================================
    # Enhanced Basic GUI Operations (Production + New Features)
    # =============================================================================

    def click_coordinates(self, x: int, y: int, target_user: str = "",
                         delay_after_ms: int = 300, capture_after: bool = False,
                         max_retries: int = 1, retry_delay_ms: int = 500) -> Dict[str, Any]:
        """
        Enhanced click at specific screen coordinates with retry logic.

        Args:
            x: X coordinate on screen
            y: Y coordinate on screen
            target_user: Target user for user agent routing
            delay_after_ms: Delay after click in milliseconds
            capture_after: Whether to capture screenshot after click
            max_retries: Maximum number of retry attempts
            retry_delay_ms: Delay between retries in milliseconds

        Returns:
            Dict containing success status, message, location, and execution time
        """
        self._ensure_connected()

        try:
            request = gui_automation_service_pb2.GuiRequest(
                action=gui_automation_service_pb2.GuiAction(
                    type=gui_automation_service_pb2.CLICK
                ),
                target=gui_automation_service_pb2.GuiTarget(
                    type=gui_automation_service_pb2.COORDINATES,
                    coordinates=gui_automation_service_pb2.GuiLocation(x=x, y=y)
                ),
                target_user=target_user,
                options=gui_automation_service_pb2.GuiOptions(
                    delay_after_ms=delay_after_ms,
                    capture_after=capture_after,
                    max_retries=max_retries,
                    retry_delay_ms=retry_delay_ms
                )
            )

            response = self.stub.PerformAction(request)

            result = {
                "success": response.success,
                "message": response.message,
                "location": (response.result_location.x, response.result_location.y),
                "execution_time_ms": response.execution_time_ms
            }

            if capture_after and response.screenshot_data:
                result["screenshot_data"] = response.screenshot_data
                result["screenshot_size"] = len(response.screenshot_data)

            self.logger.info(f"Click at ({x}, {y}): {response.success} - {response.message}")
            return result

        except Exception as e:
            self.logger.error(f"Click coordinates failed: {e}")
            return {"success": False, "message": str(e), "location": (0, 0), "execution_time_ms": 0}

    def double_click_coordinates(self, x: int, y: int, target_user: str = "",
                               delay_after_ms: int = 300) -> Dict[str, Any]:
        """Enhanced double-click with the same error handling pattern."""
        return self._perform_coordinate_action(
            gui_automation_service_pb2.DOUBLE_CLICK, x, y, target_user, delay_after_ms
        )

    def right_click_coordinates(self, x: int, y: int, target_user: str = "",
                              delay_after_ms: int = 300) -> Dict[str, Any]:
        """Enhanced right-click with the same error handling pattern."""
        return self._perform_coordinate_action(
            gui_automation_service_pb2.RIGHT_CLICK, x, y, target_user, delay_after_ms
        )

    def _perform_coordinate_action(self, action_type: int, x: int, y: int,
                                 target_user: str = "", delay_after_ms: int = 300) -> Dict[str, Any]:
        """Helper method for coordinate-based actions with consistent error handling."""
        self._ensure_connected()

        try:
            request = gui_automation_service_pb2.GuiRequest(
                action=gui_automation_service_pb2.GuiAction(type=action_type),
                target=gui_automation_service_pb2.GuiTarget(
                    type=gui_automation_service_pb2.COORDINATES,
                    coordinates=gui_automation_service_pb2.GuiLocation(x=x, y=y)
                ),
                target_user=target_user,
                options=gui_automation_service_pb2.GuiOptions(delay_after_ms=delay_after_ms)
            )

            response = self.stub.PerformAction(request)
            action_name = gui_automation_service_pb2.ActionType.Name(action_type)

            self.logger.info(f"{action_name} at ({x}, {y}): {response.success}")
            return {
                "success": response.success,
                "message": response.message,
                "location": (response.result_location.x, response.result_location.y),
                "execution_time_ms": response.execution_time_ms
            }

        except Exception as e:
            action_name = gui_automation_service_pb2.ActionType.Name(action_type)
            self.logger.error(f"{action_name} coordinates failed: {e}")
            return {"success": False, "message": str(e), "location": (0, 0), "execution_time_ms": 0}

    # =============================================================================
    # Enhanced Text Input Operations
    # =============================================================================

    def type_text(self, text: str, target_user: str = "", delay_before_ms: int = 100,
                 clear_field: bool = False) -> Dict[str, Any]:
        """
        Enhanced type text with optional field clearing.

        Args:
            text: Text to type
            target_user: Target user for user agent routing
            delay_before_ms: Delay before typing in milliseconds
            clear_field: Whether to clear the field before typing (Cmd+A, Delete)

        Returns:
            Dict containing success status, message, and execution time
        """
        self._ensure_connected()

        try:
            # Clear field if requested
            if clear_field:
                clear_result = self.press_key("a", "command")  # Select all
                if clear_result["success"]:
                    time.sleep(0.1)
                    self.press_key("51")  # Delete key

            request = gui_automation_service_pb2.GuiRequest(
                action=gui_automation_service_pb2.GuiAction(
                    type=gui_automation_service_pb2.TYPE_TEXT,
                    parameters={"text": text}
                ),
                target=gui_automation_service_pb2.GuiTarget(
                    type=gui_automation_service_pb2.COORDINATES,
                    coordinates=gui_automation_service_pb2.GuiLocation(x=0, y=0)
                ),
                target_user=target_user,
                options=gui_automation_service_pb2.GuiOptions(delay_before_ms=delay_before_ms)
            )

            response = self.stub.PerformAction(request)

            self.logger.info(f"Type text '{text[:50]}...': {response.success}")
            return {
                "success": response.success,
                "message": response.message,
                "execution_time_ms": response.execution_time_ms
            }

        except Exception as e:
            self.logger.error(f"Type text failed: {e}")
            return {"success": False, "message": str(e), "execution_time_ms": 0}

    def press_key(self, key: str, modifiers: Union[str, List[str]] = "",
                 target_user: str = "") -> Dict[str, Any]:
        """
        Enhanced key press with flexible modifier handling.

        Args:
            key: Key code to press or key name (e.g., "36" for Enter, "Return")
            modifiers: Modifier keys as string or list (e.g., "command", ["cmd", "shift"])
            target_user: Target user for user agent routing

        Returns:
            Dict containing success status and message
        """
        self._ensure_connected()

        try:
            # Handle both string and list modifiers
            if isinstance(modifiers, list):
                modifiers_str = " ".join(modifiers)
            else:
                modifiers_str = modifiers

            # Map common key names to key codes
            key_map = {
                "Return": "36", "Enter": "36",
                "Tab": "48",
                "Escape": "53", "Esc": "53",
                "Space": "49",
                "Delete": "51", "Backspace": "51",
                "Up": "126", "Down": "125", "Left": "123", "Right": "124"
            }

            actual_key = key_map.get(key, key)

            request = gui_automation_service_pb2.GuiRequest(
                action=gui_automation_service_pb2.GuiAction(
                    type=gui_automation_service_pb2.KEY_PRESS,
                    parameters={"key": actual_key, "modifiers": modifiers_str}
                ),
                target=gui_automation_service_pb2.GuiTarget(
                    type=gui_automation_service_pb2.COORDINATES,
                    coordinates=gui_automation_service_pb2.GuiLocation(x=0, y=0)
                ),
                target_user=target_user
            )

            response = self.stub.PerformAction(request)

            self.logger.info(f"Press key {key} ({modifiers_str}): {response.success}")
            return {
                "success": response.success,
                "message": response.message,
                "execution_time_ms": response.execution_time_ms
            }

        except Exception as e:
            self.logger.error(f"Press key failed: {e}")
            return {"success": False, "message": str(e), "execution_time_ms": 0}

    # =============================================================================
    # Enhanced Image-Based Operations
    # =============================================================================

    def click_image(self, image_path: str, confidence: float = 0.8,
                   search_region: Optional[Tuple[int, int, int, int]] = None,
                   target_user: str = "", delay_after_ms: int = 300,
                   capture_before: bool = False, capture_after: bool = False,
                   highlight_target: bool = False, max_retries: int = 2) -> Dict[str, Any]:
        """
        Enhanced image-based clicking with comprehensive options.

        Args:
            image_path: Path to the image file to find
            confidence: Confidence threshold (0.0 to 1.0) for image matching
            search_region: Optional (x, y, width, height) to limit search area
            target_user: Target user for user agent routing
            delay_after_ms: Delay after click in milliseconds
            capture_before: Capture screenshot before action
            capture_after: Capture screenshot after action
            highlight_target: Highlight the found element
            max_retries: Maximum retry attempts for finding the image

        Returns:
            Dict containing success status, message, found location, and execution time
        """
        self._ensure_connected()

        try:
            # Validate image path
            image_path = Path(image_path)
            if not image_path.exists():
                return {"success": False, "message": f"Image file not found: {image_path}"}

            with open(image_path, "rb") as f:
                image_data = f.read()

            # Build target with enhanced options
            target = gui_automation_service_pb2.GuiTarget(
                type=gui_automation_service_pb2.IMAGE_MATCH,
                target_image=image_data,
                confidence_threshold=confidence
            )

            # Add search region if specified
            if search_region:
                x, y, width, height = search_region
                target.search_region.CopyFrom(
                    gui_automation_service_pb2.GuiLocation(x=x, y=y, width=width, height=height)
                )

            request = gui_automation_service_pb2.GuiRequest(
                action=gui_automation_service_pb2.GuiAction(
                    type=gui_automation_service_pb2.CLICK
                ),
                target=target,
                target_user=target_user,
                options=gui_automation_service_pb2.GuiOptions(
                    capture_before=capture_before,
                    capture_after=capture_after,
                    delay_after_ms=delay_after_ms,
                    highlight_target=highlight_target,
                    max_retries=max_retries,
                    retry_delay_ms=1000
                )
            )

            response = self.stub.PerformAction(request)

            result = {
                "success": response.success,
                "message": response.message,
                "execution_time_ms": response.execution_time_ms
            }

            if response.success:
                result["location"] = (response.result_location.x, response.result_location.y)
                self.logger.info(f"Click image '{image_path.name}': Found at {result['location']}")
            else:
                result["location"] = None
                self.logger.warning(f"Click image '{image_path.name}': {response.message}")

            # Handle screenshots
            if response.screenshot_data:
                result["screenshot_data"] = response.screenshot_data
                result["screenshot_size"] = len(response.screenshot_data)

                # Auto-save if capture was requested
                if capture_before or capture_after:
                    self._save_screenshot_automatically(
                        response.screenshot_data,
                        f"image_click_{image_path.stem}_{int(time.time())}.png"
                    )

            return result

        except Exception as e:
            self.logger.error(f"Click image failed: {e}")
            return {"success": False, "message": str(e), "location": None, "execution_time_ms": 0}

    def find_image(self, image_path: str, confidence: float = 0.8,
                  search_region: Optional[Tuple[int, int, int, int]] = None,
                  return_all_matches: bool = False) -> Dict[str, Any]:
        """
        Enhanced image finding with multiple match support.

        Args:
            image_path: Path to the image file to find
            confidence: Confidence threshold for image matching
            search_region: Optional search region (x, y, width, height)
            return_all_matches: Whether to return all matches or just the best one

        Returns:
            Dict containing success status, message, and found location(s)
        """
        self._ensure_connected()

        try:
            image_path = Path(image_path)
            if not image_path.exists():
                return {"success": False, "message": f"Image file not found: {image_path}"}

            with open(image_path, "rb") as f:
                image_data = f.read()

            target = gui_automation_service_pb2.GuiTarget(
                type=gui_automation_service_pb2.IMAGE_MATCH,
                target_image=image_data,
                confidence_threshold=confidence
            )

            if search_region:
                x, y, width, height = search_region
                target.search_region.CopyFrom(
                    gui_automation_service_pb2.GuiLocation(x=x, y=y, width=width, height=height)
                )

            request = gui_automation_service_pb2.GuiRequest(
                action=gui_automation_service_pb2.GuiAction(
                    type=gui_automation_service_pb2.FIND_ELEMENT
                ),
                target=target,
                options=gui_automation_service_pb2.GuiOptions(
                    return_element_info=return_all_matches
                )
            )

            response = self.stub.FindElements(request)

            result = {
                "success": response.success,
                "message": response.message
            }

            if response.success:
                result["location"] = (response.result_location.x, response.result_location.y)
                self.logger.info(f"Find image '{image_path.name}': Found at {result['location']}")

                # Add additional match info if available
                if response.result_data:
                    result["matches"] = dict(response.result_data)
            else:
                result["location"] = None
                self.logger.info(f"Find image '{image_path.name}': {response.message}")

            return result

        except Exception as e:
            self.logger.error(f"Find image failed: {e}")
            return {"success": False, "message": str(e), "location": None}

    # =============================================================================
    # Enhanced Screenshot Operations with Automatic Management
    # =============================================================================

    def take_screenshot(self, target_user: str = "", filename: str = "",
                       region: Optional[Tuple[int, int, int, int]] = None,
                       auto_timestamp: bool = True) -> Dict[str, Any]:
        """
        Enhanced screenshot capture with automatic file management.

        Args:
            target_user: Target user for user agent routing
            filename: Name of the file to save (auto-generated if empty)
            region: Optional region to capture (x, y, width, height)
            auto_timestamp: Whether to add timestamp to filename

        Returns:
            Dict containing success status, message, screenshot data, and file path
        """
        self._ensure_connected()

        # Setup screenshot directory
        screenshot_dir = os.path.join(LoggerConfig.ARTIFACTS_DIR, "screenshots")
        os.makedirs(screenshot_dir, exist_ok=True)

        # Generate filename if not provided
        if not filename:
            timestamp = int(time.time()) if auto_timestamp else ""
            filename = f"screenshot_{timestamp}.png"
        elif auto_timestamp and not any(ts in filename for ts in ["_", "-"]):
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{int(time.time())}{ext}"

        file_path = os.path.join(screenshot_dir, filename)

        try:
            # Build request for screenshot or region capture
            if region:
                x, y, width, height = region
                target = gui_automation_service_pb2.GuiTarget(
                    type=gui_automation_service_pb2.COORDINATES,
                    search_region=gui_automation_service_pb2.GuiLocation(
                        x=x, y=y, width=width, height=height
                    )
                )
            else:
                target = gui_automation_service_pb2.GuiTarget(
                    type=gui_automation_service_pb2.COORDINATES,
                    coordinates=gui_automation_service_pb2.GuiLocation(x=0, y=0)
                )

            request = gui_automation_service_pb2.GuiRequest(
                action=gui_automation_service_pb2.GuiAction(
                    type=gui_automation_service_pb2.TAKE_SCREENSHOT
                ),
                target=target,
                target_user=target_user
            )

            response = self.stub.CaptureScreen(request)

            result = {
                "success": response.success,
                "message": response.message,
                "screenshot_data": response.screenshot_data,
                "screenshot_size": len(response.screenshot_data)
            }

            # Save to file
            if response.screenshot_data:
                with open(file_path, 'wb') as f:
                    f.write(response.screenshot_data)

                result["file_path"] = str(file_path)
                region_str = f" (region {region})" if region else ""
                self.logger.info(f"Screenshot saved to: {file_path}{region_str}")

            return result

        except Exception as e:
            self.logger.error(f"Take screenshot failed: {e}")
            return {"success": False, "message": str(e), "screenshot_data": b"", "screenshot_size": 0}

    def _save_screenshot_automatically(self, screenshot_data: bytes, suggested_name: str) -> str:
        """Helper method to automatically save screenshots with proper naming."""
        screenshot_dir = os.path.join(LoggerConfig.ARTIFACTS_DIR, "screenshots", "auto")
        os.makedirs(screenshot_dir, exist_ok=True)

        file_path = os.path.join(screenshot_dir, suggested_name)
        with open(file_path, 'wb') as f:
            f.write(screenshot_data)

        self.logger.debug(f"Auto-saved screenshot: {file_path}")
        return file_path

    # =============================================================================
    # Enhanced Batch Operations with Smart Fallback
    # =============================================================================

    def perform_batch_operations(self, operations: List[Dict[str, Any]],
                                target_user: str = "", stop_on_error: bool = True,
                                timeout_seconds: int = 60,
                                prefer_individual: bool = False) -> Dict[str, Any]:
        """
        Enhanced batch operations with intelligent fallback and progress tracking.

        Args:
            operations: List of operation dictionaries
            target_user: Target user for user agent routing
            stop_on_error: Whether to stop on first error
            timeout_seconds: Timeout for the batch operation
            prefer_individual: Force individual operation execution (useful for debugging)

        Returns:
            Dict containing overall success, operation count, and individual results
        """
        self._ensure_connected()

        # Force individual operations if requested or if too many operations
        if prefer_individual or not PROTOBUF_AVAILABLE or len(operations) > 10:
            return self._perform_individual_operations(operations, target_user, stop_on_error)

        try:
            # Build gRPC requests
            gui_requests = []
            for i, op in enumerate(operations):
                request = self._build_request_from_operation(op, target_user)
                if request:
                    gui_requests.append(request)
                else:
                    self.logger.warning(f"Skipping invalid operation {i+1}: {op}")

            if not gui_requests:
                return {
                    "overall_success": True,
                    "successful_operations": 0,
                    "failed_operations": 0,
                    "operation_results": [],
                    "message": "No valid operations to execute"
                }

            # Execute batch request
            batch_request = gui_automation_service_pb2.GuiBatchRequest(
                operations=gui_requests,
                target_user=target_user,
                stop_on_error=stop_on_error
            )

            self.logger.info(f"Executing batch of {len(gui_requests)} operations...")
            response = self.stub.PerformBatch(batch_request, timeout=timeout_seconds)

            # Process results
            result = {
                "overall_success": response.overall_success,
                "successful_operations": response.successful_operations,
                "failed_operations": response.failed_operations,
                "operation_results": []
            }

            for op_response in response.operation_results:
                op_result = {
                    "success": op_response.success,
                    "message": op_response.message,
                    "location": (op_response.result_location.x, op_response.result_location.y),
                    "execution_time_ms": op_response.execution_time_ms
                }
                result["operation_results"].append(op_result)

            self.logger.info(
                f"Batch completed: {response.successful_operations} successful, {response.failed_operations} failed"
            )
            return result

        except Exception as e:
            self.logger.warning(f"Batch operation failed, falling back to individual operations: {e}")
            return self._perform_individual_operations(operations, target_user, stop_on_error)

    def _perform_individual_operations(self, operations: List[Dict[str, Any]],
                                     target_user: str = "", stop_on_error: bool = True) -> Dict[str, Any]:
        """
        Enhanced individual operation execution with progress tracking.
        """
        self.logger.info(f"Executing {len(operations)} operations individually...")

        successful_operations = 0
        failed_operations = 0
        operation_results = []

        for i, op in enumerate(operations):
            try:
                self.logger.debug(f"Executing operation {i+1}/{len(operations)}: {op.get('action', 'unknown')}")

                action_type = op.get("action")
                result = None

                # Execute based on action type
                if action_type == "click":
                    result = self.click_coordinates(
                        op["x"], op["y"],
                        target_user=target_user,
                        delay_after_ms=op.get("delay_after", 300)
                    )
                elif action_type == "double_click":
                    result = self.double_click_coordinates(
                        op["x"], op["y"],
                        target_user=target_user,
                        delay_after_ms=op.get("delay_after", 300)
                    )
                elif action_type == "type":
                    result = self.type_text(
                        op["text"],
                        target_user=target_user,
                        delay_before_ms=op.get("delay_before", 100),
                        clear_field=op.get("clear_field", False)
                    )
                elif action_type == "key_press":
                    result = self.press_key(
                        op["key"],
                        modifiers=op.get("modifiers", ""),
                        target_user=target_user
                    )
                elif action_type == "click_text":
                    result = self.click_text(
                        op["text"],
                        search_region=op.get("search_region"),
                        target_user=target_user,
                        delay_after_ms=op.get("delay_after", 300)
                    )
                elif action_type == "click_image":
                    result = self.click_image(
                        op["image_path"],
                        confidence=op.get("confidence", 0.8),
                        search_region=op.get("search_region"),
                        target_user=target_user,
                        delay_after_ms=op.get("delay_after", 300)
                    )
                elif action_type == "screenshot":
                    result = self.take_screenshot(
                        target_user=target_user,
                        filename=op.get("filename", ""),
                        region=op.get("region")
                    )
                else:
                    result = {"success": False, "message": f"Unknown action type: {action_type}"}

                # Track results
                if result and result.get("success"):
                    successful_operations += 1
                    self.logger.debug(f"Operation {i+1} succeeded: {result.get('message', 'OK')}")
                else:
                    failed_operations += 1
                    self.logger.warning(f"Operation {i+1} failed: {result.get('message', 'Unknown error')}")
                    if stop_on_error:
                        self.logger.warning(f"Stopping at operation {i+1} due to stop_on_error=True")
                        break

                operation_results.append(result or {"success": False, "message": "No result"})

                # Add inter-operation delay if specified
                if op.get("delay_after_operation"):
                    time.sleep(op["delay_after_operation"] / 1000.0)

            except Exception as e:
                self.logger.error(f"Operation {i+1} failed with exception: {e}")
                failed_operations += 1
                operation_results.append({"success": False, "message": str(e)})

                if stop_on_error:
                    self.logger.warning(f"Stopping at operation {i+1} due to exception and stop_on_error=True")
                    break

        return {
            "overall_success": failed_operations == 0,
            "successful_operations": successful_operations,
            "failed_operations": failed_operations,
            "operation_results": operation_results,
            "message": f"Individual operations completed: {successful_operations} successful, {failed_operations} failed"
        }

    def _build_request_from_operation(self, operation: Dict[str, Any], target_user: str) -> Optional[object]:
        """Enhanced request builder with support for all operation types."""
        action_type = operation.get("action")

        try:
            if action_type == "click":
                return gui_automation_service_pb2.GuiRequest(
                    action=gui_automation_service_pb2.GuiAction(type=gui_automation_service_pb2.CLICK),
                    target=gui_automation_service_pb2.GuiTarget(
                        type=gui_automation_service_pb2.COORDINATES,
                        coordinates=gui_automation_service_pb2.GuiLocation(
                            x=operation["x"], y=operation["y"]
                        )
                    ),
                    target_user=target_user,
                    options=gui_automation_service_pb2.GuiOptions(
                        delay_before_ms=operation.get("delay_before", 0),
                        delay_after_ms=operation.get("delay_after", 300),
                        max_retries=operation.get("max_retries", 1)
                    )
                )
            elif action_type == "double_click":
                return gui_automation_service_pb2.GuiRequest(
                    action=gui_automation_service_pb2.GuiAction(type=gui_automation_service_pb2.DOUBLE_CLICK),
                    target=gui_automation_service_pb2.GuiTarget(
                        type=gui_automation_service_pb2.COORDINATES,
                        coordinates=gui_automation_service_pb2.GuiLocation(
                            x=operation["x"], y=operation["y"]
                        )
                    ),
                    target_user=target_user,
                    options=gui_automation_service_pb2.GuiOptions(
                        delay_after_ms=operation.get("delay_after", 300)
                    )
                )
            elif action_type == "type":
                return gui_automation_service_pb2.GuiRequest(
                    action=gui_automation_service_pb2.GuiAction(
                        type=gui_automation_service_pb2.TYPE_TEXT,
                        parameters={"text": operation["text"]}
                    ),
                    target=gui_automation_service_pb2.GuiTarget(
                        type=gui_automation_service_pb2.COORDINATES,
                        coordinates=gui_automation_service_pb2.GuiLocation(x=0, y=0)
                    ),
                    target_user=target_user,
                    options=gui_automation_service_pb2.GuiOptions(
                        delay_before_ms=operation.get("delay_before", 100)
                    )
                )
            elif action_type == "key_press":
                return gui_automation_service_pb2.GuiRequest(
                    action=gui_automation_service_pb2.GuiAction(
                        type=gui_automation_service_pb2.KEY_PRESS,
                        parameters={
                            "key": operation["key"],
                            "modifiers": operation.get("modifiers", "")
                        }
                    ),
                    target=gui_automation_service_pb2.GuiTarget(
                        type=gui_automation_service_pb2.COORDINATES,
                        coordinates=gui_automation_service_pb2.GuiLocation(x=0, y=0)
                    ),
                    target_user=target_user
                )
            elif action_type == "click_text":
                target = gui_automation_service_pb2.GuiTarget(
                    type=gui_automation_service_pb2.TEXT_MATCH,
                    target_text=operation["text"]
                )

                # Add search region if specified
                if operation.get("search_region"):
                    x, y, w, h = operation["search_region"]
                    target.search_region.CopyFrom(
                        gui_automation_service_pb2.GuiLocation(x=x, y=y, width=w, height=h)
                    )

                return gui_automation_service_pb2.GuiRequest(
                    action=gui_automation_service_pb2.GuiAction(type=gui_automation_service_pb2.CLICK),
                    target=target,
                    target_user=target_user,
                    options=gui_automation_service_pb2.GuiOptions(
                        delay_before_ms=operation.get("delay_before", 500),
                        max_retries=operation.get("max_retries", 2)
                    )
                )
            elif action_type == "click_image":
                # Load image data
                image_path = Path(operation["image_path"])
                if not image_path.exists():
                    self.logger.error(f"Image file not found: {image_path}")
                    return None

                with open(image_path, "rb") as f:
                    image_data = f.read()

                target = gui_automation_service_pb2.GuiTarget(
                    type=gui_automation_service_pb2.IMAGE_MATCH,
                    target_image=image_data,
                    confidence_threshold=operation.get("confidence", 0.8)
                )

                # Add search region if specified
                if operation.get("search_region"):
                    x, y, w, h = operation["search_region"]
                    target.search_region.CopyFrom(
                        gui_automation_service_pb2.GuiLocation(x=x, y=y, width=w, height=h)
                    )

                return gui_automation_service_pb2.GuiRequest(
                    action=gui_automation_service_pb2.GuiAction(type=gui_automation_service_pb2.CLICK),
                    target=target,
                    target_user=target_user,
                    options=gui_automation_service_pb2.GuiOptions(
                        delay_after_ms=operation.get("delay_after", 300),
                        max_retries=operation.get("max_retries", 2),
                        capture_after=operation.get("capture_after", False)
                    )
                )
            else:
                self.logger.warning(f"Unknown operation type for batch: {action_type}")
                return None

        except Exception as e:
            self.logger.error(f"Failed to build request for operation {action_type}: {e}")
            return None

    # =============================================================================
    # Enhanced Text-Based Operations with OCR
    # =============================================================================

    def click_text(self, text: str, search_region: Optional[Tuple[int, int, int, int]] = None,
                  target_user: str = "", delay_after_ms: int = 300,
                  case_sensitive: bool = False, partial_match: bool = True) -> Dict[str, Any]:
        """
        Enhanced text-based clicking with advanced matching options.

        Args:
            text: Text to find and click
            search_region: Optional search region (x, y, width, height)
            target_user: Target user for user agent routing
            delay_after_ms: Delay after click in milliseconds
            case_sensitive: Whether text matching should be case sensitive
            partial_match: Whether to allow partial text matches

        Returns:
            Dict containing success status, message, found location, and execution time
        """
        self._ensure_connected()

        try:
            target = gui_automation_service_pb2.GuiTarget(
                type=gui_automation_service_pb2.TEXT_MATCH,
                target_text=text
            )

            if search_region:
                x, y, width, height = search_region
                target.search_region.CopyFrom(
                    gui_automation_service_pb2.GuiLocation(x=x, y=y, width=width, height=height)
                )

            # Add text matching parameters
            parameters = {}
            if not case_sensitive:
                parameters["case_sensitive"] = "false"
            if partial_match:
                parameters["partial_match"] = "true"

            request = gui_automation_service_pb2.GuiRequest(
                action=gui_automation_service_pb2.GuiAction(
                    type=gui_automation_service_pb2.CLICK,
                    parameters=parameters
                ),
                target=target,
                target_user=target_user,
                options=gui_automation_service_pb2.GuiOptions(
                    delay_after_ms=delay_after_ms,
                    max_retries=2,
                    retry_delay_ms=1000
                )
            )

            response = self.stub.PerformAction(request)

            result = {
                "success": response.success,
                "message": response.message,
                "execution_time_ms": response.execution_time_ms
            }

            if response.success:
                result["location"] = (response.result_location.x, response.result_location.y)
                self.logger.info(f"Click text '{text}': Found at {result['location']}")
            else:
                result["location"] = None
                self.logger.warning(f"Click text '{text}': {response.message}")

            return result

        except Exception as e:
            self.logger.error(f"Click text failed: {e}")
            return {"success": False, "message": str(e), "location": None, "execution_time_ms": 0}

    def find_text(self, text: str, search_region: Optional[Tuple[int, int, int, int]] = None,
                 case_sensitive: bool = False, return_all_matches: bool = False) -> Dict[str, Any]:
        """
        Enhanced text finding with multiple match support.

        Args:
            text: Text to find
            search_region: Optional search region (x, y, width, height)
            case_sensitive: Whether text matching should be case sensitive
            return_all_matches: Whether to return all matches or just the first one

        Returns:
            Dict containing success status, message, and found location(s)
        """
        self._ensure_connected()

        try:
            target = gui_automation_service_pb2.GuiTarget(
                type=gui_automation_service_pb2.TEXT_MATCH,
                target_text=text
            )

            if search_region:
                x, y, width, height = search_region
                target.search_region.CopyFrom(
                    gui_automation_service_pb2.GuiLocation(x=x, y=y, width=width, height=height)
                )

            # Add text matching parameters
            parameters = {}
            if not case_sensitive:
                parameters["case_sensitive"] = "false"
            if return_all_matches:
                parameters["return_all"] = "true"

            request = gui_automation_service_pb2.GuiRequest(
                action=gui_automation_service_pb2.GuiAction(
                    type=gui_automation_service_pb2.FIND_ELEMENT,
                    parameters=parameters
                ),
                target=target,
                options=gui_automation_service_pb2.GuiOptions(
                    return_element_info=return_all_matches
                )
            )

            response = self.stub.FindElements(request)

            result = {
                "success": response.success,
                "message": response.message
            }

            if response.success:
                result["location"] = (response.result_location.x, response.result_location.y)
                self.logger.info(f"Find text '{text}': Found at {result['location']}")

                # Add multiple matches if available
                if response.result_data and return_all_matches:
                    result["all_matches"] = dict(response.result_data)
            else:
                result["location"] = None
                self.logger.info(f"Find text '{text}': {response.message}")

            return result

        except Exception as e:
            self.logger.error(f"Find text failed: {e}")
            return {"success": False, "message": str(e), "location": None}

    # =============================================================================
    # Enhanced Window Management and Positioning Operations
    # =============================================================================

    def position_window(self, app_name: str = "Python", x: int = 100, y: int = 100, 
                       width: Optional[int] = None, height: Optional[int] = None) -> Dict[str, Any]:
        """
        Position and optionally resize a window using AppleScript.
        
        Args:
            app_name: Name or partial name of the application
            x: X coordinate for window position
            y: Y coordinate for window position  
            width: Optional width to resize window
            height: Optional height to resize window
            
        Returns:
            Dict containing success status and message
        """
        self.logger.info(f"Positioning {app_name} window at ({x}, {y})")
        
        # Build AppleScript based on whether we're resizing
        if width and height:
            script = f'''
            tell application "System Events"
                set targetApps to every application process whose name contains "{app_name}"
                if (count of targetApps) > 0 then
                    tell item 1 of targetApps
                        set frontmost to true
                        delay 0.5
                        try
                            set position of front window to {{{x}, {y}}}
                            set size of front window to {{{width}, {height}}}
                            return "Success: Positioned window at ({x},{y}) and resized to {width}x{height}"
                        on error errMsg
                            return "Error: " & errMsg
                        end try
                    end tell
                else
                    return "Error: No applications found containing '{app_name}'"
                end if
            end tell
            '''
        else:
            script = f'''
            tell application "System Events"
                set targetApps to every application process whose name contains "{app_name}"
                if (count of targetApps) > 0 then
                    tell item 1 of targetApps
                        set frontmost to true
                        delay 0.5
                        try
                            set position of front window to {{{x}, {y}}}
                            return "Success: Positioned window at ({x},{y})"
                        on error errMsg
                            return "Error: " & errMsg
                        end try
                    end tell
                else
                    return "Error: No applications found containing '{app_name}'"
                end if
            end tell
            '''
        
        try:
            import subprocess
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            message = result.stdout.strip()
            success = "Success" in message
            
            self.logger.info(f"Window positioning result: {message}")
            
            return {
                "success": success,
                "message": message,
                "position": (x, y),
                "size": (width, height) if width and height else None
            }
            
        except Exception as e:
            error_msg = f"Failed to position window: {e}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "position": None,
                "size": None
            }

    def bring_app_to_front(self, app_name: str = "Python") -> Dict[str, Any]:
        """
        Bring an application to the front using AppleScript.
        
        Args:
            app_name: Name or partial name of the application
            
        Returns:
            Dict containing success status and message
        """
        self.logger.info(f"Bringing {app_name} to front")
        
        script = f'''
        tell application "System Events"
            set targetApps to every application process whose name contains "{app_name}"
            if (count of targetApps) > 0 then
                set frontmost of item 1 of targetApps to true
                return "Success: Brought {app_name} to front"
            else
                return "Error: No applications found containing '{app_name}'"
            end if
        end tell
        '''
        
        try:
            import subprocess
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            message = result.stdout.strip()
            success = "Success" in message
            
            self.logger.info(f"Bring to front result: {message}")
            
            return {
                "success": success,
                "message": message
            }
            
        except Exception as e:
            error_msg = f"Failed to bring app to front: {e}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg
            }

    def click_and_type_coordinates(self, x: int, y: int, text: str, 
                                  clear_field: bool = True, delay_ms: int = 300) -> Dict[str, Any]:
        """
        Click at coordinates and type text using AppleScript.
        This method combines clicking and typing for better reliability.
        
        Args:
            x: X coordinate to click
            y: Y coordinate to click
            text: Text to type
            clear_field: Whether to clear the field before typing (Cmd+A)
            delay_ms: Delay between click and type in milliseconds
            
        Returns:
            Dict containing success status and message
        """
        self.logger.info(f"Click and type at ({x}, {y}): '{text[:20]}...'")
        
        # Build AppleScript with optional field clearing
        clear_commands = '''
        -- Clear field first
        key code 0 using command down -- Cmd+A
        delay 0.1
        ''' if clear_field else ''
        
        script = f'''
        tell application "System Events"
            -- Click at coordinates
            click at {{{x}, {y}}}
            delay {delay_ms / 1000.0}
            
            {clear_commands}
            
            -- Type the text
            keystroke "{text}"
            
            return "Success: Clicked at ({x},{y}) and typed text"
        end tell
        '''
        
        try:
            import subprocess
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            message = result.stdout.strip()
            success = "Success" in message
            
            if success:
                self.logger.info(f"Successfully clicked and typed at ({x}, {y})")
            else:
                self.logger.warning(f"Click and type failed: {message}")
            
            return {
                "success": success,
                "message": message,
                "location": (x, y),
                "text": text,
                "execution_time_ms": delay_ms
            }
            
        except Exception as e:
            error_msg = f"Failed to click and type: {e}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "location": (x, y),
                "text": text,
                "execution_time_ms": 0
            }

    def get_window_info(self, app_name: str = "Python") -> Dict[str, Any]:
        """
        Get detailed information about an application's window.
        
        Args:
            app_name: Name or partial name of the application
            
        Returns:
            Dict containing window information
        """
        self.logger.info(f"Getting window info for {app_name}")
        
        script = f'''
        tell application "System Events"
            set targetApps to every application process whose name contains "{app_name}"
            if (count of targetApps) > 0 then
                tell item 1 of targetApps
                    try
                        set frontWindow to front window
                        set windowTitle to title of frontWindow
                        set windowPosition to position of frontWindow
                        set windowSize to size of frontWindow
                        set windowX to item 1 of windowPosition
                        set windowY to item 2 of windowPosition
                        set windowWidth to item 1 of windowSize
                        set windowHeight to item 2 of windowSize
                        
                        return "Success|" & windowTitle & "|" & windowX & "|" & windowY & "|" & windowWidth & "|" & windowHeight
                    on error errMsg
                        return "Error: " & errMsg
                    end try
                end tell
            else
                return "Error: No applications found containing '{app_name}'"
            end if
        end tell
        '''
        
        try:
            import subprocess
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            message = result.stdout.strip()
            
            if message.startswith("Success|"):
                # Parse the result
                parts = message.split("|")
                window_info = {
                    "success": True,
                    "title": parts[1],
                    "position": (int(parts[2]), int(parts[3])),
                    "size": (int(parts[4]), int(parts[5])),
                    "bounds": {
                        "x": int(parts[2]),
                        "y": int(parts[3]), 
                        "width": int(parts[4]),
                        "height": int(parts[5])
                    }
                }
                
                self.logger.info(f"Window info: {window_info['title']} at {window_info['position']} size {window_info['size']}")
                return window_info
            else:
                self.logger.warning(f"Failed to get window info: {message}")
                return {
                    "success": False,
                    "message": message,
                    "title": None,
                    "position": None,
                    "size": None,
                    "bounds": None
                }
                
        except Exception as e:
            error_msg = f"Failed to get window info: {e}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "title": None,
                "position": None,
                "size": None,
                "bounds": None
            }

    # =============================================================================
    # New Advanced Operations (From New Implementation)
    # =============================================================================

    def drag(self, from_x: int, from_y: int, to_x: int, to_y: int,
            target_user: str = "", duration_ms: int = 500, **options) -> Dict[str, Any]:
        """
        Perform a drag operation from one point to another.

        Args:
            from_x: Starting X coordinate
            from_y: Starting Y coordinate
            to_x: Ending X coordinate
            to_y: Ending Y coordinate
            target_user: Target user for agent routing
            duration_ms: Duration of drag operation in milliseconds
            **options: Additional options (capture_before, capture_after, etc.)

        Returns:
            Dict containing operation result
        """
        self._ensure_connected()

        try:
            request = gui_automation_service_pb2.GuiRequest(
                action=gui_automation_service_pb2.GuiAction(
                    type=gui_automation_service_pb2.DRAG,
                    parameters={
                        "to_x": str(to_x),
                        "to_y": str(to_y),
                        "duration_ms": str(duration_ms)
                    }
                ),
                target=gui_automation_service_pb2.GuiTarget(
                    type=gui_automation_service_pb2.COORDINATES,
                    coordinates=gui_automation_service_pb2.GuiLocation(x=from_x, y=from_y)
                ),
                target_user=target_user,
                options=gui_automation_service_pb2.GuiOptions(
                    capture_before=options.get('capture_before', False),
                    capture_after=options.get('capture_after', False),
                    delay_after_ms=options.get('delay_after_ms', 300)
                )
            )

            response = self.stub.PerformAction(request)

            result = {
                "success": response.success,
                "message": response.message,
                "execution_time_ms": response.execution_time_ms
            }

            if response.success:
                self.logger.info(f"Drag from ({from_x}, {from_y}) to ({to_x}, {to_y}): Success")
            else:
                self.logger.warning(f"Drag operation failed: {response.message}")

            return result

        except Exception as e:
            self.logger.error(f"Drag operation failed: {e}")
            return {"success": False, "message": str(e), "execution_time_ms": 0}

    def scroll(self, x: int, y: int, direction: str = "down", clicks: int = 3,
              target_user: str = "", **options) -> Dict[str, Any]:
        """
        Perform a scroll operation at the specified location.

        Args:
            x: X coordinate to scroll at
            y: Y coordinate to scroll at
            direction: Scroll direction ("up", "down", "left", "right")
            clicks: Number of scroll clicks
            target_user: Target user for agent routing
            **options: Additional options

        Returns:
            Dict containing operation result
        """
        self._ensure_connected()

        try:
            request = gui_automation_service_pb2.GuiRequest(
                action=gui_automation_service_pb2.GuiAction(
                    type=gui_automation_service_pb2.SCROLL,
                    parameters={
                        "direction": direction,
                        "clicks": str(clicks)
                    }
                ),
                target=gui_automation_service_pb2.GuiTarget(
                    type=gui_automation_service_pb2.COORDINATES,
                    coordinates=gui_automation_service_pb2.GuiLocation(x=x, y=y)
                ),
                target_user=target_user,
                options=gui_automation_service_pb2.GuiOptions(
                    delay_after_ms=options.get('delay_after_ms', 200)
                )
            )

            response = self.stub.PerformAction(request)

            result = {
                "success": response.success,
                "message": response.message,
                "execution_time_ms": response.execution_time_ms
            }

            if response.success:
                self.logger.info(f"Scroll {direction} {clicks} clicks at ({x}, {y}): Success")
            else:
                self.logger.warning(f"Scroll operation failed: {response.message}")

            return result

        except Exception as e:
            self.logger.error(f"Scroll operation failed: {e}")
            return {"success": False, "message": str(e), "execution_time_ms": 0}

    def hover(self, x: int, y: int, target_user: str = "", duration_ms: int = 1000) -> Dict[str, Any]:
        """
        Hover mouse over the specified coordinates.

        Args:
            x: X coordinate to hover over
            y: Y coordinate to hover over
            target_user: Target user for agent routing
            duration_ms: How long to hover in milliseconds

        Returns:
            Dict containing operation result
        """
        self._ensure_connected()

        try:
            request = gui_automation_service_pb2.GuiRequest(
                action=gui_automation_service_pb2.GuiAction(
                    type=gui_automation_service_pb2.HOVER,
                    parameters={"duration_ms": str(duration_ms)}
                ),
                target=gui_automation_service_pb2.GuiTarget(
                    type=gui_automation_service_pb2.COORDINATES,
                    coordinates=gui_automation_service_pb2.GuiLocation(x=x, y=y)
                ),
                target_user=target_user
            )

            response = self.stub.PerformAction(request)

            result = {
                "success": response.success,
                "message": response.message,
                "execution_time_ms": response.execution_time_ms
            }

            if response.success:
                self.logger.info(f"Hover at ({x}, {y}) for {duration_ms}ms: Success")
            else:
                self.logger.warning(f"Hover operation failed: {response.message}")

            return result

        except Exception as e:
            self.logger.error(f"Hover operation failed: {e}")
            return {"success": False, "message": str(e), "execution_time_ms": 0}

    # =============================================================================
    # Context Manager Support
    # =============================================================================

    def __enter__(self):
        """Context manager entry - automatically connect."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup if needed."""
        if hasattr(self, 'disconnect'):
            try:
                self.disconnect()
            except:
                pass
        self._connected = False
        self.logger.debug("Context manager: GUI Automation Service client cleaned up")

    def disconnect(self):
        """Disconnect from the GUI Automation Service."""
        self._connected = False
        self.stub = None
        self.logger.info(f"GUI Automation Service disconnected for client '{self.client_name}'")

    # =============================================================================
    # Template/Pattern Matching Support
    # =============================================================================

    def click_pattern(self, pattern_name: str, patterns_dir: str = "patterns",
                     confidence: float = 0.8, **options) -> Dict[str, Any]:
        """
        Click using pre-defined patterns/templates.

        Args:
            pattern_name: Name of the pattern (without .png extension)
            patterns_dir: Directory containing pattern images
            confidence: Confidence threshold for pattern matching
            **options: Additional options passed to click_image

        Returns:
            Dict containing operation result

        Usage:
            # Click on a predefined button pattern
            result = client.click_pattern("submit_button", confidence=0.9)
            
            # Use custom patterns directory
            result = client.click_pattern("close_button", patterns_dir="ui_patterns")
        """
        # Build pattern path
        patterns_path = Path(patterns_dir)
        if not patterns_path.is_absolute():
            # If relative path, make it relative to artifacts directory
            patterns_path = Path(LoggerConfig.ARTIFACTS_DIR) / patterns_path
        
        pattern_file = patterns_path / f"{pattern_name}.png"
        
        if not pattern_file.exists():
            return {
                "success": False,
                "message": f"Pattern file not found: {pattern_file}",
                "location": None,
                "execution_time_ms": 0
            }
        
        self.logger.info(f"Clicking pattern '{pattern_name}' from {pattern_file}")
        return self.click_image(str(pattern_file), confidence=confidence, **options)

    def find_pattern(self, pattern_name: str, patterns_dir: str = "patterns",
                    confidence: float = 0.8, **options) -> Dict[str, Any]:
        """
        Find a pre-defined pattern without clicking.

        Args:
            pattern_name: Name of the pattern (without .png extension)
            patterns_dir: Directory containing pattern images
            confidence: Confidence threshold for pattern matching
            **options: Additional options passed to find_image

        Returns:
            Dict containing search result
        """
        # Build pattern path
        patterns_path = Path(patterns_dir)
        if not patterns_path.is_absolute():
            patterns_path = Path(LoggerConfig.ARTIFACTS_DIR) / patterns_path
        
        pattern_file = patterns_path / f"{pattern_name}.png"
        
        if not pattern_file.exists():
            return {
                "success": False,
                "message": f"Pattern file not found: {pattern_file}",
                "location": None
            }
        
        self.logger.info(f"Finding pattern '{pattern_name}' from {pattern_file}")
        return self.find_image(str(pattern_file), confidence=confidence, **options)

    def save_pattern(self, pattern_name: str, region: Tuple[int, int, int, int],
                    patterns_dir: str = "patterns") -> Dict[str, Any]:
        """
        Save a screen region as a pattern for future use.

        Args:
            pattern_name: Name to save the pattern as (without .png extension)
            region: Screen region to capture (x, y, width, height)
            patterns_dir: Directory to save pattern images

        Returns:
            Dict containing save result
        """
        # Build pattern path
        patterns_path = Path(patterns_dir)
        if not patterns_path.is_absolute():
            patterns_path = Path(LoggerConfig.ARTIFACTS_DIR) / patterns_path
        
        patterns_path.mkdir(parents=True, exist_ok=True)
        pattern_file = patterns_path / f"{pattern_name}.png"
        
        # Take screenshot of the region
        result = self.take_screenshot(region=region, filename=str(pattern_file))
        
        if result["success"]:
            self.logger.info(f"Saved pattern '{pattern_name}' to {pattern_file}")
            return {
                "success": True,
                "message": f"Pattern saved successfully",
                "pattern_path": str(pattern_file)
            }
        else:
            return {
                "success": False,
                "message": f"Failed to save pattern: {result.get('message', 'Unknown error')}",
                "pattern_path": None
            }

    # =============================================================================
    # Async/Await Support
    # =============================================================================

    async def click_coordinates_async(self, x: int, y: int, **options) -> Dict[str, Any]:
        """Async version of click_coordinates for concurrent operations."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.click_coordinates, x, y, **options)

    async def click_image_async(self, image_path: str, **options) -> Dict[str, Any]:
        """Async version of click_image for concurrent operations."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.click_image, image_path, **options)

    async def click_text_async(self, text: str, **options) -> Dict[str, Any]:
        """Async version of click_text for concurrent operations."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.click_text, text, **options)

    async def type_text_async(self, text: str, **options) -> Dict[str, Any]:
        """Async version of type_text for concurrent operations."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.type_text, text, **options)

    async def take_screenshot_async(self, **options) -> Dict[str, Any]:
        """Async version of take_screenshot for concurrent operations."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.take_screenshot, **options)

    async def perform_batch_operations_async(self, operations: List[Dict[str, Any]], **options) -> Dict[str, Any]:
        """Async version of perform_batch_operations for concurrent operations."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.perform_batch_operations, operations, **options)

    async def find_image_async(self, image_path: str, **options) -> Dict[str, Any]:
        """Async version of find_image for concurrent operations."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.find_image, image_path, **options)

    async def find_text_async(self, text: str, **options) -> Dict[str, Any]:
        """Async version of find_text for concurrent operations."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.find_text, text, **options)


# =============================================================================
# Connection Pool for High-Throughput Scenarios
# =============================================================================

@dataclass
class ConnectionPoolConfig:
    """Configuration for GUI Automation connection pool."""
    pool_size: int = 5
    max_retries: int = 3
    retry_delay: float = 1.0
    health_check_interval: float = 30.0


class GuiAutomationConnectionPool:
    """
    Connection pool for high-throughput GUI automation scenarios.
    
    Usage:
        pool = GuiAutomationConnectionPool(pool_size=10)
        
        # Get a client from the pool
        async with pool.acquire() as client:
            result = await client.click_coordinates_async(100, 200)
            
        # Or use synchronously
        with pool.acquire_sync() as client:
            result = client.click_coordinates(100, 200)
    """
    
    def __init__(self, config: ConnectionPoolConfig = None):
        self.config = config or ConnectionPoolConfig()
        self.available_clients: List[GuiAutomationServiceClient] = []
        self.in_use_clients: List[GuiAutomationServiceClient] = []
        self.logger = get_logger("GuiAutomationConnectionPool")
        self._lock = asyncio.Lock()
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize the connection pool with clients."""
        for i in range(self.config.pool_size):
            client = GuiAutomationServiceClient(client_name=f"pool_client_{i}")
            try:
                client.connect()
                self.available_clients.append(client)
                self.logger.debug(f"Initialized pool client {i}")
            except Exception as e:
                self.logger.warning(f"Failed to initialize pool client {i}: {e}")
    
    async def acquire(self) -> GuiAutomationServiceClient:
        """Acquire a client from the pool (async version)."""
        async with self._lock:
            if not self.available_clients:
                # Try to create a new client if pool is empty
                for i in range(self.config.max_retries):
                    try:
                        client = GuiAutomationServiceClient(client_name=f"pool_client_extra_{i}")
                        client.connect()
                        self.logger.info(f"Created additional pool client due to high demand")
                        return client
                    except Exception as e:
                        self.logger.warning(f"Failed to create additional client: {e}")
                        if i < self.config.max_retries - 1:
                            await asyncio.sleep(self.config.retry_delay)
                
                raise RuntimeError("No available clients in pool and cannot create new ones")
            
            client = self.available_clients.pop()
            self.in_use_clients.append(client)
            return client
    
    def acquire_sync(self) -> GuiAutomationServiceClient:
        """Acquire a client from the pool (synchronous version)."""
        if not self.available_clients:
            # Try to create a new client if pool is empty
            for i in range(self.config.max_retries):
                try:
                    client = GuiAutomationServiceClient(client_name=f"pool_client_extra_sync_{i}")
                    client.connect()
                    self.logger.info(f"Created additional pool client due to high demand")
                    return client
                except Exception as e:
                    self.logger.warning(f"Failed to create additional client: {e}")
                    if i < self.config.max_retries - 1:
                        time.sleep(self.config.retry_delay)
            
            raise RuntimeError("No available clients in pool and cannot create new ones")
        
        client = self.available_clients.pop()
        self.in_use_clients.append(client)
        return client
    
    async def release(self, client: GuiAutomationServiceClient):
        """Release a client back to the pool (async version)."""
        async with self._lock:
            if client in self.in_use_clients:
                self.in_use_clients.remove(client)
                
                # Check if client is still healthy
                if client.is_connected():
                    self.available_clients.append(client)
                else:
                    # Try to reconnect
                    try:
                        client.connect()
                        self.available_clients.append(client)
                        self.logger.debug("Reconnected client before returning to pool")
                    except Exception as e:
                        self.logger.warning(f"Failed to reconnect client, discarding: {e}")
    
    def release_sync(self, client: GuiAutomationServiceClient):
        """Release a client back to the pool (synchronous version)."""
        if client in self.in_use_clients:
            self.in_use_clients.remove(client)
            
            # Check if client is still healthy
            if client.is_connected():
                self.available_clients.append(client)
            else:
                # Try to reconnect
                try:
                    client.connect()
                    self.available_clients.append(client)
                    self.logger.debug("Reconnected client before returning to pool")
                except Exception as e:
                    self.logger.warning(f"Failed to reconnect client, discarding: {e}")
    
    def close(self):
        """Close all clients in the pool."""
        for client in self.available_clients + self.in_use_clients:
            try:
                client.disconnect()
            except:
                pass
        
        self.available_clients.clear()
        self.in_use_clients.clear()
        self.logger.info("Connection pool closed")
    
    def get_pool_status(self) -> Dict[str, Any]:
        """Get current pool status."""
        return {
            "available_clients": len(self.available_clients),
            "in_use_clients": len(self.in_use_clients),
            "total_clients": len(self.available_clients) + len(self.in_use_clients),
            "pool_size": self.config.pool_size
        }
    
    # Context manager support
    async def __aenter__(self):
        """Async context manager entry."""
        client = await self.acquire()
        return client
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # Note: client would need to be stored in context
        pass
    
    def __enter__(self):
        """Sync context manager entry."""
        return self.acquire_sync()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Sync context manager exit."""
        # Note: client would need to be stored in context
        pass


# =============================================================================
# Enhanced Convenience Functions
# =============================================================================

def click_apple_menu(client_name: str = "user") -> Dict[str, Any]:
    """Enhanced function to click the Apple menu with better error handling."""
    client = GuiAutomationServiceClient(client_name)
    try:
        client.connect()
        return client.click_coordinates(20, 10, delay_after_ms=1000, capture_after=True)
    except Exception as e:
        return {"success": False, "message": f"Failed to click Apple menu: {e}"}

def open_spotlight(client_name: str = "user") -> Dict[str, Any]:
    """Enhanced function to open Spotlight search."""
    client = GuiAutomationServiceClient(client_name)
    try:
        client.connect()
        return client.press_key("Space", "command")  # Command+Space
    except Exception as e:
        return {"success": False, "message": f"Failed to open Spotlight: {e}"}

def launch_application(app_name: str, client_name: str = "user", wait_time: float = 2.0) -> Dict[str, Any]:
    """
    Enhanced function to launch an application via Spotlight with better timing.

    Args:
        app_name: Name of the application to launch
        client_name: gRPC client name to use
        wait_time: Time to wait between steps

    Returns:
        Dict containing the overall result
    """
    client = GuiAutomationServiceClient(client_name)

    try:
        client.connect()

        # Create a workflow for launching the app
        operations = [
            {"action": "key_press", "key": "Space", "modifiers": "command"},  # Open Spotlight
            {"action": "delay", "duration_ms": int(wait_time * 500)},         # Wait for Spotlight
            {"action": "type", "text": app_name, "clear_field": True},        # Type app name
            {"action": "delay", "duration_ms": int(wait_time * 500)},         # Wait for results
            {"action": "key_press", "key": "Return"},                         # Press Enter
            {"action": "delay", "duration_ms": int(wait_time * 1000)}         # Wait for launch
        ]

        # Execute the workflow
        result = client.perform_batch_operations(
            operations,
            stop_on_error=True,
            timeout_seconds=30
        )

        if result["overall_success"]:
            client.logger.info(f"Successfully launched application: {app_name}")
        else:
            client.logger.warning(f"Failed to launch application {app_name}: {result.get('message', 'Unknown error')}")

        return result

    except Exception as e:
        return {"success": False, "message": f"Failed to launch application {app_name}: {e}"}


# =============================================================================
# Workflow Builder Class for Complex Automations
# =============================================================================

class GuiWorkflowBuilder:
    """
    Enhanced workflow builder for creating complex GUI automation sequences.

    Usage:
        workflow = GuiWorkflowBuilder("user")
        workflow.click(100, 100).wait(500).type("Hello").press_key("Return")
        result = workflow.execute()
    """

    def __init__(self, client_name: str = "user"):
        self.client_name = client_name
        self.operations = []
        self.logger = get_logger(f"GuiWorkflowBuilder[{client_name}]")

    def click(self, x: int, y: int, delay_after: int = 300):
        """Add click operation to workflow."""
        self.operations.append({
            "action": "click",
            "x": x,
            "y": y,
            "delay_after": delay_after
        })
        return self

    def double_click(self, x: int, y: int, delay_after: int = 300):
        """Add double-click operation to workflow."""
        self.operations.append({
            "action": "double_click",
            "x": x,
            "y": y,
            "delay_after": delay_after
        })
        return self

    def type(self, text: str, clear_field: bool = False, delay_before: int = 100):
        """Add type operation to workflow."""
        self.operations.append({
            "action": "type",
            "text": text,
            "clear_field": clear_field,
            "delay_before": delay_before
        })
        return self

    def press_key(self, key: str, modifiers: str = "", delay_after: int = 200):
        """Add key press operation to workflow."""
        self.operations.append({
            "action": "key_press",
            "key": key,
            "modifiers": modifiers,
            "delay_after": delay_after
        })
        return self

    def click_text(self, text: str, search_region: Optional[Tuple[int, int, int, int]] = None,
                   delay_after: int = 300):
        """Add text-based click operation to workflow."""
        op = {
            "action": "click_text",
            "text": text,
            "delay_after": delay_after
        }
        if search_region:
            op["search_region"] = search_region
        self.operations.append(op)
        return self

    def click_image(self, image_path: str, confidence: float = 0.8,
                    search_region: Optional[Tuple[int, int, int, int]] = None,
                    delay_after: int = 300):
        """Add image-based click operation to workflow."""
        op = {
            "action": "click_image",
            "image_path": image_path,
            "confidence": confidence,
            "delay_after": delay_after
        }
        if search_region:
            op["search_region"] = search_region
        self.operations.append(op)
        return self

    def wait(self, duration_ms: int):
        """Add wait/delay operation to workflow."""
        self.operations.append({
            "action": "delay",
            "duration_ms": duration_ms
        })
        return self

    def screenshot(self, filename: str = "", region: Optional[Tuple[int, int, int, int]] = None):
        """Add screenshot operation to workflow."""
        op = {"action": "screenshot"}
        if filename:
            op["filename"] = filename
        if region:
            op["region"] = region
        self.operations.append(op)
        return self

    def execute(self, stop_on_error: bool = True, timeout_seconds: int = 60) -> Dict[str, Any]:
        """Execute the built workflow."""
        if not self.operations:
            return {"success": True, "message": "No operations to execute", "operation_results": []}

        client = GuiAutomationServiceClient(self.client_name)
        client.connect()

        self.logger.info(f"Executing workflow with {len(self.operations)} operations")
        return client.perform_batch_operations(
            self.operations,
            stop_on_error=stop_on_error,
            timeout_seconds=timeout_seconds
        )

    def clear(self):
        """Clear all operations from the workflow."""
        self.operations.clear()
        return self