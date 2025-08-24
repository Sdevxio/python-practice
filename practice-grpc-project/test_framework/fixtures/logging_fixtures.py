"""
Logging component fixtures.

These fixtures provide logging infrastructure components that are shared globally:
- Test logger with correlation IDs
- Log management and setup
- Environment-specific logging configuration
"""
import datetime
import os

import pytest

from test_framework.utils import set_test_case, get_logger, LoggerManager
from test_framework.utils.logger_settings.logger_config import LoggerConfig

# Global run ID for the test session
RUN_ID = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


@pytest.fixture(scope="session", autouse=True)
def setup_logging():
    """
    Global logging setup component.

    Initializes the logging infrastructure for the entire test session.
    This is automatically used by all tests and provides the foundation
    for all logging operations.
    """
    LoggerConfig.initialize()
    log_manager = LoggerManager()
    environment = os.environ.get("TEST_ENVIRONMENT", "test")
    log_manager.set_environment(environment)
    pytest.run_id = RUN_ID
    return log_manager


@pytest.fixture(scope="function")
def test_logger(request, setup_logging):
    """
    Test-specific logger component.

    Provides a logger configured with:
    - Test name in the logger name
    - Correlation ID for tracking
    - Automatic test result logging
    - Proper test lifecycle logging
    """
    test_name = request.node.name
    set_test_case(test_name)
    logger = get_logger(f"{test_name}")
    correlation_id = f"{RUN_ID[:8]}"
    setup_logging.set_correlation_id(correlation_id)
    logger.info(f"{'=' * 30} START TEST: {test_name}")

    yield logger

    # Log test result based on test outcome
    passed = True
    if hasattr(request.node, 'rep_call'):
        passed = not request.node.rep_call.failed
    if passed:
        logger.info(f"âœ“ Test passed: {test_name}")
    else:
        logger.error(f"âœ— Test failed: {test_name}")


@pytest.fixture(scope="function")
def debug_logger(test_logger):
    """
    Debug logger component.

    Provides enhanced debug logging capabilities.
    Useful for troubleshooting and detailed test analysis.
    """
    import logging
    debug_logger = get_logger(f"debug_{test_logger.name}")
    debug_logger.setLevel(logging.DEBUG)
    return debug_logger