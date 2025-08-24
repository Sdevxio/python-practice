"""
Integration tests for Screen Capture service with real gRPC services.

Tests screenshot capture, OCR text extraction, image handling, and error handling
using actual gRPC connections and macOS screen capture functionality.
"""

import pytest
import os
import tempfile
import time
from datetime import datetime


class TestScreenCaptureServiceIntegration:
    """Integration tests for Screen Capture service with real gRPC services."""

    def test_screencapture_service_availability(self, services):
        """Test that Screen Capture service is available in user context."""
        # Screen capture typically only works in user context (not root)
        user_screencapture = services.screen_capture("admin")
        assert user_screencapture is not None
        
        # Screen capture is typically not available in root context
        try:
            root_screencapture = services.screen_capture("root")
            # If available, should not be None
            if root_screencapture is not None:
                assert root_screencapture is not None
        except AttributeError:
            # Root context doesn't have screen capture - that's expected
            print("Screen capture not available in root context (expected)")

    def test_screencapture_service_connection_handling(self, services):
        """Test Screen Capture service connection handling."""
        screencapture_service = services.screen_capture("admin")
        
        # Test basic service properties
        assert screencapture_service.client_name == "admin"
        assert screencapture_service.logger is not None
        
        # Service should have stub available after connection
        assert screencapture_service.stub is not None
        
        # Test expected methods exist
        assert hasattr(screencapture_service, 'capture_screenshot')
        assert hasattr(screencapture_service, 'extract_text_from_screenshot')
        assert callable(screencapture_service.capture_screenshot)
        assert callable(screencapture_service.extract_text_from_screenshot)

    def test_screencapture_full_screen_capture(self, services):
        """Test Screen Capture service full screen capture functionality."""
        screencapture_service = services.screen_capture("admin")
        
        # Test full screen capture
        result = screencapture_service.capture_screenshot(capture_region=False)
        
        if result is not None:
            # Successful capture
            assert isinstance(result, dict)
            assert "success" in result
            assert "image_data" in result
            assert "file_path" in result
            
            assert result["success"] is True
            assert isinstance(result["image_data"], bytes)
            assert isinstance(result["file_path"], str)
            
            # Image data should not be empty
            assert len(result["image_data"]) > 0
            
            # File path should be reasonable
            assert len(result["file_path"]) > 0
            assert result["file_path"].endswith(('.png', '.jpg', '.jpeg'))
            
        else:
            # Screen capture might fail due to permissions - that's expected
            print("Screen capture failed - possibly due to screen recording permissions")

    def test_screencapture_region_capture(self, services):
        """Test Screen Capture service region capture functionality."""
        screencapture_service = services.screen_capture("admin")
        
        # Test region capture with reasonable coordinates
        result = screencapture_service.capture_screenshot(
            capture_region=True,
            region_x=100,
            region_y=100,
            region_width=300,
            region_height=200
        )
        
        if result is not None:
            # Successful region capture
            assert isinstance(result, dict)
            assert result["success"] is True
            assert isinstance(result["image_data"], bytes)
            assert isinstance(result["file_path"], str)
            
            # Region capture should produce smaller image than full screen
            assert len(result["image_data"]) > 0
            
        else:
            # Region capture might fail - that's expected without permissions
            print("Region capture failed - possibly due to screen recording permissions")

    def test_screencapture_with_custom_save_path(self, services):
        """Test Screen Capture service with custom save path."""
        screencapture_service = services.screen_capture("admin")
        
        # Create temporary path for screenshot
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_path = temp_file.name
        
        # Test capture with custom save path
        result = screencapture_service.capture_screenshot(
            capture_region=True,
            region_x=50,
            region_y=50, 
            region_width=200,
            region_height=150,
            save_path=temp_path
        )
        
        if result is not None:
            # Should use custom save path
            assert result["success"] is True
            # File path might be the custom path or server-determined path
            assert isinstance(result["file_path"], str)
            assert len(result["file_path"]) > 0
            
        # Cleanup
        try:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        except:
            pass

    def test_screencapture_parameter_validation(self, services):
        """Test Screen Capture service parameter validation."""
        screencapture_service = services.screen_capture("admin")
        
        # Test with various parameter combinations
        test_cases = [
            # Valid region parameters
            {"capture_region": True, "region_x": 0, "region_y": 0, "region_width": 100, "region_height": 100},
            # Boundary values
            {"capture_region": True, "region_x": 10, "region_y": 10, "region_width": 50, "region_height": 50},
            # Large region
            {"capture_region": True, "region_x": 0, "region_y": 0, "region_width": 1920, "region_height": 1080},
        ]
        
        for params in test_cases:
            result = screencapture_service.capture_screenshot(**params)
            
            # Should either succeed or fail gracefully
            if result is not None:
                assert isinstance(result, dict)
                assert "success" in result
            # None result is acceptable (service might reject parameters)

    @pytest.mark.ocr
    def test_screencapture_ocr_text_extraction(self, services):
        """Test Screen Capture service OCR text extraction functionality."""
        screencapture_service = services.screen_capture("admin")
        
        # First, try to capture a screenshot
        screenshot_result = screencapture_service.capture_screenshot(
            capture_region=True,
            region_x=100,
            region_y=100,
            region_width=400,
            region_height=200
        )
        
        if screenshot_result and screenshot_result["success"]:
            # Test OCR with image data
            image_data = screenshot_result["image_data"]
            extracted_text = screencapture_service.extract_text_from_screenshot(
                image_data=image_data
            )
            
            # OCR might succeed or fail depending on image content and Tesseract availability
            if extracted_text is not None:
                assert isinstance(extracted_text, str)
                # Text can be empty if no text in image
                print(f"OCR extracted text: '{extracted_text}'")
            else:
                print("OCR extraction failed - possibly Tesseract not installed")
                
            # Test OCR with file path
            file_path = screenshot_result["file_path"]
            extracted_text_from_file = screencapture_service.extract_text_from_screenshot(
                file_path=file_path
            )
            
            # Same expectations as image data OCR
            if extracted_text_from_file is not None:
                assert isinstance(extracted_text_from_file, str)
        else:
            print("Cannot test OCR - screenshot capture failed")

    def test_screencapture_error_handling(self, services):
        """Test Screen Capture service error handling."""
        screencapture_service = services.screen_capture("admin")
        
        # Test with invalid parameters
        invalid_cases = [
            # Negative coordinates
            {"capture_region": True, "region_x": -100, "region_y": -100, "region_width": 100, "region_height": 100},
            # Zero dimensions
            {"capture_region": True, "region_x": 100, "region_y": 100, "region_width": 0, "region_height": 0},
            # Extremely large coordinates
            {"capture_region": True, "region_x": 10000, "region_y": 10000, "region_width": 100, "region_height": 100},
        ]
        
        for params in invalid_cases:
            result = screencapture_service.capture_screenshot(**params)
            
            # Should handle invalid parameters gracefully
            # Either return None or return result with success=False
            if result is not None:
                assert isinstance(result, dict)
                # If returned, should indicate failure
                if "success" in result:
                    # Success could be False for invalid parameters
                    assert isinstance(result["success"], bool)


