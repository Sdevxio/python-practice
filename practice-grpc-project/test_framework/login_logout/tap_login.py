import logging
import time
from typing import Optional

from tappers_service.controller.tapper_service import TapperService
from tappers_service.command import sequences
from test_framework.utils import get_logger


class LoginTapper:
    """Login tapper."""

    def __init__(self, station_id: str, logger: Optional[logging.Logger] = None):
        self.station_id = station_id
        self.logger = logger or get_logger(f"login_tapper [{station_id}]")

    def perform_login_tap(self,
                          max_retries: int = 3,
                          retry_delay:float=1.0,
                          verification_callback: Optional[callable] = None,
                          verification_timeout: int = 10)-> bool:
        """Perform login tap."""
        self.logger.info(f"Starting login tap process (max attempts: {max_retries})")
        for attempt in range(max_retries):
            self.logger.info(f"Login tap attempt {attempt + 1} of {max_retries}")
            # Step 1: Perform the tap
            if not self._execution_single_tap():
                self.logger.warning(f"Tap execution failed on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                continue

            # Step 2: Optional verification (if callback provided)
            if verification_callback:
                self.logger.info(f"Verification login tap success ...")
                try:
                    if self._verification_callback(verification_callback,verification_timeout):
                        self.logger.info("Login tap verified successfully")
                        return True
                    else:
                        self.logger.warning(f"Login tap verification failed on attempt {attempt + 1}")
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                        continue
                except Exception as e:
                    self.logger.warning(f"Login tap verification failed on attempt {attempt + 1}: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                    continue
            else:
                # No verification requested -tap execution success is sufficient
                self.logger.info(f"Login tap verified successfully")
                return True
        self.logger.error(f"All {max_retries} login tap attempts failed")
        return False


    def _execution_single_tap(self)-> bool:
        try:
            tapper_service = TapperService(station_id=self.station_id)
            if not tapper_service.connect():
                return False

            sequences.safe_simple_tap(tapper_service.protocol)
            self.logger.info("Login tap executed successfully")
            return True
        except Exception as e:
            self.logger.error(f"Login tap execution failed: {e}")
            return False

    def _verification_callback(self, verification_callback: callable, verification_timeout: int)-> bool:
        """Verify login tap."""
        try:
            return verification_callback(verification_timeout)
        except Exception as e:
            self.logger.error(f"Login tap verification failed: {e}")
            return False