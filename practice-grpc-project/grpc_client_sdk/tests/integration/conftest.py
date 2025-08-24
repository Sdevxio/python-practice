import datetime
import os

import pytest

from test_framework.utils import LoggerManager, set_test_case, get_logger
from test_framework.utils.loaders.station_loader import StationLoader
from test_framework.utils.logger_settings.logger_config import LoggerConfig

# Global run ID for the test session
RUN_ID = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


@pytest.fixture(scope="session", autouse=True)
def setup_logging():
    """
    Initialize logging with run ID and environment information.
    """
    LoggerConfig.initialize()
    log_manager = LoggerManager()
    environment = os.environ.get("TEST_ENVIRONMENT", "test")
    log_manager.set_environment(environment)
    pytest.run_id = RUN_ID
    return log_manager


@pytest.fixture
def setup(setup_logging):
    """Example fixture to get test station config."""
    stations = (StationLoader()
                .get_station_endpoint("station1" , "grpc"))
    yield stations


@pytest.fixture(scope="function")
def test_logger(request, setup_logging):
    """
    Fixture that provides a logger configured with the test name.
    """
    test_name = request.node.name
    set_test_case(test_name)
    logger = get_logger(f"test_{test_name}")
    correlation_id = f"test_{RUN_ID[:8]}"
    setup_logging.set_correlation_id(correlation_id)
    logger.info(f"Starting test: {test_name}")

    yield logger
    passed = True
    if hasattr(request.node, 'rep_call'):
        passed = not request.node.rep_call.failed
    if passed:
        logger.info(f"Test passed: {test_name}")
    else:
        logger.error(f"Test failed: {test_name}")


def get_grpc_target(station_name: str):
    """Get gRPC target for station (backwards compatibility)"""
    return