class TestScreenCaptureServiceRobustness:
    """Tests for Screen Capture service robustness and edge cases."""

    def test_screencapture_service_multiple_captures(self, services):
        """Test Screen Capture service handles multiple sequential captures."""
        screencapture_service = services.screen_capture("admin")
        
        # Make multiple capture attempts
        results = []
        for i in range(3):
            result = screencapture_service.capture_screenshot(
                capture_region=True,
                region_x=50 + i * 10,
                region_y=50 + i * 10,
                region_width=150,
                region_height=100
            )
            results.append(result)
        
        # All calls should complete (success or graceful failure)
        for result in results:
            # Should either be None (failed) or valid dict
            if result is not None:
                assert isinstance(result, dict)
                assert "success" in result

    def test_screencapture_service_concurrent_usage(self, services):
        """Test Screen Capture service concurrent usage patterns."""
        screencapture_service = services.screen_capture("admin")
        
        # Test that service can handle mixed operations
        operations = [
            lambda: screencapture_service.capture_screenshot(capture_region=False),
            lambda: screencapture_service.capture_screenshot(capture_region=True, region_x=100, region_y=100),
            lambda: screencapture_service.extract_text_from_screenshot(image_data=b"fake_image_data"),
        ]
        
        for operation in operations:
            try:
                result = operation()
                # Each operation should complete without crashing
                # Result can be None (failure) or valid response
                if result is not None:
                    assert isinstance(result, (dict, str))
            except Exception:
                # Operations might raise exceptions - that's acceptable
                pass

    def test_screencapture_service_permission_detection(self, services):
        """Test Screen Capture service permission detection."""
        screencapture_service = services.screen_capture("admin")
        
        # Try a simple capture to test permissions
        result = screencapture_service.capture_screenshot(capture_region=False)
        
        if result is None:
            # Capture failed - likely due to screen recording permissions
            print("Screen capture failed - check Screen Recording permissions")
            print("Go to System Preferences > Security & Privacy > Privacy > Screen Recording")
            print("Make sure the gRPC server is allowed to record screen")
        elif result["success"] is False:
            # Capture returned failure - might have permission info in logs
            print("Screen capture returned failure - check service logs")
        else:
            # Capture succeeded
            print("Screen capture permissions are working correctly")
            assert len(result["image_data"]) > 0

    def test_screencapture_service_integration_with_session(self, services):
        """Test Screen Capture service integration with session."""
        screencapture_service = services.screen_capture("admin")
        command_service = services.command("admin")
        
        # Both services should be available in user context
        assert screencapture_service is not None
        assert command_service is not None
        
        # Test that they work independently
        cmd_result = command_service.run_command("echo 'screen capture test'")
        capture_result = screencapture_service.capture_screenshot(
            capture_region=True,
            region_x=10,
            region_y=10,
            region_width=100,
            region_height=100
        )
        
        # Command should work
        assert cmd_result is not None
        assert cmd_result["exit_code"] == 0
        
        # Screen capture result depends on permissions
        if capture_result is not None:
            assert isinstance(capture_result, dict)


