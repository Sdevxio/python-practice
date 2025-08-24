from grpc_client_sdk.core.grpc_client_manager import GrpcClientManager
from grpc_client_sdk.services.apple_script_service_client import AppleScriptServiceClient


def test_run_applescript_service(setup):
    """
    Test the AppleScriptServiceClient gRPC client.
    This test verifies the connection to the gRPC server and the execution of a simple AppleScript command.
    It checks if the client is registered and connected, and if the AppleScript command executes successfully.

    :param setup: Fixture that sets up the gRPC server and client.
    """
    target = setup
    GrpcClientManager.register_clients(name="root", target=target)

    client = GrpcClientManager.get_client("root")
    assert client is not None, "Client should be registered and connected"

    script_client = AppleScriptServiceClient(client_name="root")
    script_client.connect()

    response = script_client.run_applescript(script='return "Hello from user"')
    assert response["success"]
    assert response["exit_code"] == 0
    assert "Hello from user" in response["stdout"]

def test_stream_applescript_service(setup):
    """
    Test the AppleScriptServiceClient gRPC client with streaming.
    This test verifies the connection to the gRPC server and the execution of a simple AppleScript command.
    It checks if the client is registered and connected, and if the AppleScript command executes successfully.

    :param setup: Fixture that sets up the gRPC server and client.
    """
    target = setup
    GrpcClientManager.register_clients(name="root", target=target)

    client = GrpcClientManager.get_client("root")
    assert client is not None, "Client should be registered and connected"

    script_client = AppleScriptServiceClient(client_name="root")
    script_client.connect()

    response = script_client.stream_applescript(script='return "Hello from user"')
    assert response is not None, "Response should not be None"

    # a generator response, you need to iterate over the generator and validate each yielded item.
    for item in response:
        assert "output" in item, "Response item should contain 'output'"
        assert "is_error" in item, "Response item should contain 'is_error'"
        assert "is_complete" in item, "Response item should contain 'is_complete'"
        assert "exit_code" in item, "Response item should contain 'exit_code'"
        assert not item["is_error"], "There should be no errors in the response"
        if item["is_complete"]:
            assert item["exit_code"] == 0, "Exit code should be 0 for successful execution"
