
import logging
import time
from typing import Optional

from test_framework.utils import get_logger
from tappers_service.controller.tapper_service import TapperService
from tappers_service.command import sequences


class LogoutTapper:
    """
    Handles logoff tapping operations with mandatory verification.
    Features:
    - Logoff tap with retry logic
    - User logout verification
    - Configurable verification methods
    """

    def __init__(self, station_id: str, logger: Optional[logging.Logger] = None):
        self.station_id = station_id
        self.logger = logger or get_logger(f"logout_tapper_{station_id}")
        self.tapper_service = TapperService(station_id, logger)

    def perform_logoff_with_verification(self, 
                                       expected_user: str,
                                       grpc_session_manager,
                                       max_attempts: int = 3,
                                       retry_delay: float = 2.0,
                                       verification_timeout: int = 10) -> bool:
        """
        Perform logoff tap with mandatory user verification.
        
        :param expected_user: Username that should be logged out
        :param grpc_session_manager: GrpcSessionManager to check user state
        :param max_attempts: Maximum tap attempts
        :param retry_delay: Delay between attempts
        :param verification_timeout: Timeout for verification per attempt
        :return: True if logoff was successful and verified
        """
        self.logger.info(f"Starting verified logoff process for user '{expected_user}'")
        
        # Ensure tapper connection
        if not self.tapper_service.connect():
            self.logger.error("Failed to connect to tapper service")
            return False
        
        try:
            for attempt in range(max_attempts):
                self.logger.info(f"Logoff attempt {attempt + 1}/{max_attempts}")

                # Step 1: Perform the tap
                if not self._execute_single_logoff_tap():
                    self.logger.warning(f"Logoff tap failed on attempt {attempt + 1}")
                    if attempt < max_attempts - 1:
                        self.logger.info(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    continue

                # Step 2: Verify the logoff
                if self._wait_for_console_user_change(grpc_session_manager, expected_user, verification_timeout):
                    self.logger.info(f"Logoff verified successfully for user '{expected_user}'")
                    return True
                else:
                    self.logger.warning(f"Logoff verification failed on attempt {attempt + 1}")
                    if attempt < max_attempts - 1:
                        self.logger.info(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)

            self.logger.error(f"Failed to complete verified logoff after {max_attempts} attempts")
            return False
            
        finally:
            self.tapper_service.disconnect()

    def _execute_single_logoff_tap(self) -> bool:
        """
        Execute a single logout tap using the tapper service.
        
        :return: True if tap was executed successfully, False otherwise
        """
        try:
            self.logger.info("Executing logout tap")
            tapper_service = TapperService(self.station_id, self.station_id)
            if not tapper_service.connect():
                self.logger.error("Failed to connect to tapper service")
                return False

            # Use safe_simple_tap for logout - this ensures proper positioning
            sequences.safe_simple_tap(self.tapper_service.protocol)
            self.logger.info("Logout tap completed successfully")
            tapper_service.disconnect()
            return True
        except Exception as e:
            self.logger.error(f"Failed to execute logout tap: {e}")
            return False

    def _wait_for_console_user_change(self, grpc_session_manager, expected_user: str, timeout: int) -> bool:
        """
        Wait for console user to change from expected_user, indicating successful logout.
        
        :param grpc_session_manager: Manager to check session state
        :param expected_user: User that should be logged out
        :param timeout: Maximum time to wait for change in seconds
        :return: True if console user changed (logout confirmed), False otherwise
        """
        deadline = time.time() + timeout
        poll_interval = 1.0
        
        while time.time() < deadline:
            try:
                user_info = grpc_session_manager.get_logged_in_users()
                console_user = user_info.get("console_user", "")
                self.logger.debug(f"Current console user: '{console_user}'")

                if console_user != expected_user:
                    if console_user == "root" or console_user == "":
                        self.logger.info(f"Console user changed from '{expected_user}' to '{console_user}' - logout confirmed")
                        return True
                    else:
                        self.logger.info(f"Console user changed from '{expected_user}' to '{console_user}' - different user logged in")
                        return True
                else:
                    remaining_time = int(deadline - time.time())
                    self.logger.debug(f"Console user still '{expected_user}' - waiting for {remaining_time} seconds...")
                    
            except Exception as e:
                self.logger.error(f"Failed to check console user: {e}")
                return False

            time.sleep(poll_interval)

        # Final check for debugging
        try:
            user_info = grpc_session_manager.get_logged_in_users()
            final_user = user_info.get("console_user", "")
            self.logger.warning(f"Logout verification timed out after {timeout} seconds. Final user: '{final_user}'")
        except Exception as e:
            self.logger.error(f"Failed final user check: {e}")
            
        return False