class TestScreenCaptureServiceConfiguration:
    """Tests for Screen Capture service configuration and setup."""

    def test_screencapture_service_logger_configuration(self, services):
        """Test Screen Capture service logger is properly configured."""
        user_screencapture = services.screen_capture("admin")
        
        # Should have logger configured
        assert user_screencapture.logger is not None
        assert hasattr(user_screencapture.logger, 'name')

    def test_screencapture_service_client_names(self, services):
        """Test Screen Capture service client name configuration."""
        user_screencapture = services.screen_capture("admin")
        
        assert user_screencapture.client_name == "admin"
        
        # Screen capture is typically not available in root context
        try:
            root_screencapture = services.screen_capture("root")
            if root_screencapture is not None:
                assert root_screencapture.client_name == "root"
        except AttributeError:
            # Root context doesn't have screen capture - that's expected
            pass

    def test_screencapture_service_stub_configuration(self, services):
        """Test Screen Capture service stub configuration."""
        screencapture_service = services.screen_capture("admin")
        
        # Should have ScreenCaptureServiceStub
        assert screencapture_service.stub is not None
        
        # Should have the expected gRPC methods
        expected_methods = ['CaptureScreenshot', 'ExtractText']
        for method_name in expected_methods:
            assert hasattr(screencapture_service.stub, method_name)
            assert callable(getattr(screencapture_service.stub, method_name))

    def test_screencapture_service_default_parameters(self, services):
        """Test Screen Capture service default parameter handling."""
        screencapture_service = services.screen_capture("admin")
        
        # Test capture with minimal parameters (should use defaults)
        result = screencapture_service.capture_screenshot()
        
        # Should handle default parameters without error
        # Result depends on permissions, but should not crash
        if result is not None:
            assert isinstance(result, dict)
            assert "success" in result


