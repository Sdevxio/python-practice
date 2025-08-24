"""
Simple real endpoint configuration fixture.

Reads actual macOS endpoint IPs and stations from existing YAML files
without adding complexity. Supports environment variable overrides.
"""

import os
import yaml
import pytest


@pytest.fixture(scope="session")
def real_endpoint_config():
    """
    Simple configuration that uses real macOS endpoints instead of localhost.
    
    Environment variables:
    - TARGET_STATION: station1, station2, station3 (default: station1)
    - TARGET_USER: admin, alaeddinekramou, etc. (default: admin)
    """
    # Get target station and user from environment
    target_station = os.environ.get("TARGET_STATION", "station1")
    target_user = os.environ.get("TARGET_USER", "admin")
    
    # Load station definitions
    try:
        stations_path = os.path.join(os.getcwd(), "test_framework", "configuration", 
                                   "stations", "station_definitions.yaml")
        with open(stations_path, 'r') as f:
            stations_config = yaml.safe_load(f)
    except Exception:
        # Fallback if file not found
        stations_config = {"stations": {target_station: {"endpoint": "mac-endpoint-01"}}}
    
    # Load endpoint definitions  
    try:
        endpoints_path = os.path.join(os.getcwd(), "test_framework", "configuration",
                                    "infrastructure", "macos_endpoints.yaml")
        with open(endpoints_path, 'r') as f:
            endpoints_config = yaml.safe_load(f)
    except Exception:
        # Fallback if file not found
        endpoints_config = {"endpoints": {"mac-endpoint-01": {"ip": "127.0.0.1"}}}
    
    # Get station info
    station_info = stations_config.get("stations", {}).get(target_station, {})
    endpoint_id = station_info.get("endpoint", "mac-endpoint-01")
    
    # Get endpoint info
    endpoint_info = endpoints_config.get("endpoints", {}).get(endpoint_id, {})
    endpoint_ip = endpoint_info.get("ip", "127.0.0.1")
    
    # Get port from defaults
    default_port = endpoints_config.get("defaults", {}).get("grpc-server", {}).get("port", 50051)
    
    return {
        "station_id": target_station,
        "expected_user": target_user,
        "endpoint_ip": endpoint_ip,
        "endpoint_port": default_port,
        "enable_tapping": os.environ.get("ENABLE_TAPPING", "false").lower() == "true",
        "login_timeout": 30,
        "tap_timeout": 10,
    }