"""
Manual CAPTCHA Solver - User solves CAPTCHAs in the browser
"""

from typing import Optional
from playwright.sync_api import Page
import time

from utils.logger import setup_logger

logger = setup_logger(__name__)


class ManualCaptchaSolver:
    """
    Manual CAPTCHA solver - shows the browser and waits for user to solve
    """
    
    def __init__(self, timeout: int = 60):
        """
        Args:
            timeout: Max seconds to wait for user to solve CAPTCHA
        """
        self.timeout = timeout
        logger.info("✅ ManualCaptchaSolver initialized - YOU will solve CAPTCHAs")
    
    def solve_captcha(self, page: Page, image_bytes: bytes = None) -> Optional[str]:
        """
        Wait for user to manually solve the CAPTCHA in the browser
        
        Returns:
            The solved text (read from input field after user enters it)
        """
        try:
            logger.info("⏳ WAITING FOR YOU TO SOLVE CAPTCHA...")
            logger.info("   1. Look at the CAPTCHA image in the browser")
            logger.info("   2. Type the text you see in the input box")
            logger.info("   3. Press the Submit button")
            
            # Wait for the CAPTCHA to be filled and submitted
            # Check if input has value and Submit button was clicked
            start = time.time()
            captcha_input = page.locator("input#captcha")
            
            while time.time() - start < self.timeout:
                try:
                    # Check if CAPTCHA input has text
                    input_value = captcha_input.input_value(timeout=1000)
                    
                    if input_value and len(input_value) >= 4:
                        logger.info(f"✅ You entered: {input_value}")
                        
                        # Check if Submit button exists and click it
                        submit_btn = page.locator("button:has-text('Submit'), input[type='submit'][value*='Submit']")
                        if submit_btn.count() > 0:
                            logger.info("Clicking Submit button...")
                            submit_btn.first.click()
                            page.wait_for_timeout(2000)
                        
                        # Wait a bit to see if CAPTCHA disappears (success)
                        page.wait_for_timeout(3000)
                        
                        # Check if CAPTCHA is still visible
                        canvas = page.locator("canvas")
                        if canvas.count() == 0:
                            logger.info("✅ CAPTCHA solved successfully!")
                            return input_value
                        else:
                            logger.warning("CAPTCHA still visible - may be incorrect")
                            # Clear and try again
                            captcha_input.fill("")
                    
                except Exception:
                    pass
                
                time.sleep(1)
            
            logger.error(f"❌ Timeout after {self.timeout}s waiting for CAPTCHA solve")
            return None
            
        except Exception as e:
            logger.error(f"Manual CAPTCHA error: {e}")
            return None
