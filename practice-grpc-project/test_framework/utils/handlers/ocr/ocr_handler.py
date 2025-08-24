import logging

import pytesseract
from PIL import Image

from client_framework.test_framework.utils.consts.constants import TESSERACT_OCR_PATH
from client_framework.test_framework.utils.logger_settings.logger_manager import LoggerManager

logger = LoggerManager().get_logger("").setLevel(logging.INFO)


def extract_text_from_image(image_path: str) -> str:
    """
    Extracts text from a screenshot using OCR (Tesseract).

    :param image_path: Path to the saved image file.
    :return: str: Text extracted from the image.

    Usage:
        extracted_text = extract_text_from_image("path/to/image.png")
        print(extracted_text)
    """
    try:
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_OCR_PATH
        image = Image.open(image_path).convert("L")
        extracted_text = pytesseract.image_to_string(image)
        return extracted_text.strip()
    except Exception as e:
        raise RuntimeError(f"OCR extraction failed: {e}")