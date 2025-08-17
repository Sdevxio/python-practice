import datetime
import os
from typing import Any

import pytest

from test_framework.grpc_session.session_manager import GrpcSessionManager
from test_framework.login_logout.applescript_logout import logout_user
from test_framework.login_logout.tapping_manager import TappingManager
from test_framework.utils import set_test_case, get_logger, LoggerManager
from test_framework.utils.loaders.station_loader import StationLoader
from test_framework.utils.logger_settings.logger_config import LoggerConfig

pytest_plugins = [
    "test_framework.hooks.logging_context_hook",
]

# Global run ID for the test session
RUN_ID = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


@pytest.fixture(scope="session", autouse=True)
def setup_logging():
    """Initialize logging with run ID and environment information."""
    LoggerConfig.initialize()
    log_manager = LoggerManager()
    environment = os.environ.get("TEST_ENVIRONMENT", "test")
    log_manager.set_environment(environment)
    pytest.run_id = RUN_ID
    return log_manager


@pytest.fixture(scope="function")
def test_logger(request, setup_logging):
    """Fixture that provides a logger configured with the test name."""
    test_name = request.node.name
    set_test_case(test_name)
    logger = get_logger(f"{test_name}")
    correlation_id = f"{RUN_ID[:8]}"
    setup_logging.set_correlation_id(correlation_id)
    logger.info(f"{'=' * 30} START SESSION SETUP")

    yield logger

    passed = True
    if hasattr(request.node, 'rep_call'):
        passed = not request.node.rep_call.failed
    if passed:
        logger.info(f"Test passed: {test_name}")
    else:
        logger.error(f"Test failed: {test_name}")


@pytest.fixture(scope="function")
def session_config():
    """Session configuration for the test using StationLoader."""
    station_id = os.environ.get("TEST_STATION", "station1")
    station_loader = StationLoader()

    # Get all configurations at once
    station_config = station_loader.get_complete_station_config(station_id)
    test_users = station_loader.get_test_users()
    test_cards = station_loader.get_test_cards()
    e2e_defaults = station_loader.get_e2e_defaults()

    # Determine expected user with fallback
    expected_user = (
            os.environ.get("TEST_USER") or
            test_users.get('test_user', {}).get('username') or
            "macos_lab_1"
    )

    # Determine expected card with fallback
    expected_card = (
            os.environ.get("TEST_CARD") or
            (next(iter(test_cards.values())).get('card_id') if test_cards else None) or
            "AF17C52201")
    return {
        "station_id": station_id,
        "expected_user": expected_user,
        "expected_card":expected_card,
        "login_timeout": e2e_defaults.get('login_timeout', 60),
        "station_config": station_config,
        "log_file_path": station_loader.get_e2e_defaults().get("log_file_path"),
        "test_users": test_users,
        "e2e_defaults": e2e_defaults,
    }


@pytest.fixture(scope="function")
def tapping_config():
    """Configuration for tapping behavior."""
    config_map = {
        "enable_tapping": ("ENABLE_TAPPING", "true", lambda x: x.lower() == "true"),
        "login_max_attempts": ("LOGIN_TAP_ATTEMPTS", "3", int),
        "logoff_max_attempts": ("LOGOFF_TAP_ATTEMPTS", "3", int),
        "verification_timeout": ("TAP_VERIFICATION_TIMEOUT", "15", int),
        "retry_delay": ("TAP_RETRY_DELAY", "2.0", float),
    }

    return {
        key: converter(os.environ.get(env_var, default))
        for key, (env_var, default, converter) in config_map.items()
    }


@pytest.fixture(scope="function")
def grpc_session_manager(session_config, test_logger):
    """Pure gRPC session manager without tapping concerns."""
    return GrpcSessionManager(
        station_id=session_config["station_id"],
        logger=test_logger
    )


@pytest.fixture(scope="function")
def tapping_manager(session_config, tapping_config, test_logger):
    """Tapping manager for login/logoff operations."""
    return TappingManager(
        station_id=session_config["station_id"],
        enable_tapping=tapping_config["enable_tapping"],
        logger=test_logger
    )


