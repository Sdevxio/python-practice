"""
Fat Client Web Automation Service - Hybrid Python/JavaScript Architecture

This client implements the "thin server, fat client" pattern where:
- Server: Only 3 methods (ExecuteScript, TakeScreenshot, GetPageInfo)  
- Client: Rich Python API that generates optimized JavaScript/AppleScript

Benefits:
Server stability - Rarely needs changes
Client flexibility - Easy to add new automation methods
Native performance - JavaScript runs directly in browser
Python convenience - All logic stays in familiar Python
Easy extension - Add methods without touching server
"""

import json
import time
import tempfile
from typing import Dict, Any, Optional, List, Union, Tuple
from pathlib import Path

from grpc_client_sdk.core.grpc_client_manager import GrpcClientManager
from test_framework.utils import get_logger

# Import protobuf modules with fallback
try:
    from generated import web_automation_service_pb2, web_automation_service_pb2_grpc
    PROTOBUF_AVAILABLE = True
except ImportError:
    PROTOBUF_AVAILABLE = False


class WebAutomationClient:
    """
    Fat Client for Web Automation using Hybrid Python/JavaScript Architecture
    
    This client provides a rich Python API that generates optimized JavaScript,
    AppleScript, or shell commands executed by the thin server.
    
    All browser automation is implemented as JavaScript generation, making it:
    - Fast (native browser execution)
    - Stable (server rarely changes) 
    - Flexible (easy to extend)
    - Pythonic (familiar syntax)
    
    Usage:
        client = WebAutomationClient("user")
        client.connect()
        
        # High-level Python methods
        client.navigate_to_url("https://google.com")
        client.wait_for_element("#search-box", timeout=10)
        client.type_text("#search-box", "Python automation")
        client.click_element("button[type='submit']")
        
        # All of this generates optimized JavaScript under the hood
    """

    def __init__(self, client_name: str = "user", logger: Optional[object] = None):
        self.client_name = client_name
        self.logger = logger or get_logger(f"WebAutomationClient[{client_name}]")
        self.stub = None
        self._connected = False

    def connect(self) -> None:
        """Establish connection to the Web Automation gRPC service"""
        try:
            if PROTOBUF_AVAILABLE:
                self.stub = GrpcClientManager.get_stub(
                    self.client_name,
                    web_automation_service_pb2_grpc.WebAutomationServiceStub
                )
                self.logger.info(f"Web Automation Service connected for client '{self.client_name}'")
                self._connected = True
            else:
                raise RuntimeError("Web Automation protobuf modules not available")
        except Exception as e:
            self.logger.error(f"Failed to connect Web Automation Service: {e}")
            raise RuntimeError(f"Web Automation Service connection failed: {e}")

    def is_connected(self) -> bool:
        """Check if the service is connected"""
        return self._connected and self.stub is not None

    def _ensure_connected(self):
        """Ensure connection, attempt reconnect if needed"""
        if not self.is_connected():
            self.logger.warning("Web Automation Service not connected, attempting to reconnect...")
            self.connect()

    # =============================================================================
    # Core Low-Level Methods (Direct Server Communication)
    # =============================================================================

    def execute_script(self, script: str, target_user: str = "", timeout_ms: int = 30000,
                      return_value: bool = True) -> Dict[str, Any]:
        """
        Execute JavaScript, AppleScript, or shell script on the server
        
        Args:
            script: Script code to execute
            target_user: Target user for agent routing
            timeout_ms: Timeout in milliseconds
            return_value: Whether to return the script result
            
        Returns:
            Dict with success, message, result_value, execution_time_ms, console_output
        """
        self._ensure_connected()

        try:
            request = web_automation_service_pb2.ScriptRequest(
                script=script,
                target_user=target_user,
                timeout_ms=timeout_ms,
                return_value=return_value
            )

            response = self.stub.ExecuteScript(request)

            result = {
                "success": response.success,
                "message": response.message,
                "result_value": response.result_value,
                "execution_time_ms": response.execution_time_ms,
                "console_output": list(response.console_output),
                "metadata": dict(response.metadata)
            }

            if response.success:
                self.logger.debug(f"Script executed successfully in {response.execution_time_ms}ms")
            else:
                self.logger.warning(f"Script execution failed: {response.message}")

            return result

        except Exception as e:
            self.logger.error(f"Execute script failed: {e}")
            return {
                "success": False,
                "message": str(e),
                "result_value": "",
                "execution_time_ms": 0,
                "console_output": [],
                "metadata": {}
            }

    def take_screenshot(self, target_user: str = "", region: Optional[Tuple[int, int, int, int]] = None,
                       format: str = "png", save_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Take screenshot using the server
        
        Args:
            target_user: Target user for agent routing
            region: Optional region (x, y, width, height)
            format: Image format (png, jpeg)
            save_path: Optional path to save screenshot
            
        Returns:
            Dict with success, message, image_data, width, height, file_path (if saved)
        """
        self._ensure_connected()

        try:
            request = web_automation_service_pb2.ScreenshotRequest(
                target_user=target_user,
                format=format
            )

            if region:
                request.region.x, request.region.y = region[0], region[1]
                request.region.width, request.region.height = region[2], region[3]

            response = self.stub.TakeScreenshot(request)

            result = {
                "success": response.success,
                "message": response.message,
                "image_data": response.image_data,
                "width": response.width,
                "height": response.height,
                "format": response.format,
                "file_size": response.file_size,
                "timestamp": response.timestamp,
                "execution_time_ms": response.execution_time_ms
            }

            # Save to file if requested
            if response.success and save_path and response.image_data:
                save_path = Path(save_path)
                save_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(save_path, 'wb') as f:
                    f.write(response.image_data)
                
                result["file_path"] = str(save_path)
                self.logger.info(f"Screenshot saved to: {save_path}")

            return result

        except Exception as e:
            self.logger.error(f"Take screenshot failed: {e}")
            return {
                "success": False,
                "message": str(e),
                "image_data": b"",
                "width": 0,
                "height": 0,
                "execution_time_ms": 0
            }

    def get_page_info(self, info_types: Optional[List[str]] = None, 
                      target_user: str = "") -> Dict[str, Any]:
        """
        Get page/system information from server
        
        Args:
            info_types: List of info types to retrieve
            target_user: Target user for agent routing
            
        Returns:
            Dict with success, message, page_info, structured_data
        """
        self._ensure_connected()

        try:
            request = web_automation_service_pb2.PageInfoRequest(
                target_user=target_user
            )

            # Map string info types to protobuf enum values
            if info_types:
                type_mapping = {
                    "url": web_automation_service_pb2.URL,
                    "title": web_automation_service_pb2.TITLE,
                    "user_agent": web_automation_service_pb2.USER_AGENT,
                    "viewport_size": web_automation_service_pb2.VIEWPORT_SIZE,
                    "scroll_position": web_automation_service_pb2.SCROLL_POSITION,
                    "performance_metrics": web_automation_service_pb2.PERFORMANCE_METRICS
                }
                
                for info_type in info_types:
                    if info_type in type_mapping:
                        request.info_types.append(type_mapping[info_type])

            response = self.stub.GetPageInfo(request)

            result = {
                "success": response.success,
                "message": response.message,
                "page_info": dict(response.page_info),
                "structured_data": {},
                "execution_time_ms": response.execution_time_ms
            }

            # Process structured data
            for key, data in response.structured_data.items():
                try:
                    result["structured_data"][key] = json.loads(data.json_data)
                except:
                    result["structured_data"][key] = data.json_data

            return result

        except Exception as e:
            self.logger.error(f"Get page info failed: {e}")
            return {
                "success": False,
                "message": str(e),
                "page_info": {},
                "structured_data": {},
                "execution_time_ms": 0
            }

    # =============================================================================
    # High-Level Browser Automation (JavaScript Generation)
    # =============================================================================

    def navigate_to_url(self, url: str) -> Dict[str, Any]:
        """Navigate to a URL by generating JavaScript"""
        script = f"window.location.href = '{url}';"
        return self.execute_script(script)

    def click_element(self, selector: str, wait_timeout: int = 5000) -> Dict[str, Any]:
        """Click an element by generating JavaScript with wait logic"""
        script = f"""
        (function() {{
            const startTime = Date.now();
            const timeout = {wait_timeout};
            
            function tryClick() {{
                const element = document.querySelector('{selector}');
                if (element) {{
                    element.click();
                    return {{success: true, message: 'Element clicked successfully'}};
                }} else if (Date.now() - startTime < timeout) {{
                    setTimeout(tryClick, 100);
                    return null;
                }} else {{
                    return {{success: false, message: 'Element not found within timeout'}};
                }}
            }}
            
            return tryClick();
        }})();
        """
        return self.execute_script(script)

    def type_text(self, selector: str, text: str, clear_first: bool = True) -> Dict[str, Any]:
        """Type text into an element by generating JavaScript"""
        clear_script = "element.value = '';" if clear_first else ""
        
        script = f"""
        (function() {{
            const element = document.querySelector('{selector}');
            if (element) {{
                element.focus();
                {clear_script}
                element.value = '{text}';
                
                // Trigger input events
                element.dispatchEvent(new Event('input', {{bubbles: true}}));
                element.dispatchEvent(new Event('change', {{bubbles: true}}));
                
                return {{success: true, message: 'Text typed successfully'}};
            }} else {{
                return {{success: false, message: 'Element not found'}};
            }}
        }})();
        """
        return self.execute_script(script)

    def wait_for_element(self, selector: str, timeout: int = 10000) -> Dict[str, Any]:
        """Wait for an element to appear by generating JavaScript"""
        script = f"""
        (function() {{
            return new Promise((resolve) => {{
                const startTime = Date.now();
                const timeout = {timeout};
                
                function check() {{
                    const element = document.querySelector('{selector}');
                    if (element) {{
                        resolve({{success: true, message: 'Element found'}});
                    }} else if (Date.now() - startTime < timeout) {{
                        setTimeout(check, 100);
                    }} else {{
                        resolve({{success: false, message: 'Element not found within timeout'}});
                    }}
                }}
                
                check();
            }});
        }})();
        """
        return self.execute_script(script)

    def get_element_text(self, selector: str) -> Dict[str, Any]:
        """Get text content of an element"""
        script = f"""
        (function() {{
            const element = document.querySelector('{selector}');
            if (element) {{
                return {{
                    success: true, 
                    text: element.textContent || element.innerText,
                    message: 'Text retrieved successfully'
                }};
            }} else {{
                return {{success: false, message: 'Element not found'}};
            }}
        }})();
        """
        return self.execute_script(script)

    def scroll_to_element(self, selector: str) -> Dict[str, Any]:
        """Scroll to an element"""
        script = f"""
        (function() {{
            const element = document.querySelector('{selector}');
            if (element) {{
                element.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                return {{success: true, message: 'Scrolled to element'}};
            }} else {{
                return {{success: false, message: 'Element not found'}};
            }}
        }})();
        """
        return self.execute_script(script)

    def wait_for_page_load(self) -> Dict[str, Any]:
        """Wait for page to finish loading"""
        script = """
        (function() {
            if (document.readyState === 'complete') {
                return {success: true, message: 'Page already loaded'};
            }
            
            return new Promise((resolve) => {
                window.addEventListener('load', () => {
                    resolve({success: true, message: 'Page loaded successfully'});
                });
                
                // Timeout after 30 seconds
                setTimeout(() => {
                    resolve({success: false, message: 'Page load timeout'});
                }, 30000);
            });
        })();
        """
        return self.execute_script(script)

    # =============================================================================
    # High-Level macOS Automation (AppleScript Generation)
    # =============================================================================

    def click_coordinates_macos(self, x: int, y: int, click_type: str = "single") -> Dict[str, Any]:
        """Click at coordinates on macOS using AppleScript"""
        click_commands = {
            "single": f"click at {{{x}, {y}}}",
            "double": f"double click at {{{x}, {y}}}",
            "right": f"right click at {{{x}, {y}}}"
        }
        
        command = click_commands.get(click_type, click_commands["single"])
        script = f'tell application "System Events" to {command}'
        
        return self.execute_script(script)

    def type_text_macos(self, text: str) -> Dict[str, Any]:
        """Type text on macOS using AppleScript"""
        # Escape quotes in the text
        escaped_text = text.replace('"', '\\"')
        script = f'tell application "System Events" to keystroke "{escaped_text}"'
        
        return self.execute_script(script)

    def press_key_macos(self, key_code: str, modifiers: str = "") -> Dict[str, Any]:
        """Press key combination on macOS using AppleScript"""
        if modifiers:
            script = f'tell application "System Events" to key code {key_code} using {{{modifiers}}}'
        else:
            script = f'tell application "System Events" to key code {key_code}'
            
        return self.execute_script(script)

    def open_application_macos(self, app_name: str) -> Dict[str, Any]:
        """Open an application on macOS using AppleScript"""
        script = f'tell application "{app_name}" to activate'
        return self.execute_script(script)

    def get_window_info_macos(self, app_name: str) -> Dict[str, Any]:
        """Get window information for an app on macOS"""
        script = f"""
        tell application "System Events"
            tell application process "{app_name}"
                try
                    set frontWindow to front window
                    set windowTitle to title of frontWindow
                    set windowPosition to position of frontWindow
                    set windowSize to size of frontWindow
                    
                    return "{{" & ¬
                        "\\"title\\": \\"" & windowTitle & "\\", " & ¬
                        "\\"x\\": " & (item 1 of windowPosition) & ", " & ¬
                        "\\"y\\": " & (item 2 of windowPosition) & ", " & ¬
                        "\\"width\\": " & (item 1 of windowSize) & ", " & ¬
                        "\\"height\\": " & (item 2 of windowSize) & ¬
                        "}}"
                on error
                    return "{{\\"error\\": \\"Could not get window info\\"}}"
                end try
            end tell
        end tell
        """
        return self.execute_script(script)

    # =============================================================================
    # High-Level System Operations (Shell Command Generation)
    # =============================================================================

    def list_files(self, directory: str = ".") -> Dict[str, Any]:
        """List files in a directory using shell command"""
        script = f"ls -la '{directory}'"
        return self.execute_script(script)

    def get_system_info(self) -> Dict[str, Any]:
        """Get system information using shell commands"""
        script = "uname -a && sw_vers && whoami && hostname"
        return self.execute_script(script)

    def check_process(self, process_name: str) -> Dict[str, Any]:
        """Check if a process is running"""
        script = f"ps aux | grep '{process_name}' | grep -v grep"
        return self.execute_script(script)

    # =============================================================================
    # Workflow and Batch Operations
    # =============================================================================

    def execute_workflow(self, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute a sequence of operations as a workflow"""
        results = []
        overall_success = True
        
        for i, operation in enumerate(operations):
            try:
                action = operation.get("action")
                result = None
                
                if action == "navigate":
                    result = self.navigate_to_url(operation["url"])
                elif action == "click":
                    result = self.click_element(operation["selector"])
                elif action == "type":
                    result = self.type_text(operation["selector"], operation["text"])
                elif action == "wait":
                    result = self.wait_for_element(operation["selector"], operation.get("timeout", 10000))
                elif action == "screenshot":
                    result = self.take_screenshot(save_path=operation.get("save_path"))
                elif action == "script":
                    result = self.execute_script(operation["script"])
                elif action == "click_coords":
                    result = self.click_coordinates_macos(operation["x"], operation["y"])
                else:
                    result = {"success": False, "message": f"Unknown action: {action}"}
                
                results.append(result)
                
                if not result.get("success"):
                    overall_success = False
                    if operation.get("stop_on_error", True):
                        break
                        
                # Add delay if specified
                if operation.get("delay_after"):
                    time.sleep(operation["delay_after"] / 1000.0)
                    
            except Exception as e:
                result = {"success": False, "message": str(e)}
                results.append(result)
                overall_success = False
                
                if operation.get("stop_on_error", True):
                    break
        
        return {
            "overall_success": overall_success,
            "operation_count": len(operations),
            "successful_operations": sum(1 for r in results if r.get("success")),
            "failed_operations": sum(1 for r in results if not r.get("success")),
            "operation_results": results
        }

    # =============================================================================
    # Context Manager Support
    # =============================================================================

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()

    def disconnect(self):
        """Disconnect from the service"""
        self._connected = False
        self.stub = None
        self.logger.info(f"Web Automation Service disconnected for client '{self.client_name}'")


# =============================================================================
# Convenience Functions and Workflow Builders
# =============================================================================

def google_search(query: str, client_name: str = "user") -> Dict[str, Any]:
    """Perform a Google search workflow"""
    with WebAutomationClient(client_name) as client:
        workflow = [
            {"action": "navigate", "url": "https://google.com"},
            {"action": "wait", "selector": "input[name='q']", "timeout": 5000},
            {"action": "type", "selector": "input[name='q']", "text": query},
            {"action": "click", "selector": "input[value='Google Search']"},
            {"action": "wait", "selector": "#search", "timeout": 10000},
            {"action": "screenshot", "save_path": f"/tmp/google_search_{int(time.time())}.png"}
        ]
        
        return client.execute_workflow(workflow)


def automate_form_fill(form_data: Dict[str, str], submit: bool = True, 
                      client_name: str = "user") -> Dict[str, Any]:
    """Fill out a form with provided data"""
    with WebAutomationClient(client_name) as client:
        operations = []
        
        # Fill each form field
        for selector, value in form_data.items():
            operations.extend([
                {"action": "wait", "selector": selector, "timeout": 5000},
                {"action": "type", "selector": selector, "text": value}
            ])
        
        # Submit if requested
        if submit:
            operations.append({"action": "click", "selector": "input[type='submit'], button[type='submit']"})
        
        return client.execute_workflow(operations)


class WebWorkflowBuilder:
    """Builder pattern for creating web automation workflows"""
    
    def __init__(self, client_name: str = "user"):
        self.client_name = client_name
        self.operations = []
    
    def navigate(self, url: str):
        """Add navigation operation"""
        self.operations.append({"action": "navigate", "url": url})
        return self
    
    def click(self, selector: str):
        """Add click operation"""
        self.operations.append({"action": "click", "selector": selector})
        return self
    
    def type(self, selector: str, text: str):
        """Add type operation"""
        self.operations.append({"action": "type", "selector": selector, "text": text})
        return self
    
    def wait(self, selector: str, timeout: int = 10000):
        """Add wait operation"""
        self.operations.append({"action": "wait", "selector": selector, "timeout": timeout})
        return self
    
    def screenshot(self, save_path: str = None):
        """Add screenshot operation"""
        self.operations.append({"action": "screenshot", "save_path": save_path})
        return self
    
    def script(self, script: str):
        """Add custom script operation"""
        self.operations.append({"action": "script", "script": script})
        return self
    
    def delay(self, ms: int):
        """Add delay operation"""
        self.operations.append({"action": "delay", "delay_after": ms})
        return self
    
    def execute(self) -> Dict[str, Any]:
        """Execute the built workflow"""
        with WebAutomationClient(self.client_name) as client:
            return client.execute_workflow(self.operations)
    
    def clear(self):
        """Clear all operations"""
        self.operations.clear()
        return self