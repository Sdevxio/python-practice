import os
from typing import Union

from test_framework.utils import get_logger
from test_framework.utils.logger_settings.logger_config import LoggerConfig


def save_to_artifacts(content: Union[bytes, str], filename: str, subfolder: str = "downloads") -> str:
    """
    Save content to the artifacts' directory.
    This function handles both bytes and string content types.

    :param content: File content (bytes or string)
    :param filename: Name of the file to save
    :param subfolder: Subfolder within artifacts directory (default: "downloads")
    :return: str: Full path to the saved file
    """

    logger = get_logger("file_utils")

    # Use the run-specific artifacts directory
    target_dir = os.path.join(LoggerConfig.ARTIFACTS_DIR, subfolder)

    # Create directory if it doesn't exist
    os.makedirs(target_dir, exist_ok=True)

    # Create full file path
    file_path = os.path.join(target_dir, filename)

    # Save content based on type
    try:
        if isinstance(content, bytes):
            with open(file_path, 'wb') as f:
                f.write(content)
        else:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        logger.info(f"Saved file to {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Failed to save file {filename}: {e}")
        raise