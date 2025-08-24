import logging
from typing import Optional, Callable

from test_framework.login_logout.tap_login import LoginTapper
from test_framework.login_logout.tap_logout import LogoutTapper
from test_framework.utils import get_logger


class TappingManager:

    def __init__(self, station_id: str, enable_tapping: bool, logger: Optional[logging.Logger] = None):
        """
        Initialize the tapping manager.
        
        :param station_id: Station identifier for tapper hardware
        :param logger: Optional logger instance
        """
        self.station_id = station_id
        self.enable_tapping = enable_tapping
        self.logger = logger or get_logger(f"tapping_manager_{station_id}")

        # Initialize component tappers
        self.login_tapper = LoginTapper(station_id, self.logger)
        self.logout_tapper = LogoutTapper(station_id, self.logger)

    def perform_login_tap(self, verification_callback: Optional[Callable] = None, **kwargs) -> bool:
        """
        Perform a login tap operation with optional verification.
        """
        if not self.enable_tapping:
            self.logger.info("Tapping is disabled. Skipping login tap.")
            return True
        return self.login_tapper.perform_login_tap(
            verification_callback=verification_callback,
            **kwargs)

    def perform_logoff_tap(self, expected_user: str, grpc_session_manager, **kwargs) -> bool:
        """
        Perform a logoff tap operation.
        """
        if not self.enable_tapping:
            self.logger.info("Tapping is disabled. Skipping logoff tap.")
            return True
        return self.logout_tapper.perform_logoff_with_verification(
            expected_user=expected_user,
            grpc_session_manager=grpc_session_manager,
            **kwargs)

    def is_enabled(self) -> bool:
        """Check if tapping is enabled."""
        return self.enable_tapping
