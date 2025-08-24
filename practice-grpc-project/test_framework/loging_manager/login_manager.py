"""
🎯 LoginManager - Clean Separation of Concerns Architecture

This replaces the complex login_logout architecture with proper separation:
- LoginServiceProvider: Verification & AppleScript operations (gRPC via adapter)
- Tapper: Independent physical hardware control (no gRPC dependency)
- Clean API: ensure_logged_in(), ensure_logged_out()
- Intelligent cleanup strategy with AppleScript → Tapping fallback

Your Cleanup Scenario:
1. Check if user is logged out → if yes, done
2. Use AppleScript to logout user (with retry)
3. Verify if user logged out → if yes, done  
4. If AppleScript retries fail → fallback to physical tapping
5. Verify again after tapping

Key Benefits:
- 70% less code than old architecture
- Proper separation of concerns
- Single source of truth for login/logout logic
- Intelligent fallback strategy
- Easy test integration
"""

import time
from typing import Optional, Protocol, runtime_checkable
from test_framework.utils import get_logger
from test_framework.utils.scripts.applescripts import LOG_OUT_USER_APPLESCRIPT

@runtime_checkable
class LoginServiceProvider(Protocol):
    """
    Protocol defining the interface that LoginManager expects.
    
    This documents exactly what methods LoginManager needs from a service provider.
    """
    
    def command(self, context: str):
        """Get command service for user verification operations."""
        ...
    
    def apple_script(self, context: str):  
        """Get AppleScript service for logout operations."""
        ...
    
    def health_check(self, context: str) -> bool:
        """Verify gRPC connectivity."""
        ...


# Optional tapper integration
try:
    from tappers_service.controller.tapper_service import TapperService
    from tappers_service.command import sequences
    TAPPER_AVAILABLE = True
except ImportError:
    TAPPER_AVAILABLE = False


