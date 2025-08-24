from test_framework.utils import LoggerManager

_logger_manager = LoggerManager()

# Export public functions
get_logger = _logger_manager.get_logger
set_test_case = _logger_manager.set_test_case
create_failed_test_log = _logger_manager.create_failed_test_log
