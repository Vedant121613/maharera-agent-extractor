"""
Local CAPTCHA solver using Tesseract OCR + OpenCV preprocessing.
Multiple strategies to improve accuracy.
"""

import re
from typing import Optional

try:
    import pytesseract
    from PIL import Image
    import numpy as np
    import cv2
    DEPS_OK = True
except ImportError:
    DEPS_OK = False

from config.config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)


class LocalCaptchaSolver:
    """
    Solves text CAPTCHAs using Tesseract OCR with preprocessing.
    """

    def __init__(self) -> None:
        if not DEPS_OK:
            raise ImportError(
                "Missing dependencies: pip install pytesseract pillow opencv-python-headless"
            )
        if Config.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = Config.TESSERACT_CMD

    def solve_captcha(self, image_bytes: bytes) -> Optional[str]:
        """
        Solve CAPTCHA using Tesseract with multiple preprocessing strategies.
        Returns alphanumeric text (letters + numbers).
        """
        try:
            logger.debug(f">>> solve_captcha called with {len(image_bytes)} bytes")
            img = self._decode(image_bytes)
            if img is None:
                logger.error("Failed to decode image")
                return None
            
            logger.debug(f"Image decoded successfully: shape={img.shape}")

            # Try multiple preprocessing strategies
            strategies = [
                ("grayscale", self._preprocess_grayscale),
                ("threshold", self._preprocess_threshold),
                ("adaptive", self._preprocess_adaptive),
                ("morphology", self._preprocess_morphology),
            ]

            for idx, (name, preprocess_fn) in enumerate(strategies, 1):
                try:
                    logger.debug(f"Strategy {idx}/4: '{name}' - preprocessing...")
                    prepared = preprocess_fn(img)
                    logger.debug(f"Strategy '{name}' - preprocessed shape: {prepared.shape}")
                    
                    logger.debug(f"Strategy '{name}' - running Tesseract OCR...")
                    text = self._ocr_digits(prepared)
                    logger.debug(f"Strategy '{name}' → Tesseract result: '{text}' (length={len(text)})")
                    
                    if text and len(text) >= 4:  # Accept 4+ characters (typical CAPTCHA length)
                        logger.info(f"✅ CAPTCHA solved [{name}]: '{text}'")
                        return text
                    elif text:
                        logger.debug(f"Result '{text}' too short (length={len(text)})")
                    else:
                        logger.debug(f"Strategy '{name}' returned empty string")
                        
                except Exception as e:
                    logger.warning(f"Strategy '{name}' error: {type(e).__name__}: {e}")

            logger.warning("❌ All Tesseract strategies failed to extract valid text")
            return None

        except Exception as exc:
            logger.error(f"Local OCR error: {type(exc).__name__}: {exc}", exc_info=True)
            return None

    @staticmethod
    def _decode(image_bytes: bytes) -> Optional[np.ndarray]:
        """Decode bytes to OpenCV image."""
        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        return img

    @staticmethod
    def _upscale(img: np.ndarray, scale: int = 3) -> np.ndarray:
        """Upscale image for better OCR."""
        h, w = img.shape[:2]
        return cv2.resize(img, (w * scale, h * scale), interpolation=cv2.INTER_CUBIC)

    def _ocr_digits(self, image: np.ndarray) -> str:
        """Run Tesseract OCR and extract alphanumeric characters."""
        try:
            # Convert to PIL Image
            pil_img = Image.fromarray(image)
            
            # Run Tesseract with custom config for alphanumeric (letters + numbers)
            custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            logger.debug(f"Running Tesseract with config: {custom_config}")
            
            raw_text = pytesseract.image_to_string(pil_img, config=custom_config)
            logger.debug(f"Tesseract raw output: '{raw_text}'")
            
            # Extract alphanumeric only (remove spaces, newlines, etc.)
            cleaned = ''.join(c for c in raw_text if c.isalnum()).upper()
            logger.debug(f"Extracted alphanumeric: '{cleaned}'")
            
            return cleaned
        except Exception as e:
            logger.error(f"Tesseract error: {type(e).__name__}: {e}", exc_info=True)
            return ""

    def _preprocess_grayscale(self, img: np.ndarray) -> np.ndarray:
        """Simple grayscale + upscale."""
        big = self._upscale(img)
        gray = cv2.cvtColor(big, cv2.COLOR_BGR2GRAY)
        return gray

    def _preprocess_threshold(self, img: np.ndarray) -> np.ndarray:
        """Binary threshold."""
        big = self._upscale(img)
        gray = cv2.cvtColor(big, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        return binary

    def _preprocess_adaptive(self, img: np.ndarray) -> np.ndarray:
        """Adaptive threshold."""
        big = self._upscale(img)
        gray = cv2.cvtColor(big, cv2.COLOR_BGR2GRAY)
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        return binary

    def _preprocess_morphology(self, img: np.ndarray) -> np.ndarray:
        """Morphological operations to clean up."""
        big = self._upscale(img)
        gray = cv2.cvtColor(big, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        
        # Remove noise
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        
        return cleaned
