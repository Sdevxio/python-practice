from typing import Optional

from generated import screen_capture_service_pb2
from generated.screen_capture_service_pb2_grpc import ScreenCaptureServiceStub

from grpc_client_sdk.core.grpc_client_manager import GrpcClientManager
from test_framework.utils import get_logger


class ScreenCaptureServiceClient:
    """
    ScreenCaptureServiceClient is a gRPC client wrapper for the ScreenCaptureService
    exposed by the macOS user agent.

    Support operations:
    - Capture the entire screen or a specific region
    - Retrieve image bytes and/or saved file path
    - Extract text from screenshots using OCR (server-side)

    Attributes:
        client_name (str): Logical gRPC context ('user' by default).
        logger (Logger): Logger instance for structured output.
        stub (ScreenCaptureServiceStub): gRPC stub from compiled proto.

    Usage:
        client = ScreenCaptureServiceClient(client_name="user")
        client.connect()
        screenshot = client.capture_screenshot(capture_region=True, region_x=100, region_y=100)
        if screenshot:
            print(f"Screenshot saved at: {screenshot['file_path']}")
        else:
            print("Screenshot capture failed.")
    """

    def __init__(self, client_name: str = "user", logger: Optional[object] = None):
        """
        Initialize the ScreenCaptureServiceClient.
        This method sets up the client name and logger for structured output.
        It also initializes the gRPC stub for screen capture operations.

        :param client_name: Name of the gRPC client in GrpcClientManager.
        :param logger: Custom logger instance. If
        None, a default logger is created.
        """
        self.client_name = client_name
        self.logger = logger or get_logger(f"ScreenCaptureServiceClient[{client_name}]")
        self.stub: Optional[ScreenCaptureServiceStub] = None

    def connect(self) -> None:
        """
        Establishes the gRPC connection and stub for ScreenCaptureService.
        """
        self.stub = GrpcClientManager.get_stub(self.client_name, ScreenCaptureServiceStub)

    def capture_screenshot(
            self,
            capture_region: bool = False,
            region_x: int = 10,
            region_y: int = 10,
            region_width: int = 400,
            region_height: int = 400,
            save_path: Optional[str] = None
    ) -> Optional[dict]:
        """
        Captures a screenshot of the screen or a defined region.
        This method handles the streaming of image data from the server to the client.

        :param capture_region: If True, captures a specific region; otherwise, captures the entire screen.
        :param region_x: X-coordinate of the top-left corner of the capture region.
        :param region_y: Y-coordinate of the top-left corner of the capture region.
        :param region_width: Width of the capture region.
        :param region_height: Height of the capture region.
        :param save_path: Optional path to save the captured image on the macOS machine.

        :return:
        Optional[dict]: Dictionary with keys:
                - "success": bool
                - "image_data": bytes
                - "file_path": str (remote path on macOS)

        Example:
            client = ScreenCaptureServiceClient(client_name="user")
            client.connect()
            screenshot = client.capture_screenshot(capture_region=True, region_x=100, region_y=100)
            if screenshot:
                print(f"Screenshot saved at: {screenshot['file_path']}")
            else:
                print("Screenshot capture failed.")
        """
        if not self.stub:
            raise RuntimeError("ScreenCaptureServiceClient not connected.")

        try:
            request = screen_capture_service_pb2.ScreenshotRequest(
                capture_region=capture_region,
                region_x=region_x,
                region_y=region_y,
                region_width=region_width,
                region_height=region_height,
                save_path=save_path or ""
            )
            response = self.stub.CaptureScreenshot(request)

            if response.success:
                self.logger.info(f"Screenshot captured and saved at: {response.file_path}")
                return {
                    "success": True,
                    "image_data": response.image_data,
                    "file_path": response.file_path
                }
            else:
                self.logger.warning("Screenshot failed with unknown error.")
                return None

        except Exception as e:
            self.logger.error(f"Exception during screenshot capture: {e}")
            return None

    def extract_text_from_screenshot(
            self,
            image_data: Optional[bytes] = None,
            file_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Performs OCR to extract text from a screenshot.
        This method can accept either image data or a file path to the image.
        If both are provided, image_data will be used.
        Needs Tesseracts installed on the server.

        :param image_data: Raw image bytes (PNG).
        :param file_path: Path to image file on macOS.
        :return: Extracted text as a string, or None if extraction fails.

        Example:
            client = ScreenCaptureServiceClient(client_name="user")
            client.connect()
            extracted_text = client.extract_text(image_data=b'...')
            if extracted_text:
                print(f"Extracted text: {extracted_text}")
            else:
                print("OCR extraction failed.")
        """
        if not self.stub:
            raise RuntimeError("ScreenCaptureServiceClient not connected.")

        try:
            request = screen_capture_service_pb2.ExtractTextRequest(
                image_data=image_data or b"",
                file_path=file_path or ""
            )
            response = self.stub.ExtractText(request)

            if response.success:
                self.logger.info("OCR extraction successful.")
                return response.extracted_text
            else:
                self.logger.warning("OCR extraction failed.")
                return None

        except Exception as e:
            self.logger.error(f"Exception during OCR: {e}")
            return None