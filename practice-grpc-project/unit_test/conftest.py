import pytest

from test_framework.grpc_session.session_manager import GrpcSessionManager
from test_framework.utils import get_logger

pytest_plugins = [
    "test_framework.fixtures.config_fixtures",
    "test_framework.fixtures.logging_fixtures",
    "test_framework.fixtures.login_fixtures"
]

@pytest.fixture(scope="function")
def services(test_config, login_manager, request):
    """
    Single fixture that replaces all the complex fixture dependencies.
    
    Now uses proper pytest dependency injection:
    - login_manager: Provided by login fixtures via pytest_plugins
    - test_config: Provided by config fixtures via pytest_plugins

    Provides simple API:
        services.command("root").run_command("whoami")  # root-grpc-server
        services.command("admin").run_command("whoami") # user-agent server
        services.apple_script("admin").run_applescript("...")
        services.login_manager.ensure_logged_out("admin")
    """
    logger = get_logger(f"services-{request.node.name}")

    # Create enhanced session manager
    session_mgr = GrpcSessionManager(test_config["station_id"])

    # Setup session for expected user
    expected_user = test_config["expected_user"]
    logger.info(f"Setting up session for user: {expected_user}")

    try:
        # This will wait for user login and establish both connections:
        # - root-grpc-server (system operations)
        # - user-agent server (UI/user operations)
        session_mgr.setup_user(expected_user, timeout=test_config["login_timeout"])

        # Use the login_manager provided by pytest fixtures
        # No need to manually create adapter - it's handled by login_fixtures

        # Create services object with simple API
        class Services:
            def __init__(self, session_manager, login_mgr):
                self.session_manager = session_manager
                self.login_manager = login_mgr
                self.expected_user = expected_user

            def command(self, context: str):
                """Get command service - routes to correct server"""
                return self.session_manager.command(context)

            def apple_script(self, context: str):
                """Get AppleScript service - routes to correct server"""
                return self.session_manager.apple_script(context)

            def file_transfer(self, context: str):
                """Get file transfer service - routes to correct server"""
                return self.session_manager.file_transfer(context)

            def screen_capture(self, context: str):
                """Get screen capture service - routes to correct server"""
                return self.session_manager.screen_capture(context)

            def logs_monitor_stream(self, context: str):
                """Get logs monitoring service - routes to correct server"""
                return self.session_manager.logs_monitor_stream(context)

            def grpc_connection(self, context: str):
                """Get connection service - routes to correct server"""
                return self.session_manager.grpc_connection(context)

            def gui_automation(self, context: str):
                """Get GUI automation service - routes to correct server"""
                return self.session_manager.gui_automation(context)

            def registry(self, context: str):
                """Get registry service - routes to correct server"""
                return self.session_manager.registry(context)

            def web_automation(self, context: str):
                """Get web automation service - routes to correct server"""
                return self.session_manager.web_automation(context)

            def health_check(self, context: str) -> bool:
                """Perform health check for context"""
                return self.session_manager.health_check(context)

            def get_current_user(self):
                """Get current logged in user"""
                return self.session_manager.get_current_user()

        services_obj = Services(session_mgr, login_manager)
        logger.info(f"Services ready for user: {expected_user}")

        yield services_obj

    except Exception as e:
        logger.error(f"Failed to setup services: {e}")
        pytest.skip(f"Service setup failed: {e}")

    finally:
        # Cleanup: Ensure user is logged out
        try:
            current_user = session_mgr.get_current_user()
            if current_user:
                logger.info(f"🧹 Cleaning up logged in user: {current_user}")
                # Use LoginManager for intelligent cleanup  
                login_manager.ensure_logged_out(current_user)
        except Exception as e:
            logger.warning(f"Cleanup warning: {e}")