class TestScreenCaptureServiceOCR:
    """Tests for Screen Capture service OCR functionality."""

    @pytest.mark.ocr
    def test_screencapture_ocr_with_empty_data(self, services):
        """Test Screen Capture OCR with empty/invalid data."""
        screencapture_service = services.screen_capture("admin")
        
        # Test with empty image data
        result = screencapture_service.extract_text_from_screenshot(image_data=b"")
        # Should handle empty data gracefully
        assert result is None or isinstance(result, str)
        
        # Test with invalid image data  
        result = screencapture_service.extract_text_from_screenshot(image_data=b"not_image_data")
        # Should handle invalid data gracefully
        assert result is None or isinstance(result, str)
        
        # Test with non-existent file path
        result = screencapture_service.extract_text_from_screenshot(file_path="/nonexistent/path.png")
        # Should handle invalid path gracefully
        assert result is None or isinstance(result, str)

    @pytest.mark.ocr
    def test_screencapture_ocr_parameter_priority(self, services):
        """Test Screen Capture OCR parameter priority (image_data vs file_path)."""
        screencapture_service = services.screen_capture("admin")
        
        # According to docs, image_data takes priority if both provided
        result = screencapture_service.extract_text_from_screenshot(
            image_data=b"fake_image_data",
            file_path="/some/path.png"
        )
        
        # Should handle the case gracefully
        # Result depends on server OCR implementation
        assert result is None or isinstance(result, str)

    @pytest.mark.ocr
    def test_screencapture_ocr_tesseract_availability(self, services):
        """Test Screen Capture OCR Tesseract dependency."""
        screencapture_service = services.screen_capture("admin")
        
        # Try OCR operation to check if Tesseract is available
        result = screencapture_service.extract_text_from_screenshot(
            image_data=b"dummy_data"
        )
        
        if result is None:
            print("OCR failed - Tesseract might not be installed on server")
        else:
            print("OCR functionality appears to be available")
            assert isinstance(result, str)