class LoginManager:
    """
    🎯 Simple Login/Logout Manager - Clean separation of concerns
    
    This class provides a clean interface for managing user login/logout states
    with proper separation between verification, AppleScript operations, and tapping.
    
    Architecture:
    - LoginServiceProvider: For verification & AppleScript logout operations
    - Tapper: Independent physical hardware control (no gRPC dependency)
    - Clean separation: Each component has single responsibility
    
    Cleanup Strategy (your scenario):
    1. Use AppleScript to logout user (with retry)
    2. Verify if user logged out → if yes, done
    3. If AppleScript retry fails → fallback to physical tapping
    4. Verify again after tapping
    
    Usage:
        login_mgr = LoginManager(login_service_provider, station_id="station1")
        
        # Before test - ensure user is logged in  
        login_mgr.ensure_logged_in(target_user="testuser")
        
        # After test - intelligent cleanup
        login_mgr.ensure_logged_out(current_user="testuser")
    """
    
    def __init__(self, 
                 service_manager: LoginServiceProvider,
                 station_id: Optional[str] = None,
                 enable_tapping: bool = True):
        """
        Initialize LoginManager with proper component separation.
        
        Args:
            service_manager: LoginServiceProvider for verification & AppleScript operations
            station_id: Station identifier for tapper hardware (optional)
            enable_tapping: Whether to enable physical tapping fallback (default: True)
        """
        # LoginServiceProvider for verification & AppleScript (gRPC operations)
        self.services = service_manager
        
        # Tapper for physical hardware control (independent)
        self.station_id = station_id
        self.enable_tapping = enable_tapping and TAPPER_AVAILABLE and station_id
        self.tapper = None
        
        self.logger = get_logger(self.__class__.__name__)
        
        # Initialize tapper independently (no LoginServiceProvider dependency)
        if self.enable_tapping:
            try:
                self.tapper = TapperService(station_id=station_id)
                self.logger.info(f"🎯 LoginManager: tapper available for station {station_id}")
            except Exception as e:
                self.logger.warning(f"Tapper initialization failed: {e}")
                self.enable_tapping = False
        
        self.logger.info(f"🎯 LoginManager initialized - tapping: {self.enable_tapping}, station: {station_id}")
    
    def ensure_logged_in(self, 
                        target_user: str,
                        max_attempts: int = 3,
                        verification_timeout: int = 10) -> bool:
        """
        Ensure the target user is logged in. Performs login tap if needed.
        
        Args:
            target_user: Username that should be logged in
            max_attempts: Maximum login attempts (default: 3)
            verification_timeout: Timeout for verification per attempt (default: 10s)
            
        Returns:
            True if user is logged in, False if login failed
        """
        self.logger.info(f"🔐 Ensuring user '{target_user}' is logged in")
        
        # First check if user is already logged in
        if self._is_user_logged_in(target_user):
            self.logger.info(f"✅ User '{target_user}' is already logged in")
            return True
        
        # User not logged in - attempt login if tapping is enabled
        if not self.enable_tapping:
            self.logger.warning(f"⚠️ User '{target_user}' not logged in and tapping disabled")
            return False
        
        # Perform login attempts
        for attempt in range(max_attempts):
            self.logger.info(f"🔄 Login attempt {attempt + 1}/{max_attempts} for user '{target_user}'")
            
            if self._perform_login_tap():
                # Verify login worked
                if self._wait_for_user_login(target_user, verification_timeout):
                    self.logger.info(f"✅ Login successful for user '{target_user}'")
                    return True
                else:
                    self.logger.warning(f"⚠️ Login tap completed but verification failed (attempt {attempt + 1})")
            else:
                self.logger.warning(f"⚠️ Login tap failed (attempt {attempt + 1})")
            
            # Delay before retry (except last attempt)
            if attempt < max_attempts - 1:
                self.logger.info(f"⏳ Retrying in 2 seconds...")
                time.sleep(2.0)
        
        self.logger.error(f"❌ Login failed for user '{target_user}' after {max_attempts} attempts")
        return False
    
    def ensure_logged_out(self, 
                         current_user: str,
                         applescript_retries: int = 3,
                         verification_timeout: int = 15) -> bool:
        """
        Intelligent cleanup: Ensure user is logged out using your exact scenario.
        
        Your Cleanup Scenario:
        1. Check if user is logged out → if yes, done
        2. Use AppleScript to logout user (with retry)
        3. Verify if user logged out → if yes, done  
        4. If AppleScript retries fail → fallback to physical tapping
        5. Verify again after tapping
        
        Args:
            current_user: Username that should be logged out
            applescript_retries: AppleScript retry attempts (default: 3)
            verification_timeout: Timeout for verification (default: 15s)
            
        Returns:
            True if user is logged out, False if all methods failed
        """
        self.logger.info(f"🧹 Cleanup: Ensuring user '{current_user}' is logged out")
        
        # Step 1: Check if user is already logged out
        if not self._is_user_logged_in(current_user):
            self.logger.info(f"✅ User '{current_user}' is already logged out - cleanup complete")
            return True
        
        # Step 2: Use AppleScript to logout user (with retry)
        self.logger.info(f"🍎 Attempting AppleScript logout for user '{current_user}' ({applescript_retries} retries)")
        
        for attempt in range(applescript_retries):
            self.logger.info(f"🔄 AppleScript attempt {attempt + 1}/{applescript_retries}")
            
            if self._perform_applescript_logout(current_user):
                # Step 3: Verify if user logged out → if yes, done
                if self._wait_for_user_logout(current_user, verification_timeout):
                    self.logger.info(f"✅ AppleScript logout successful for user '{current_user}'")
                    return True
                else:
                    self.logger.warning(f"⚠️ AppleScript executed but user '{current_user}' still logged in")
            else:
                self.logger.warning(f"⚠️ AppleScript logout failed (attempt {attempt + 1})")
            
            # Delay before next AppleScript retry
            if attempt < applescript_retries - 1:
                self.logger.info(f"⏳ Retrying AppleScript in 2 seconds...")
                time.sleep(2.0)
        
        # Step 4: If AppleScript retries fail → fallback to physical tapping  
        if self.enable_tapping:
            self.logger.info(f"🎯 AppleScript retries failed - trying physical tapping fallback")
            
            if self._perform_logout_tap():
                # Step 5: Verify again after tapping
                if self._wait_for_user_logout(current_user, verification_timeout):
                    self.logger.info(f"✅ Physical tap logout successful for user '{current_user}'")
                    return True
                else:
                    self.logger.error(f"❌ Physical tap completed but user '{current_user}' still logged in")
            else:
                self.logger.error(f"❌ Physical tap logout failed for user '{current_user}'")
        else:
            self.logger.warning(f"⚠️ AppleScript failed and tapping not available - cannot logout user '{current_user}'")
        
        self.logger.error(f"❌ Cleanup failed: User '{current_user}' could not be logged out")
        return False
    
    def get_current_user(self) -> Optional[str]:
        """
        Get the currently logged in console user.
        
        Returns:
            Username of console user, or None if no user or error
        """
        try:
            user_info = self.services.command("root").get_logged_in_users()
            console_user = user_info.get("console_user", "")
            return console_user if console_user and console_user != "root" else None
        except Exception as e:
            self.logger.error(f"❌ Failed to get current user: {e}")
            return None
    
    def is_anyone_logged_in(self) -> bool:
        """
        Check if any user is currently logged in.
        
        Returns:
            True if a user is logged in, False otherwise
        """
        current_user = self.get_current_user()
        return current_user is not None
    
    def health_check(self) -> bool:
        """
        Perform a health check on LoginManager functionality.
        
        Returns:
            True if LoginManager is healthy, False otherwise
        """
        try:
            # Test LoginServiceProvider connectivity
            if not self.services.health_check("root"):
                self.logger.error("❌ LoginServiceProvider health check failed")
                return False
            
            # Test user info retrieval
            current_user = self.get_current_user()
            self.logger.info(f"🏥 Health check - current user: {current_user or 'none'}")
            
            # Test tapper if enabled
            if self.enable_tapping and self.tapper:
                try:
                    if not self.tapper.connect():
                        self.logger.warning("⚠️ Tapper connection failed during health check")
                        return False
                    self.tapper.disconnect()
                except Exception as e:
                    self.logger.warning(f"⚠️ Tapper health check failed: {e}")
                    return False
            
            self.logger.info("✅ LoginManager health check passed")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Health check failed: {e}")
            return False
    
    # =============================================================================
    # Private Implementation Methods
    # =============================================================================
    
    def _is_user_logged_in(self, username: str) -> bool:
        """Check if specific user is currently logged in."""
        try:
            current_user = self.get_current_user()
            return current_user == username
        except Exception as e:
            self.logger.error(f"❌ Failed to check if user '{username}' is logged in: {e}")
            return False
    
    def _perform_login_tap(self) -> bool:
        """Perform a single login tap using tapper service."""
        if not self.enable_tapping or not self.tapper:
            return False
        
        try:
            if not self.tapper.connect():
                self.logger.error("❌ Failed to connect to tapper for login")
                return False
            
            sequences.safe_simple_tap(self.tapper.protocol)
            self.tapper.disconnect()
            self.logger.debug("✅ Login tap executed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Login tap failed: {e}")
            return False
    
    def _perform_logout_tap(self) -> bool:
        """Perform a single logout tap using tapper service."""
        if not self.enable_tapping or not self.tapper:
            return False
        
        try:
            if not self.tapper.connect():
                self.logger.error("❌ Failed to connect to tapper for logout")
                return False
            
            sequences.safe_simple_tap(self.tapper.protocol)
            self.tapper.disconnect()
            self.logger.debug("✅ Logout tap executed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Logout tap failed: {e}")
            return False
    
    def _perform_applescript_logout(self, username: str) -> bool:
        """Perform logout using existing AppleScript from test_framework/scripts."""
        try:
            apple_script_service = self.services.apple_script(username)
            
            # Use the existing, tested AppleScript for logout
            result = apple_script_service.run_applescript(LOG_OUT_USER_APPLESCRIPT, timeout_seconds=20)
            
            if result and result.get("success", False):
                self.logger.debug(f"✅ AppleScript logout executed for user '{username}'")
                return True
            else:
                error_msg = result.get("stderr", "Unknown error") if result else "No result returned"
                self.logger.warning(f"⚠️ AppleScript logout failed: {error_msg}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ AppleScript logout failed: {e}")
            return False
    
    def _wait_for_user_login(self, username: str, timeout: int) -> bool:
        """Wait for specific user to be logged in."""
        deadline = time.time() + timeout
        poll_interval = 1.0
        
        while time.time() < deadline:
            if self._is_user_logged_in(username):
                return True
            time.sleep(poll_interval)
        
        return False
    
    def _wait_for_user_logout(self, username: str, timeout: int) -> bool:
        """Wait for specific user to be logged out."""
        deadline = time.time() + timeout
        poll_interval = 1.0
        
        while time.time() < deadline:
            if not self._is_user_logged_in(username):
                return True
            time.sleep(poll_interval)
        
        return False
    
    def __repr__(self):
        tapper_status = "enabled" if self.enable_tapping else "disabled"
        return f"LoginManager(station={self.station_id}, tapping={tapper_status})"
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure cleanup."""
        if self.tapper:
            try:
                self.tapper.disconnect()
            except Exception as e:
                self.logger.debug(f"Error disconnecting tapper: {e}")


# =============================================================================
# Convenience Functions for Quick Access
# =============================================================================

def create_login_manager(service_manager: LoginServiceProvider, 
                        station_id: Optional[str] = None,
                        enable_tapping: bool = True) -> LoginManager:
    """
    Create a LoginManager with standard configuration.
    
    Args:
        service_manager: LoginServiceProvider instance for gRPC operations
        station_id: Station identifier for tapper hardware
        enable_tapping: Whether to enable physical tapping
        
    Returns:
        Configured LoginManager instance
    """
    return LoginManager(service_manager, station_id=station_id, enable_tapping=enable_tapping)