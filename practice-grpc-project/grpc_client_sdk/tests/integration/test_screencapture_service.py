import os

from grpc_client_sdk.core.grpc_client_manager import GrpcClientManager
from grpc_client_sdk.services.screen_capture_service_client import ScreenCaptureServiceClient
from test_framework.utils.handlers.artifacts.artifacts_handler import save_to_artifacts
from test_framework.utils.handlers.ocr.ocr_handler import extract_text_from_image


def test_capture_screenshot_only(setup):
    """
    Test the ScreenCaptureServiceClient for capturing screenshots.

    :param setup: Fixture that sets up the gRPC client and server.
    """
    # Register the client with the GrpcClientManager
    target = setup
    print(f"Connecting to gRPC server at {target}")
    GrpcClientManager.register_clients(name="root", target=target)
    # Get the registered client
    client = GrpcClientManager.get_client("root")
    assert client is not None, "Client should be registered and connected"

    # Create a ScreenCaptureServiceClient instance
    screen_capture_client = ScreenCaptureServiceClient("root")
    # Connect to the gRPC server
    screen_capture_client.connect()

    # Test if the client can capture a screenshot
    screenshot = screen_capture_client.capture_screenshot()

    assert screenshot and screenshot["success"], "Failed to capture screenshot"
    assert screenshot["image_data"], "No image data returned"

    # Save image data to local file
    local_path = save_to_artifacts(screenshot["image_data"], "full_screenshot.png", subfolder="screenshots")

    assert os.path.exists(local_path), f"File not saved at {local_path}"
    assert os.path.getsize(local_path) > 1000, "Saved screenshot is unexpectedly small"

    print(f"Screenshot saved: {local_path}")


def test_extract_text_from_screenshot(setup):
    """
    Test the ScreenCaptureServiceClient for extracting text from screenshots.

    :param setup: Fixture that sets up the gRPC client and server.
    """
    # Register the client with the GrpcClientManager
    target = setup
    GrpcClientManager.register_clients(name="root", target=target)
    # Get the registered client
    client = GrpcClientManager.get_client("root")
    assert client is not None, "Client should be registered and connected"

    # Create a ScreenCaptureServiceClient instance
    screen_capture_client = ScreenCaptureServiceClient("root")
    # Connect to the gRPC server
    screen_capture_client.connect()

    # Test if the client can capture a screenshot
    screenshot = screen_capture_client.capture_screenshot(
        capture_region=True,
        region_x=0,
        region_y=0,
        region_width=290,
        region_height=298,
    )

    assert screenshot and screenshot["success"], "Failed to capture screenshot"
    assert screenshot["image_data"], "No image data returned"

    # Save image data to local file
    local_path = save_to_artifacts(screenshot["image_data"], "ocr_test.png", subfolder="screenshots")

    assert os.path.exists(local_path), f"File not saved at {local_path}"
    assert os.path.getsize(local_path) > 1000, "Saved screenshot is unexpectedly small"

    # Extract text from the captured image data
    extracted_text = extract_text_from_image(local_path)
    print(f"Extracted text: {extracted_text}")
    assert extracted_text, "OCR extraction failed"
    assert "Edit" in extracted_text, "Expected text not found in OCR result"