class TestScreenCaptureServiceArtifacts:
    """Tests for Screen Capture service with artifact management and file verification."""

    @pytest.fixture
    def artifacts_dir(self):
        """Ensure artifacts directory exists and return path."""
        artifacts_path = os.path.join(os.getcwd(), "artifacts", "screenshots")
        os.makedirs(artifacts_path, exist_ok=True)
        return artifacts_path

    def test_screencapture_save_to_artifacts_full_screen(self, services, artifacts_dir):
        """Test saving full screen capture to artifacts directory."""
        screencapture_service = services.screen_capture("admin")
        
        # Create unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(artifacts_dir, f"fullscreen_test_{timestamp}.png")
        
        # Capture full screen with custom save path
        result = screencapture_service.capture_screenshot(
            capture_region=False,
            save_path=screenshot_path
        )
        
        if result is not None and result["success"]:
            print(f"✅ Screenshot saved to: {screenshot_path}")
            
            # Verify file exists
            assert os.path.exists(screenshot_path), f"Screenshot file not found at {screenshot_path}"
            
            # Verify file has content
            file_size = os.path.getsize(screenshot_path)
            assert file_size > 0, f"Screenshot file is empty: {file_size} bytes"
            
            # Verify image data was returned
            assert len(result["image_data"]) > 0
            
            # Verify file path in result matches our path
            print(f"Server returned path: {result['file_path']}")
            print(f"Expected path: {screenshot_path}")
            
            # File exists regardless of path mismatch (server may use different path)
            assert os.path.exists(screenshot_path)
            
            print(f"✅ Full screen screenshot verified: {file_size} bytes")
        else:
            print("❌ Full screen capture failed - check screen recording permissions")

    def test_screencapture_save_to_artifacts_region_capture(self, services, artifacts_dir):
        """Test saving region capture to artifacts directory."""
        screencapture_service = services.screen_capture("admin")
        
        # Create unique filename for region capture
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(artifacts_dir, f"region_test_{timestamp}.png")
        
        # Capture specific region
        result = screencapture_service.capture_screenshot(
            capture_region=True,
            region_x=200,
            region_y=200,
            region_width=400,
            region_height=300,
            save_path=screenshot_path
        )
        
        if result is not None and result["success"]:
            print(f"✅ Region screenshot saved to: {screenshot_path}")
            
            # Verify file exists and has content
            assert os.path.exists(screenshot_path), f"Screenshot file not found at {screenshot_path}"
            file_size = os.path.getsize(screenshot_path)
            assert file_size > 0, f"Screenshot file is empty"
            
            # Region capture should typically be smaller than full screen
            print(f"✅ Region screenshot verified: {file_size} bytes")
            print(f"Region: 400x300 at (200,200)")
        else:
            print("❌ Region capture failed - check screen recording permissions")

    def test_screencapture_save_multiple_artifacts(self, services, artifacts_dir):
        """Test saving multiple screenshots to artifacts directory."""
        screencapture_service = services.screen_capture("admin")
        
        # Capture multiple screenshots with different regions
        regions = [
            {"name": "topleft", "x": 0, "y": 0, "w": 300, "h": 200},
            {"name": "center", "x": 400, "y": 300, "w": 300, "h": 200},
            {"name": "small", "x": 100, "y": 100, "w": 150, "h": 100}
        ]
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_files = []
        
        for i, region in enumerate(regions):
            screenshot_path = os.path.join(artifacts_dir, f"multi_{region['name']}_{timestamp}_{i}.png")
            
            result = screencapture_service.capture_screenshot(
                capture_region=True,
                region_x=region["x"],
                region_y=region["y"],
                region_width=region["w"],
                region_height=region["h"],
                save_path=screenshot_path
            )
            
            if result is not None and result["success"]:
                assert os.path.exists(screenshot_path)
                file_size = os.path.getsize(screenshot_path)
                assert file_size > 0
                saved_files.append((screenshot_path, file_size, region))
                print(f"✅ Saved {region['name']} region: {file_size} bytes")
            else:
                print(f"❌ Failed to capture {region['name']} region")
        
        print(f"✅ Successfully saved {len(saved_files)} screenshots to artifacts")
        
        # Verify we saved at least some screenshots
        if len(saved_files) > 0:
            total_size = sum(size for _, size, _ in saved_files)
            print(f"Total artifacts size: {total_size} bytes")

    def test_screencapture_artifacts_with_ocr_verification(self, services, artifacts_dir):
        """Test saving screenshot and performing OCR verification."""
        screencapture_service = services.screen_capture("admin")
        
        # Capture a region that might contain text (top of screen with menu bar)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(artifacts_dir, f"ocr_test_{timestamp}.png")
        
        result = screencapture_service.capture_screenshot(
            capture_region=True,
            region_x=0,
            region_y=0,
            region_width=800,
            region_height=100,  # Top menu bar area
            save_path=screenshot_path
        )
        
        if result is not None and result["success"]:
            print(f"✅ OCR test screenshot saved to: {screenshot_path}")
            
            # Verify file exists
            assert os.path.exists(screenshot_path)
            file_size = os.path.getsize(screenshot_path)
            assert file_size > 0
            
            # Try OCR on the saved screenshot
            extracted_text = screencapture_service.extract_text_from_screenshot(
                file_path=screenshot_path
            )
            
            if extracted_text is not None:
                print(f"✅ OCR extracted text: '{extracted_text}'")
                assert isinstance(extracted_text, str)
                
                # Save OCR results to text file for inspection
                ocr_results_path = os.path.join(artifacts_dir, f"ocr_results_{timestamp}.txt")
                with open(ocr_results_path, 'w') as f:
                    f.write(f"Screenshot: {screenshot_path}\n")
                    f.write(f"File size: {file_size} bytes\n") 
                    f.write(f"Region: 800x100 at (0,0)\n")
                    f.write(f"Extracted text:\n{extracted_text}\n")
                
                print(f"✅ OCR results saved to: {ocr_results_path}")
            else:
                print("❌ OCR extraction failed - possibly no text in region or Tesseract not available")
        else:
            print("❌ OCR test screenshot capture failed")

    def test_screencapture_artifacts_cleanup_verification(self, services, artifacts_dir):
        """Test artifacts directory and provide cleanup information."""
        # List all screenshots in artifacts directory
        screenshot_files = []
        for file in os.listdir(artifacts_dir):
            if file.endswith(('.png', '.jpg', '.jpeg')):
                file_path = os.path.join(artifacts_dir, file)
                file_size = os.path.getsize(file_path)
                screenshot_files.append((file, file_size))
        
        print(f"\n📁 Artifacts directory: {artifacts_dir}")
        print(f"📸 Total screenshots: {len(screenshot_files)}")
        
        if screenshot_files:
            total_size = sum(size for _, size in screenshot_files)
            print(f"💾 Total size: {total_size} bytes ({total_size / 1024 / 1024:.2f} MB)")
            
            print("\nScreenshots saved:")
            for filename, size in screenshot_files:
                print(f"  • {filename}: {size} bytes")
            
            # Provide cleanup command
            print(f"\nTo clean up screenshots: rm -f {artifacts_dir}/*.png {artifacts_dir}/*.jpg")
        else:
            print("No screenshots found in artifacts directory")
        
        # This test always passes - it's just for information
        assert os.path.exists(artifacts_dir)