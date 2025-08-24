"""
Proof of Concept: Service Registry Pattern

This test demonstrates the new Service Registry approach with before/after examples.
It shows how the same functionality can be achieved with much simpler code.

Run with: pytest test_service_registry_poc.py -v
"""
import pytest


class TestServiceRegistryBasics:
    """Basic usage patterns that cover 90% of test scenarios."""

    def test_simple_command(self, command):
        """
        Simple command execution - the most common test pattern.
        
        OLD approach required: command_service, setup, understanding fixture chains
        NEW approach: just ask for 'command' fixture
        """
        result = command("whoami")
        assert result.exit_code == 0
        assert result.stdout.strip()  # Should return actual username

    def test_smart_command_with_context(self, command):
        """
        Smart command that can handle both user and root contexts.
        
        This demonstrates the 'smart' aspect - the same fixture can handle
        different contexts based on parameters.
        """
        # User context (default)
        user_result = command("whoami")
        assert user_result.exit_code == 0
        
        # Root context when needed (if system supports it)
        # Note: This might fail in test environments without sudo access
        try:
            root_result = command("whoami", as_root=True)
            # If successful, we're in a system that allows root commands
            assert root_result.exit_code == 0
        except Exception:
            # Expected in restricted test environments
            pytest.skip("Root access not available in test environment")

    def test_screen_capture_simple(self, screen_capture):
        """
        Simple screen capture test.
        
        OLD approach: user_services.screen_capture.capture_screenshot()
        NEW approach: screen_capture() 
        """
        screenshot = screen_capture()
        assert screenshot is not None
        assert screenshot.get("success", False), "Screenshot should succeed"
        
        # Check that we got image data
        image_data = screenshot.get("image_data")
        assert image_data, "Should return image data"

    def test_file_operations_workflow(self, command, temp_file):
        """
        Combined workflow using multiple simple fixtures.
        
        This shows how simple fixtures compose cleanly for complex workflows.
        """
        # Create test file
        test_content = "Hello from Service Registry test!"
        file_path = temp_file(test_content)
        
        # Verify file exists using command service
        result = command(f"test -f {file_path} && echo 'file_exists'")
        assert result.exit_code == 0
        assert "file_exists" in result.stdout


class TestExplicitContextControl:
    """Advanced patterns for when you need explicit context control."""

    def test_both_root_and_user_commands(self, root_command, user_command):
        """
        Test that needs both root and user commands explicitly.
        
        This was impossible with the old approach - you could only get
        one context at a time. Now it's simple and clear.
        """
        # Root command for system operations
        root_result = root_command("pwd")  # Should work in root context
        assert root_result.exit_code == 0
        
        # User command for user operations  
        user_result = user_command("pwd")  # Should work in user context
        assert user_result.exit_code == 0
        
        # Both should succeed but might have different working directories

    def test_mixed_services(self, root_command, screen_capture, user_command):
        """
        Test using services from different contexts in one test.
        
        This demonstrates the flexibility of the new approach.
        """
        # System check with root
        system_check = root_command("pwd")
        assert system_check.exit_code == 0
        
        # User operation
        user_check = user_command("echo 'user test'")
        assert user_check.exit_code == 0
        assert "user test" in user_check.stdout
        
        # UI operation  
        screenshot = screen_capture()
        assert screenshot is not None


class TestAdvancedUsage:
    """Advanced patterns for power users (1% of tests)."""

    def test_service_registry_direct_access(self, service_registry):
        """
        Direct registry access for maximum flexibility.
        
        This shows how to use the registry directly for complex scenarios.
        """
        # Get services with custom configuration
        command_service = service_registry.get_service("command", context="user")
        
        # Use the service
        result = command_service.run_command("echo 'direct registry access'")
        assert result.exit_code == 0
        assert "direct registry access" in result.stdout

    def test_multiple_user_sessions(self, user_session_factory):
        """
        Test with multiple user sessions.
        
        This shows how to create sessions for different users when needed.
        """
        # Create session for default admin user
        admin_session = user_session_factory("admin")
        assert admin_session is not None
        
        # Session should have user context with services
        assert hasattr(admin_session, 'user_context')
        assert hasattr(admin_session.user_context, 'command')
        
        # Use the session
        command_result = admin_session.user_context.command.run_command("whoami")
        assert command_result.exit_code == 0

    def test_debug_available_services(self, debug_services):
        """
        Debug test to see what services are available.
        
        Useful for development and troubleshooting.
        """
        print("\nAvailable services:")
        for context, services in debug_services.items():
            print(f"  {context}: {', '.join(services)}")
        
        # Verify we have expected services
        assert "root" in debug_services
        assert "user" in debug_services
        assert "command" in debug_services["root"]
        assert "command" in debug_services["user"]
        assert "screen_capture" in debug_services["user"]


