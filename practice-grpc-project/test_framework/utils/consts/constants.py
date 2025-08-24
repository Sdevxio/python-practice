"""
Configuration constants
"""

# Config module settings
DEFAULT_CONFIG_NAME = "configs"
DEFAULT_CONFIG_MODULE = f"test_framework/{DEFAULT_CONFIG_NAME}"
FALLBACK_CONFIG_MODULES = []

# Supported file extensions
CONFIG_EXTENSIONS = ['.yaml', '.yml', '.json', '.ini']


# File encoding
DEFAULT_ENCODING = "utf-8"

# Error messages
ERROR_CONFIG_NOT_FOUND = "Config '{name}' not found in '{module}' or fallback modules: {fallbacks}"
ERROR_FILE_NOT_FOUND = "File not found: {path}"
ERROR_YAML_PARSE = "Error parsing YAML file: {path}"

# Tesseract OCR path
TESSERACT_OCR_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Remote log path for test_log.log on macOS
REMOTE_LOG_NAME = "test_log.log"
REMOTE_LOG_PATH = f"/Library/Logs/{REMOTE_LOG_NAME}"