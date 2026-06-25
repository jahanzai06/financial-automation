import logging
from typing import Union, Optional
from PIL import Image, ImageGrab
import pyperclip

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_clipboard_data() -> Optional[Union[Image.Image, str]]:
    """
    Checks the system clipboard.
    First tries to retrieve an image.
    If no image is found, retrieves text.
    Returns None if the clipboard is empty or unsupported.
    """
    try:
        # 1. Try to extract image from clipboard
        image = ImageGrab.grabclipboard()
        if image is not None:
            # ImageGrab.grabclipboard() can return a list of file paths (when copying files in Explorer)
            # or a PIL Image object when copying an actual image
            if isinstance(image, Image.Image):
                logger.info("Successfully extracted image from clipboard.")
                return image
            elif isinstance(image, list) and len(image) > 0:
                # If a list of file paths is returned, let's try to open the first file as an image
                try:
                    file_path = image[0]
                    img = Image.open(file_path)
                    logger.info(f"Successfully opened copied image file: {file_path}")
                    return img
                except Exception as ex:
                    logger.warning(f"Clipboard contained files, but could not open first file as image: {ex}")

        # 2. Try to extract text from clipboard
        text = pyperclip.paste()
        if text and text.strip():
            logger.info("Successfully extracted text from clipboard.")
            return text.strip()
            
    except Exception as e:
        logger.error(f"Error extracting data from clipboard: {e}")
        
    return None
