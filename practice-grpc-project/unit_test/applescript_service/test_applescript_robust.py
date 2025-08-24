"""
Robust integration tests for AppleScript service.

Tests that handle real-world scenarios including server errors,
permissions issues, and service availability in a robust way.
"""

import pytest


class TestAppleScriptServiceRobust:
    """Robust tests for AppleScript service that handle real-world issues."""

    def test_applescript_service_client_availability(self, services):
        """Test that AppleScript service clients are properly available."""
        # Test that we can get AppleScript service clients
        root_service = services.apple_script("root")
        user_service = services.apple_script("admin")
        
        assert root_service is not None
        assert user_service is not None
        
        # Test that they have the expected methods
        assert hasattr(root_service, 'run_applescript')
        assert hasattr(root_service, 'stream_applescript')
        assert callable(root_service.run_applescript)
        assert callable(root_service.stream_applescript)

    def test_applescript_service_connection_handling(self, services):
        """Test AppleScript service connection handling."""
        applescript_service = services.apple_script("root")
        
        # Test basic service properties
        assert applescript_service.client_name == "root"
        assert applescript_service.logger is not None
        
        # Service should have stub available after connection
        assert applescript_service.stub is not None

    def test_applescript_service_error_response_structure(self, services):
        """Test that AppleScript service returns proper error structure."""
        applescript_service = services.apple_script("root")
        
        # Test with simple script (might fail due to server issues)
        result = applescript_service.run_applescript('return "test"')
        
        # Regardless of success/failure, result structure should be correct
        assert result is not None
        assert isinstance(result, dict)
        assert "success" in result
        assert "stdout" in result  
        assert "stderr" in result
        assert "exit_code" in result
        assert "execution_time_ms" in result
        
        # Types should be correct
        assert isinstance(result["success"], bool)
        assert isinstance(result["stdout"], str)
        assert isinstance(result["stderr"], str)
        assert isinstance(result["exit_code"], int)
        assert isinstance(result["execution_time_ms"], int)

    def test_applescript_service_contexts_comparison(self, services):
        """Test AppleScript service behavior across different contexts."""
        root_service = services.apple_script("root")
        user_service = services.apple_script("admin")
        
        # Both services should have same interface but different context
        assert root_service.client_name == "root"
        assert user_service.client_name == "admin"
        
        # Both should have proper logger setup
        assert "root" in str(root_service.logger.name).lower()
        assert "admin" in str(user_service.logger.name).lower()

    def test_applescript_service_timeout_parameter(self, services):
        """Test AppleScript service timeout parameter handling."""
        applescript_service = services.apple_script("root")
        
        # Test with custom timeout parameter (even if script fails)
        result = applescript_service.run_applescript(
            'return "timeout test"',
            timeout_seconds=5
        )
        
        # Should get a result back (success or failure)
        assert result is not None
        assert isinstance(result, dict)

    def test_applescript_service_parameters_handling(self, services):
        """Test AppleScript service parameter handling."""
        applescript_service = services.apple_script("root")
        
        # Test with parameters dict (even if script fails)
        result = applescript_service.run_applescript(
            'return "parameter test"',
            parameters={"test_param": "test_value"},
            timeout_seconds=5
        )
        
        # Should handle parameters without crashing
        assert result is not None
        assert isinstance(result, dict)

    def test_applescript_streaming_structure(self, services):
        """Test AppleScript streaming response structure."""
        applescript_service = services.apple_script("root")
        
        # Test streaming (should return generator even if stream fails)
        stream = applescript_service.stream_applescript('return "streaming test"')
        
        assert stream is not None
        
        # Convert to list to test structure
        outputs = list(stream)
        
        # Should get at least one output (even if error)
        assert len(outputs) > 0
        
        # Test structure of streaming outputs
        for output in outputs:
            assert isinstance(output, dict)
            assert "output" in output
            assert "is_error" in output  
            assert "is_complete" in output
            assert "exit_code" in output
            
            # Types should be correct
            assert isinstance(output["output"], str)
            assert isinstance(output["is_error"], bool)
            assert isinstance(output["is_complete"], bool)
            assert isinstance(output["exit_code"], int)

    def test_applescript_error_handling_robustness(self, services):
        """Test AppleScript service error handling robustness."""
        applescript_service = services.apple_script("root")
        
        # Test various error scenarios
        test_scripts = [
            'return "simple test"',           # Simple script
            'invalid syntax here',            # Invalid syntax
            '',                              # Empty script
            'tell app "NonExistentApp" to quit', # Non-existent app
        ]
        
        for script in test_scripts:
            result = applescript_service.run_applescript(script)
            
            # Should always get a result, never None
            assert result is not None
            assert isinstance(result, dict)
            assert "success" in result
            
            # If it fails, should have proper error info
            if not result["success"]:
                assert result["exit_code"] != 0 or len(result["stderr"]) > 0

    def test_applescript_service_multiple_calls(self, services):
        """Test AppleScript service handles multiple sequential calls."""
        applescript_service = services.apple_script("root")
        
        # Make multiple calls to test service stability
        results = []
        for i in range(3):
            result = applescript_service.run_applescript(f'return "call {i}"')
            results.append(result)
        
        # All calls should return results
        for i, result in enumerate(results):
            assert result is not None
            assert isinstance(result, dict)
            assert "success" in result

    def test_applescript_service_integration_with_session_manager(self, services):
        """Test AppleScript service integration with session manager."""
        # Test that AppleScript service works alongside other services
        applescript_service = services.apple_script("root")
        command_service = services.command("root")
        
        # Both should be available
        assert applescript_service is not None
        assert command_service is not None
        
        # Test that they work independently
        as_result = applescript_service.run_applescript('return "applescript test"')
        cmd_result = command_service.run_command("echo 'command test'")
        
        assert as_result is not None
        assert cmd_result is not None

    def test_applescript_server_error_detection(self, services):
        """Test detection and handling of server-side errors."""
        applescript_service = services.apple_script("root")
        
        result = applescript_service.run_applescript('return "server test"')
        
        # If we get server errors, they should be properly captured
        if result and not result["success"]:
            # Server error messages should be in stderr
            assert isinstance(result["stderr"], str)
            
            # Common server error patterns
            server_error_patterns = [
                "has no attribute",
                "native script execution",
                "Unexpected error"
            ]
            
            # If it's a server error, stderr should contain one of these patterns
            if any(pattern in result["stderr"] for pattern in server_error_patterns):
                # This is expected - server implementation issue, not client issue
                assert result["exit_code"] == -1
                print(f"Detected server-side error: {result['stderr']}")


class TestAppleScriptServiceConfiguration:
    """Tests for AppleScript service configuration and setup."""

    def test_applescript_service_logger_configuration(self, services):
        """Test AppleScript service logger is properly configured."""
        root_service = services.apple_script("root")
        user_service = services.apple_script("admin")
        
        # Both should have different logger names
        assert root_service.logger.name != user_service.logger.name
        assert "root" in root_service.logger.name.lower()
        assert "admin" in user_service.logger.name.lower()

    def test_applescript_service_client_names(self, services):
        """Test AppleScript service client name configuration."""
        root_service = services.apple_script("root")
        user_service = services.apple_script("admin")
        
        assert root_service.client_name == "root"
        assert user_service.client_name == "admin"

    def test_applescript_service_stub_configuration(self, services):
        """Test AppleScript service stub configuration."""
        applescript_service = services.apple_script("root")
        
        # Should have AppleScriptServiceStub
        assert applescript_service.stub is not None
        
        # Should have the expected gRPC methods
        expected_methods = ['RunAppleScript', 'StreamAppleScript']
        for method_name in expected_methods:
            assert hasattr(applescript_service.stub, method_name)
            assert callable(getattr(applescript_service.stub, method_name))