@pytest.fixture(scope="function")
def session_setup(session_config, tapping_config, grpc_session_manager, tapping_manager, test_logger):
    """Complete session setup with modular tapping and gRPC management."""
    test_logger.info("Setting up session with modular architecture")

    expected_user = session_config["expected_user"]
    login_timeout = session_config["login_timeout"]
    session_context = None

    # # Pre-test cleanup: Ensure no user is currently logged in
    # test_logger.info("Checking for existing user sessions before test start...")
    # _ensure_clean_start(grpc_session_manager, tapping_manager, tapping_config, test_logger)

    # Perform login tap if enabled
    tap_start_time = None
    login_success = True
    if tapping_config["enable_tapping"]:
        tap_start_time = datetime.datetime.now()
        test_logger.info(f"Login tap start time: {tap_start_time}")
        # login_success = tapping_manager.perform_login_tap(
        #     verification_callback=None,
        #     max_attempts=tapping_config["login_max_attempts"]
        # )
        if not login_success:
            test_logger.warning("Login tap failed, continuing with session creation")

    # Create gRPC session
    try:
        session_context = grpc_session_manager.create_session(
            expected_user=expected_user,
            timeout=login_timeout
        )
        session_created_time = datetime.datetime.now()
        test_logger.info(f"Session established for user: {session_context.username}, at: {session_created_time}")

        login_duration = None
        if tap_start_time is not None:
            login_duration = (session_created_time - tap_start_time).total_seconds()

        session_context.session_timing= {
            "tap_start_time": tap_start_time,
            "session_created_time": session_created_time,
            "login_duration": login_duration
        }

        # Attach teardown dependencies
        session_context._cleanup_data = {
            'grpc_manager': grpc_session_manager,
            'tapping_manager': tapping_manager,
            'tapping_config': tapping_config,
            'expected_user': expected_user,
        }

        yield session_context

    except Exception as e:
        test_logger.error(f"Failed to create session: {e}")
        pytest.fail(f"Session creation failed: {e}")
    #
    # finally:
    #     if session_context is not None:
    #         _cleanup_session(session_context, test_logger)


def _ensure_clean_start(grpc_manager: Any, tapping_manager: Any, tapping_config: dict, logger: Any) -> None:
    """Ensure no user is logged in before starting the test."""
    try:
        # Check current user state
        current_state = grpc_manager.get_logged_in_users()
        console_user = current_state.get("console_user", "")

        if console_user and console_user.strip():
            logger.warning(f"Found existing user '{console_user}' logged in. Performing pre-test cleanup...")

            # Create a temporary session context for logout
            temp_session_context = type('TempSession', (), {
                'user_context': type('UserContext', (), {
                    'apple_script': grpc_manager._session_context.user_context.apple_script if hasattr(grpc_manager, '_session_context') else None
                })()
            })()

            # First try AppleScript logout
            if hasattr(temp_session_context.user_context, 'apple_script') and temp_session_context.user_context.apple_script:
                logger.info("Attempting pre-test logout via AppleScript...")
                logout_success = logout_user(
                    session_context=temp_session_context,
                    grpc_manager=grpc_manager,
                    expected_user=console_user,
                    max_attempts=2,
                    verification_timeout=10,
                    retry_delay=1.0,
                    logger=logger
                )

                if logout_success:
                    logger.info("Pre-test AppleScript logout successful")
                    return
                else:
                    logger.warning("Pre-test AppleScript logout failed, trying tapping fallback...")

            # Fallback to tapping manager
            if tapping_config.get("enable_tapping", False):
                logger.info("Attempting pre-test logout via tapping...")
                logout_success = tapping_manager.perform_logoff_tap(
                    expected_user=console_user,
                    grpc_session_manager=grpc_manager,
                    max_attempts=2,
                    verification_timeout=10,
                    retry_delay=1.0
                )

                if logout_success:
                    logger.info("Pre-test tapping logout successful")
                else:
                    logger.error("Pre-test tapping logout failed - proceeding with test anyway")
            else:
                logger.warning("Tapping disabled - cannot perform physical logout. Proceeding with test...")

        else:
            logger.info("No user currently logged in - clean start confirmed")

    except Exception as e:
        logger.warning(f"Error during pre-test cleanup check: {e}. Proceeding with test...")

