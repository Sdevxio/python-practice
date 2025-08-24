import logging


class TestCaseFilter(logging.Filter):
    """
    A logging filter that adds the test case name to the log record.
    This is useful for filtering logs based on the test case name.
    """

    def __init__(self):
        super().__init__()
        self.test_case = None

    def filter(self, record: logging.LogRecord) -> bool | None:
        """
        Filter the log record to include the test case name.
        This method adds the test case name to the log record if it is set.

        :param record: The log record to filter.
        :return: True if the record should be logged, False otherwise.
        """

        if not hasattr(record, "test_case"):
            record.test_case = self.test_case or "N/A"

        return True


class EnhancedContextFilter(logging.Filter):
    """
    Filter that adds enhanced context to log records.
    This filter allows adding additional context information to log records.

    Attributes:
        test_case (str): Name of the test case.
        environment (str): Environment information.
        correlation_id (str): Correlation ID for tracking requests.
    """

    def __init__(self):
        super().__init__()
        self.test_case = None
        self.environment = None
        self.correlation_id = None

    def filter(self, record) -> bool:
        """
        Filter the log record to include enhanced context.
        Always return True and handle missing attributes gracefully

        :param record: The log record to filter.
        :return: True if the record should be logged, False otherwise.
        """
        try:
            # Add context attributes to the record
            if not hasattr(record, "test_case"):
                record.test_case = self.test_case or "N/A"
            if not hasattr(record, "environment"):
                record.environment = self.environment or "N/A"
            if not hasattr(record, "correlation_id"):
                record.correlation_id = self.correlation_id or "N/A"
        except Exception:
            record.test_case = "N/A"
            record.environment = "N/A"
            record.correlation_id = "N/A"

        return True