import time
from typing import Any


def logout_user(session_context: Any, grpc_manager: Any,
                expected_user: str,
                max_attempts: int = 3,
                verification_timeout: int = 15,
                retry_delay: float = 2.0,
                logger: Any = None) -> bool:
    """Logout user."""

    for attempt in range(max_attempts):
        try:
            if logger:
                logger.info(f" Attempting logout via applescript (attempt {attempt + 1} of {max_attempts})...")
            script_result = session_context.user_context.apple_script.logout_user(expected_user)
            if logger:
                logger.info(f"Applescript execution result: {script_result}")

            if script_result.get("success", False):
                if logger:
                    logger.debug(f"Script applescript logout executed: {script_result.get('output', 'No output')}")

                # Verify logout occurred
                if logger:
                    logger.info(f"Verifying logout for user: {expected_user}...")

                if _wait_for_console_user_change(grpc_manager, expected_user, verification_timeout, logger):
                    if logger:
                        logger.info(f"Logout verified successfully for user: {expected_user}")
                    return True
                else:
                    if logger:
                        logger.warning(f"Logout verification failed for attempt {attempt + 1}")
                    if attempt < max_attempts - 1:
                        if logger:
                            logger.error(f"Logout verification failed for user: {expected_user}")
                        time.sleep(retry_delay)
            else:
                if logger:
                    logger.error(f"Applescript logout failed: {script_result.get('error', 'Unknown error')}")
                if attempt < max_attempts - 1:
                    time.sleep(retry_delay)
        except Exception as e:
            if logger:
                logger.error(f"Logout attempt {attempt + 1} failed: {e}")
            if attempt < max_attempts - 1:
                time.sleep(retry_delay)

    if logger:
        logger.error(f"Logout failed for user: {expected_user}")
    return False


def _wait_for_console_user_change(grpc_manager: Any, expected_user: str, timeout: int, logger: Any) -> bool:
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            current_state = grpc_manager.get_logged_in_users()
            console_user = current_state.get("console_user", "")
            if console_user != expected_user:
                return True
            time.sleep(1)
        except Exception as e:
            if logger:
                logger.error(f"Logout verification failed: {e}")
            time.sleep(1)

    if logger:
        logger.warning(f"Timeout waiting for console user change from '{expected_user}' to a different user")

    return False
