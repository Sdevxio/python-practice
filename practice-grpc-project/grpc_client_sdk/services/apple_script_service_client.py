from typing import Optional, Dict, Any, Generator

from generated import apple_script_service_pb2
from generated.apple_script_service_pb2_grpc import AppleScriptServiceStub

from grpc_client_sdk.core.grpc_client_manager import GrpcClientManager
from test_framework.utils import get_logger


class AppleScriptServiceClient:
    """
    AppleScriptServiceClient is a gRPC client wrapper for executing AppleScript and
    performing UI automation via macOS's user agent.

    Supported operations:
    - Direct AppleScript execution
    - Parameterized UI automation using enums
    - Streaming output for long-running AppleScript commands

    Typical use cases:
    - Executing AppleScript commands for UI automation
    - Performing UI actions like clicks, keystrokes, etc.
    - Streaming output for long-running scripts

    Attributes:
        client_name (str): gRPC context ("username" expected).
        logger (Logger): Logger instance for structured output.
        stub (AppleScriptServiceStub): gRPC stub to communicate with server.

    Usage:
        client = AppleScriptServiceClient(client_name="user/root") # "username" or "root" expected
        client.connect()
        result = client.run_applescript('return "Hello, World!"')
        if result["success"]:
            print(result["stdout"])  # Should print "Hello, World!"
    """

    def __init__(self, client_name: str = "user", logger: Optional[object] = None):
        """
        Initialize AppleScriptServiceClient.

        :param client_name: Name of the gRPC client in GrpcClientManager.
        :param logger: Custom logger instance. If None, a default logger is created.
        """
        self.client_name = client_name
        self.logger = logger or get_logger(f"AppleScriptServiceClient[{client_name}]")
        self.stub: Optional[AppleScriptServiceStub] = None

    def connect(self):
        """
        Establishes the gRPC connection and stub for AppleScriptService.
        """
        self.stub = GrpcClientManager.get_stub(self.client_name, AppleScriptServiceStub)

    def run_applescript(
            self,
            script: str,
            parameters: Optional[Dict[str, str]] = None,
            timeout_seconds: int = 10
    ) -> Optional[Dict[str, Any]]:
        """
        Executes AppleScript with optional parameters.
        This method allows for the execution of AppleScript commands, with the
        ability to substitute placeholders in the script with provided parameters.
        It also supports a timeout for the script execution.

        :param script: The AppleScript content to execute.
        :param parameters: Optional dictionary of parameters for placeholder substitution.
        :param timeout_seconds: Timeout for the script execution in seconds.
        :return: A dictionary containing the result of the script execution, including
                 stdout, stderr, exit code, etc. Returns None if the execution fails.

        Example:
        result = client.run_applescript('return "Hello, World!"')
        if result["success"]:
            print(result["stdout"])  # Should print "Hello, World!"
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() before executing scripts.")

        try:
            # Prepare the request
            request = apple_script_service_pb2.AppleScriptRequest(
                script=script,
                parameters=parameters or {},
                timeout_seconds=timeout_seconds
            )
            response: apple_script_service_pb2.AppleScriptResponse = self.stub.RunAppleScript(request)
            result = {
                "success": response.success,
                "stdout": response.stdout,
                "stderr": response.stderr,
                "exit_code": response.exit_code,
                "execution_time_ms": response.execution_time_ms
            }
            if not response.success and "osascript in not allowed assistive access" in response.stderr:
                self.logger.error("=== ACCESSIBILITY PERMISSION ERROR ===")
                self.logger.error("The gRPC server needs permission to control UI components.")
                self.logger.error(
                    "Add the server to System Preferences > Security & Privacy > Privacy > Accessibility.")
                self.logger.error("===================================")

                result["osascript_error"] = (
                    "Accessibility permission error: "
                    "osascript in not allowed assistive access. "
                    "Please check System Preferences > Security & Privacy > Privacy > Accessibility."
                )
            return result
        except Exception as e:
            self.logger.error(f"applescript execution failed: {str(e)}")
            return None

    def stream_applescript(
            self,
            script: str,
            parameters: Optional[Dict[str, str]] = None,
            timeout_seconds: int = 10
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Executes AppleScript and streams stdout/stderr in real time.
        This method allows for the execution of long-running AppleScript commands,
        providing real-time output streaming. It also supports parameter substitution
        and a timeout for the script execution.

        :param script: The AppleScript to run.
        :param parameters: Optional dictionary of parameters for placeholder substitution.
        :param timeout_seconds: Timeout for the script execution in seconds.
        :return: A generator yielding dictionaries with stdout/stderr/exit_code/etc.

        Example:
        for output in client.stream_applescript('return "Hello, World!"'):
            print(output['output'])  # Should print "Hello, World!" in real-time
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() before executing scripts.")

        try:
            request = apple_script_service_pb2.AppleScriptRequest(
                script=script,
                parameters=parameters or {},
                timeout_seconds=timeout_seconds
            )
            stream = self.stub.StreamAppleScript(request)

            for response in stream:
                yield {
                    "output": response.output,
                    "is_error": response.is_error,
                    "is_complete": response.is_complete,
                    "exit_code": response.exit_code
                }

        except Exception as e:
            self.logger.error(f"applescript streaming failed: {str(e)}")
            yield {
                "output": "",
                "is_error": True,
                "is_complete": True,
                "exit_code": -1
            }

    def perform_ui_action(
            self,
            action: apple_script_service_pb2.UiActions,
            script_template: str,
            parameters: Optional[Dict[str, str]] = None,
            timeout_seconds: int = 10
    ) -> Optional[Dict[str, Any]]:
        """
        Executes a UI action using AppleScript with optional parameters.
        This method allows for the execution of predefined UI actions, with the
        ability to substitute placeholders in the script with provided parameters.
        It also supports a timeout for the script execution.

        :param action: The UI action to perform (e.g., UiActions.CLICK).
        :param script_template: The AppleScript template to execute.
        :param parameters: Optional dictionary of parameters for placeholder substitution.
        :param timeout_seconds: Timeout for the script execution in seconds.
        :return: A dictionary containing the result of the script execution, including
                 stdout, stderr, exit code, etc. Returns None if the execution fails.

        Example:
        result = client.perform_ui_action(
            action=apple_script_service_pb2.UiActions.CLICK,
            script_template='tell application "System Events" to click button "OK" of window "Alert"',
            parameters={"window_name": "Alert"}
        )
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() before executing scripts.")

        try:
            param_dict = parameters or {}
            param_dict["SCRIPT"] = script_template

            request = apple_script_service_pb2.UiActionsRequest(
                actions=action,
                parameters=param_dict,
                timeout_seconds=timeout_seconds
            )
            response: apple_script_service_pb2.UiActionsResponse = self.stub.PerformUiAction(request)

            return {
                "success": response.success,
                "stdout": response.stdout,
                "stderr": response.stderr,
                "exit_code": response.exit_code,
                "execution_time_ms": response.execution_time_ms
            }
        except Exception as e:
            self.logger.error(f"perform_ui_action failed: {str(e)}")
            return None