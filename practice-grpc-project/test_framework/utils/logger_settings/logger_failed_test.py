import os
from datetime import datetime


class LoggerFailedTestHandler:
    """
    Handler that extracts test-specific logs for failed tests.
    This handler creates a separate log file for each failed test case.

    Attributes:
        failed_tests_dir (str): Directory where failed test logs are stored.
        main_log_file (str): Path to the main log file.
    """

    def __init__(self, failed_tests_dir: str, main_log_file: str):
        """
        Initialize the FailedTestLogHandler.

        :param failed_tests_dir: Directory where failed test logs are stored.
        :param main_log_file: Path to the main log file.
        """
        self.failed_tests_dir = failed_tests_dir
        self.main_log_file = main_log_file

    def create_log(self, test_name: str) -> str | None:
        """
        Extract logs for a specific test into a separate file.

        :param test_name: Name of the test case.
        :return: Path to the created log file or None if test_name is empty.

        Example:
            log_handler = FailedTestLogHandler('/path/to/failed_tests', '/path/to/main_log.log')
            log_path = log_handler.create_log('test_case_name')
            print(f"Log created at: {log_path}")
        """
        if not test_name:
            return None

        # Create a timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = os.path.join(
            self.failed_tests_dir,
            f"{test_name}_{timestamp}.log"
        )

        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(log_path), exist_ok=True)

            # Extract relevant log entries
            if os.path.exists(self.main_log_file):
                with open(self.main_log_file, 'r') as main_log:
                    with open(log_path, 'w') as failed_log:
                        for line in main_log:
                            if test_name in line:
                                failed_log.write(line)

                # Check if we got any content
                if os.path.getsize(log_path) < 10:
                    with open(log_path, 'a') as failed_log:
                        failed_log.write(f"Note: Test '{test_name}' failed, but no specific log entries were found.\n")
            else:
                # Create a file with error message if main log not found
                with open(log_path, 'w') as failed_log:
                    failed_log.write(f"Test '{test_name}' failed, but main log file not found.\n")

            return log_path

        except Exception as e:
            import sys
            print(f"Error creating failed test log: {e}", file=sys.stderr)
            return None

    def create_failure_log_with_details(self, test_name: str, details: str) -> str | None:
        """
        Create a separate failure log file containing provided exception details.

        :param test_name: Name of the test case.
        :param details: Exception traceback or failure text.
        :return: Path to the created log file or None if error.
        """
        if not test_name:
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = os.path.join(
            self.failed_tests_dir,
            f"{test_name}_{timestamp}.log"
        )

        try:
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write(details)
            return log_path
        except Exception as e:
            import sys
            print(f"Error writing failure log: {e}", file=sys.stderr)
            return None