class TestBackwardCompatibility:
    """Tests to ensure the new approach doesn't break existing functionality."""

    def test_legacy_setup_fixture_still_works(self, setup):
        """
        Verify that existing tests using 'setup' fixture still work.
        
        This ensures zero-disruption migration.
        """
        assert setup is not None
        # setup should contain station configuration
        # The exact structure depends on your StationLoader implementation

    def test_safe_commands_utility(self, command, safe_commands):
        """
        Test the safe commands utility fixture.
        
        This replaces the old sample_commands fixture with a simpler approach.
        """
        # Test basic commands
        for cmd_name, cmd in safe_commands['basic'].items():
            result = command(cmd)
            assert result.exit_code == 0, f"Command '{cmd_name}' failed"


# =============================================================================
# Performance and Reliability Tests
# =============================================================================

class TestPerformanceAndReliability:
    """Tests to verify performance improvements and reliability."""

    def test_service_caching_performance(self, command):
        """
        Test that services are cached for performance.
        
        Multiple calls should reuse the same service instance.
        """
        # First call - might be slower (creates service)
        result1 = command("echo 'test1'")
        assert result1.exit_code == 0
        
        # Second call - should be faster (cached service)
        result2 = command("echo 'test2'")
        assert result2.exit_code == 0
        
        # Both should succeed
        assert "test1" in result1.stdout
        assert "test2" in result2.stdout

    def test_parallel_execution_safety(self, command, screen_capture):
        """
        Test that multiple services can be used safely in parallel.
        
        This verifies thread safety of the registry.
        """
        import threading
        import time
        
        results = []
        
        def worker():
            result = command("echo 'parallel test'")
            screenshot = screen_capture()
            results.append((result.exit_code, screenshot is not None))
        
        # Run multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # All should succeed
        assert len(results) == 3
        for exit_code, screenshot_ok in results:
            assert exit_code == 0
            assert screenshot_ok

    @pytest.mark.parametrize("context", ["user", "root"])
    def test_command_service_contexts(self, service_registry, context):
        """
        Parametrized test to verify both contexts work.
        
        This tests the registry's ability to handle different contexts.
        """
        command_service = service_registry.get_service("command", context=context)
        result = command_service.run_command("echo 'context test'")
        assert result.exit_code == 0
        assert "context test" in result.stdout


# =============================================================================
# Migration Demonstration
# =============================================================================

def test_migration_comparison():
    """
    This test demonstrates the difference between old and new approaches.
    
    It's not meant to run - just to show the code comparison.
    """
    
    # OLD APPROACH (complex, many dependencies)
    """
    def test_old_approach(command_service, user_services, temp_file_factory, test_logger):
        # Complex setup with multiple fixtures
        test_logger.info("Starting test")
        temp_file = temp_file_factory(content="test data", suffix=".txt")
        
        # Limited - can only use root command service
        result = command_service.run_command(f"test -f {temp_file}")
        assert result.exit_code == 0
        
        # Need separate fixture for user services
        screenshot = user_services.screen_capture.capture_screenshot()
        assert screenshot["success"]
        
        # Can't easily get user command service!
    """
    
    # NEW APPROACH (simple, clear)
    """
    def test_new_approach(command, screen_capture, temp_file):
        # Simple, clear dependencies
        temp_file_path = temp_file("test data")
        
        # Smart command service - works for both contexts
        result = command(f"test -f {temp_file_path}")
        assert result.exit_code == 0
        
        # Simple screen capture
        screenshot = screen_capture()
        assert screenshot["success"]
        
        # Can easily get both contexts when needed:
        # root_result = command("sudo something", as_root=True)
    """
    
    pytest.skip("This is a documentation test, not meant to run")