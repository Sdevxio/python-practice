import logging
from statistics import correlation

from test_framework.utils.logger_settings.logger_config import LoggerConfig
from test_framework.utils.logger_settings.logger_failed_test import LoggerFailedTestHandler
from test_framework.utils.logger_settings.logger_filter import EnhancedContextFilter
from  test_framework.utils.logger_settings.logger_rotating_file import ArchivingRotatingFileHandler


class LoggerManager:
    """
    Centralized manager for all test logging functionality.
    This class is a singleton, ensuring that only one instance exists throughout test framework.

    Attributes:
        _instance (LoggerManager): Singleton instance of LoggerManager.
        config (LogConfig): Configuration for logging.
        context_filter (EnhancedContextFilter): Filter to add enhanced context to log records.
        failed_test_handler (FailedTestLogHandler): Handler for failed test logs.
    """
    _instance = None

    def __new__(cls, config=None):
        """
        Create a new instance of LoggerManager or return the existing one.

        :param config: Configuration for logging.
        """
        if cls._instance is None:
            cls._instance = super(LoggerManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config=None):
        """
        Initialize the LoggerManager with the given configuration.
        If no configuration is provided, it will use the default configuration.

        :param config: Configuration for logging.
        """
        # Skip if already initialized
        if getattr(self, '_initialized', False):
            return

        # Initialize configuration
        self.config = config or LoggerConfig.initialize()

        # Create enhanced context filter
        self.context_filter = EnhancedContextFilter()

        # Set up logging system
        self._setup_logging()

        # Create handler for failed tests
        self.failed_test_handler = LoggerFailedTestHandler(
            self.config.FAILED_TESTS_DIR,
            self.config.MAIN_LOG_FILE
        )

        self._initialized = True

    def _setup_logging(self):
        """
        Configure the logging system.
        This method sets up the root logger, adds a console handler, and attaches the context filter.
        It also configures the file handler for logging to a file with rotation.
        """
        formatter = logging.Formatter(
            '%(asctime)s - %(test_case)s - %(environment)s - %(name)s - %(levelname)s - %(message)s'
        )

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)

        # Clear all existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Add enhanced context filter to root logger
        root_logger.addFilter(self.context_filter)

        # Apply filter to ALL existing loggers, including third-party ones
        def apply_filter_to_logger(logger_name, logger_obj):
            """Apply our context filter to any logger"""
            try:
                if isinstance(logger_obj, logging.Logger):
                    if not any(isinstance(f, EnhancedContextFilter) for f in logger_obj.filters):
                        logger_obj.addFilter(self.context_filter)
            except Exception:
                pass  # Ignore errors for problematic loggers

        # Apply to all existing loggers
        for name, logger in logging.root.manager.loggerDict.items():
            apply_filter_to_logger(name, logger)

        # Monkey patch getLogger to auto-apply filter to new loggers
        if not hasattr(logging, '_original_getLogger'):
            logging._original_getLogger = logging.getLogger

            def patched_getLogger(name=None):
                logger = logging._original_getLogger(name)
                try:
                    if not any(isinstance(f, EnhancedContextFilter) for f in logger.filters):
                        logger.addFilter(self.context_filter)
                except Exception:
                    pass  # Ignore errors
                return logger

            logging.getLogger = patched_getLogger

        # Console handler
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        console.setLevel(logging.INFO)
        root_logger.addHandler(console)

        # File handler
        file_handler = ArchivingRotatingFileHandler(
            self.config.MAIN_LOG_FILE,
            max_bytes=self.config.MAX_LOG_SIZE,
            backup_count=self.config.BACKUP_COUNT,
            archive_dir=self.config.ARCHIVED_LOGS_DIR
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)

    def get_logger(self, name: str = "test"):
        """
        Get a logger with the specified name.
        This method returns a logger instance that can be used for logging messages.

        :param name: The name of the logger.
        :return: A logger instance.
        """
        logger = logging.getLogger(name)

        # Ensure it has the enhanced context filter
        has_filter = any(isinstance(f, EnhancedContextFilter) for f in logger.filters)
        if not has_filter:
            logger.addFilter(self.context_filter)

        return logger

    def set_test_case(self, name: str):
        """
        Set the current test case name for all logs.
        This method updates the test case name in the context filter,
        ensuring that all subsequent log messages include the test case name.

        :param name: The name of the test case.
        """
        self.context_filter.test_case = name

    def set_environment(self, env_name: str):
        """
        Set the current environment name for all logs.
        This method updates the environment name in the context filter,
        ensuring that all subsequent log messages include the environment name.

        :param env_name: The name of the environment.
        """
        self.context_filter.environment = env_name

    def set_correlation_id(self, correlation_id: correlation):
        """
        Set the current correlation ID for all logs.
        This method updates the correlation ID in the context filter,
        ensuring that all subsequent log messages include the correlation ID.

        :param correlation_id: The correlation ID.
        """
        self.context_filter.correlation_id = correlation_id

    def create_failed_test_log(self, test_name: str):
        """
        Create a separate log file for a failed test.
        This method generates a log file specifically for a test that has failed,
        allowing for easier debugging and analysis of test failures.

        :param test_name: The name of the test that failed.
        """
        return self.failed_test_handler.create_log(test_name)