def _cleanup_session(session_context: Any, test_logger: Any) -> None:
    """Helper function to handle session cleanup."""
    test_logger.info("=" * 30 + " TEARDOWN SESSION ")

    if not hasattr(session_context, '_cleanup_data'):
        test_logger.info("Session teardown completed (no cleanup data)")
        return

    cleanup_data = session_context._cleanup_data
    grpc_manager = cleanup_data['grpc_manager']
    tapping_manager = cleanup_data['tapping_manager']
    expected_user = cleanup_data.get('expected_user')
    tapping_config = cleanup_data.get('tapping_config', {})

    # First check if there's actually a user logged in
    try:
        current_state = grpc_manager.get_logged_in_users()
        console_user = current_state.get("console_user", "")

        if not console_user or not console_user.strip():
            test_logger.info("No user currently logged in - cleanup not needed")
            test_logger.info("Session teardown completed")
            return

        test_logger.info(f"Found user '{console_user}' logged in - proceeding with logout")
    except Exception as e:
        test_logger.warning(f"Could not check current user state: {e}. Proceeding with logout attempt...")

    # Use the logout_user function for clean logout
    logoff_success = logout_user(
        session_context=session_context,
        grpc_manager=grpc_manager,
        expected_user=expected_user,
        max_attempts=tapping_config.get('logoff_max_attempts', 3),
        verification_timeout=tapping_config.get('verification_timeout', 15),
        retry_delay=tapping_config.get('retry_delay', 2.0),
        logger=test_logger
    )

    if not logoff_success:
        test_logger.warning("AppleScript logout failed - checking if user is still logged in...")

        try:
            current_state = grpc_manager.get_logged_in_users()
            console_user_after = current_state.get("console_user", "")

            if not console_user_after or not console_user_after.strip():
                test_logger.info("User is no longer logged in - AppleScript may have worked despite failure report")
                logoff_success = True
            elif console_user_after == expected_user:
                test_logger.warning("User is still logged in - attempting fallback to tapping manager")
                logoff_success = tapping_manager.perform_logoff_tap(
                    expected_user=cleanup_data['expected_user'],
                    grpc_session_manager=cleanup_data['grpc_manager'],
                    max_attempts=cleanup_data['tapping_config']["logoff_max_attempts"],
                    verification_timeout=cleanup_data['tapping_config']["verification_timeout"],
                    retry_delay=cleanup_data['tapping_config']["retry_delay"]
                )
            else:
                test_logger.info(f"Different user '{console_user_after}' is now logged in - logout goal achieved")
                logoff_success = True

        except Exception as e:
            test_logger.error(f"Could not verify user state after AppleScript failure: {e}")
            # If we can't verify, try tapping as last resort
            test_logger.warning("Attempting tapping fallback due to verification failure...")
            logoff_success = tapping_manager.perform_logoff_tap(
                expected_user=cleanup_data['expected_user'],
                grpc_session_manager=cleanup_data['grpc_manager'],
                max_attempts=cleanup_data['tapping_config']["logoff_max_attempts"],
                verification_timeout=cleanup_data['tapping_config']["verification_timeout"],
                retry_delay=cleanup_data['tapping_config']["retry_delay"]
            )

    if logoff_success:
        test_logger.info("Verified logoff completed successfully")
    else:
        test_logger.error("Verified logoff failed - user may still be logged in")
        _log_final_user_state(grpc_manager, test_logger)

    test_logger.info("Session teardown completed")


def _log_final_user_state(grpc_manager:Any, test_logger: Any) -> None:
    """Helper function to log final user state on logoff failure."""
    try:
        final_state = grpc_manager.get_logged_in_users()
        final_console = final_state.get("console_user", "")
        test_logger.error(f"Final console user: '{final_console}'")
    except Exception as e:
        test_logger.error(f"Could not get final user state: {e}")

# Command line options for tapping control
def pytest_addoption(parser):
    """Add command line options for tapping control."""
    options = [
        ("--no-tapping", "store_true", False, "Disable all tapping operations for local testing"),
        ("--tapping-debug", "store_true", False, "Enable debug logging for tapping operations")
    ]

    for option, action, default, help_text in options:
        parser.addoption(option, action=action, default=default, help=help_text)


@pytest.fixture(autouse=True)
def apply_tapping_options(request):
    """Apply tapping-specific command line options."""
    if request.config.getoption("--no-tapping"):
        os.environ["ENABLE_TAPPING"] = "false"

    if request.config.getoption("--tapping-debug"):
        _enable_tapping_debug_logging()


def _enable_tapping_debug_logging():
    """Enable debug logging for tapping-related loggers."""
    import logging
    tapping_loggers = ["login_tapper", "logoff_tapper", "tapping_manager"]
    for logger_name in tapping_loggers:
        logging.getLogger(logger_name).setLevel(logging.DEBUG)

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item):
    """Hook to capture test outcomes."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)