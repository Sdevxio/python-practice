"""
Simplified configuration fixtures.

Provides clean, simple configuration loading that integrates with our
enhanced fixture architecture. Reduces complexity while maintaining functionality.
"""
import os
import pytest
from test_framework.utils.loaders.station_loader import StationLoader


@pytest.fixture(scope="session")
def test_config():
    """
    Single simplified configuration fixture.
    
    Provides all essential test configuration with clean environment overrides:
    - Station and user settings
    - Timeout and retry settings  
    - Essential test data
    
    Environment variables:
    - TEST_STATION: Override station ID (default: station1)
    - TEST_USER: Override expected user (default: admin)
    - ENABLE_TAPPING: Enable tapping operations (default: false)
    """
    # Core settings with environment overrides
    station_id = os.environ.get("TEST_STATION", "station1")
    expected_user = os.environ.get("TEST_USER", "admin")
    enable_tapping = os.environ.get("ENABLE_TAPPING", "true").lower() == "true"
    
    # Try to load additional config if available
    log_file_path = "/Users/admin/PA/dynamic_log_generator/dynamic_test.log"
    try:
        station_loader = StationLoader()
        e2e_defaults = station_loader.get_e2e_defaults()
        if e2e_defaults and "log_file_path" in e2e_defaults:
            log_file_path = e2e_defaults["log_file_path"]
    except Exception:
        # Fallback to default if loader fails
        pass
    
    return {
        # Core identifiers
        "station_id": station_id,
        "expected_user": expected_user,
        
        # Operational settings
        "enable_tapping": enable_tapping,
        "login_timeout": 30,
        "tap_timeout": 10,
        
        # Test data paths
        "log_file_path": log_file_path,
        
        # Legacy compatibility (if needed by existing tests)
        "expected_card": "1234567890",
    }