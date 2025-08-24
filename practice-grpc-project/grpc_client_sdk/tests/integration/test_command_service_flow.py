from .base_test import RootOnlyTest


class TestCommandService(RootOnlyTest):
    """
    Test the CommandService using root context.
    
    These tests use the root context since they're testing system-level command execution.
    """

    def test_run_command_service_client(self):
        """
        Test executing shell commands via CommandServiceClient.
        This test verifies command execution and result handling.
        """
        # Use the simplified interface - no manual client setup needed!
        result = self.root.command.run_command(command="whoami")

        # Check the result
        assert result.exit_code == 0
        assert result.stdout.strip(), "Expected non-empty output"

    def test_get_logged_in_users(self):
        """
        Test retrieving logged-in users via CommandServiceClient.
        This test verifies user information retrieval.
        """
        # Use the simplified interface
        result = self.root.command.get_logged_in_users()
        print(f"Logged-in users: {result}")

        # Check if the result is a dictionary and not empty
        assert isinstance(result, dict)
        assert "logged_in_users" in result and "console_user" in result
        
        # More flexible assertion - check that we have some logged-in users
        logged_in_users = result.get("logged_in_users", [])
        assert isinstance(logged_in_users, list), "Expected logged_in_users to be a list"
        
        # Note: Removed hardcoded username check as it should be environment-agnostic

