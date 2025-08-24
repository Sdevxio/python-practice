import os


class LoggerConfig:
    """
    A class to manage logging configuration for the logging system.
    This class is responsible for setting up the directory structure for logs and artifacts,
    and for initializing the logging settings.
    """

    @classmethod
    def initialize(cls, project_root: str = None):
        """
        Initialize the logger configuration.
        This method sets up the directory structure for logs and artifacts,
        and initializes the logging settings.

        :param project_root: The root directory of the project. If not provided,
                            it will be auto-detected based on the current file's location.
        :return: The class itself after initialization.
        """
        if hasattr(cls, "INITIALIZED") and cls.INITIALIZED:
            return cls

        # Auto-detect project root if not provided
        if not project_root:
            current_file = os.path.abspath(__file__)
            file_dir = os.path.dirname(current_file)
            if "test_framework" in file_dir:
                path_parts = file_dir.split(os.sep)
                tf_index = path_parts.index("test_framework")
                project_root = os.sep.join(path_parts[:tf_index])
            else:
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(file_dir)))

        cls.ARTIFACTS_DIR = os.path.join(project_root, 'artifacts')
        cls.DOWNLOADS_DIR = os.path.join(cls.ARTIFACTS_DIR, 'downloads')
        cls.LOG_DIR = os.path.join(cls.ARTIFACTS_DIR, 'logs')
        cls.FAILED_TESTS_DIR = os.path.join(cls.LOG_DIR, 'failed_tests')
        cls.ARCHIVED_LOGS_DIR = os.path.join(cls.LOG_DIR, 'archived')
        cls.MAIN_LOG_FILE = os.path.join(cls.LOG_DIR, 'test_run.log')

        # Create directories
        for directory in [
            cls.ARTIFACTS_DIR,
            cls.DOWNLOADS_DIR,
            cls.LOG_DIR,
            cls.FAILED_TESTS_DIR,
            cls.ARCHIVED_LOGS_DIR
        ]:
            os.makedirs(directory, exist_ok=True)

        # Log settings
        cls.LOG_FORMAT = '%(asctime)s - %(test_case)s - %(name)s - %(levelname)s - %(message)s'
        cls.MAX_LOG_SIZE = 50 * 1024 * 1024
        cls.BACKUP_COUNT = 5

        cls.INITIALIZED = True
        return cls