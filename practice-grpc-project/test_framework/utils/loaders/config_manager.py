# ==================================================
# 1. UPDATE: configuration_manager.py
# ==================================================

"""
Updated Configuration Manager with Singleton Pattern

This eliminates duplicate instantiations and reduces logging noise.
"""

import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Optional

from test_framework.utils import get_logger
from test_framework.utils.loaders.yaml_loader import YamlLoader


@dataclass
class StationConfig:
    """Complete station configuration with all resolved references."""
    station_id: str
    name: str
    description: str
    endpoint_config: Dict[str, Any]
    tapper_config: Dict[str, Any]
    enabled_protocols: List[str]
    primary_protocol: str
    protocol_configs: Dict[str, Any]
    overrides: Dict[str, Any]
    status: str


class ConfigurationManager:
    """
    Singleton Configuration Manager to prevent duplicate loading.

    Uses thread-safe singleton pattern to ensure only one instance
    exists across the entire application lifecycle.
    """

    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls, config_root: Optional[str] = None):
        """Thread-safe singleton implementation."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ConfigurationManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, config_root: Optional[str] = None):
        """Initialize only once, subsequent calls are ignored."""
        if ConfigurationManager._initialized:
            return

        with ConfigurationManager._lock:
            if ConfigurationManager._initialized:
                return

            self.logger = get_logger("ConfigurationManager")

            # Auto-detect config root if not provided (only log once)
            if config_root is None:
                config_root = self._auto_detect_config_root()
            else:
                config_root = Path(config_root)

            self.config_root = config_root
            self.logger.debug(f"Configuration system initialized: {self.config_root}")

            self._config_cache = {}
            self._loaders = {}
            self._initialize_loaders()

            ConfigurationManager._initialized = True

    def _auto_detect_config_root(self) -> Path:
        """Auto-detect config root (only called once)."""
        current_file = Path(__file__).resolve()

        # Try to find test_framework directory
        for parent in current_file.parents:
            if parent.name == "test_framework":
                return parent / "configuration"
            potential_config = parent / "test_framework" / "configuration"
            if potential_config.exists():
                return potential_config

        # Fallback: look for configs directory in current working directory
        cwd = Path.cwd()
        potential_configs = [
            cwd / "test_framework" / "configuration",
            cwd / "configuration",
        ]
        for potential in potential_configs:
            if potential.exists():
                return potential

        # Final fallback
        fallback = Path.cwd() / "test_framework" / "configuration"
        self.logger.warning(f"Could not auto-detect config path. Using fallback: {fallback}")
        return fallback

    def _initialize_loaders(self):
        """Initialize YAML loaders for each configuration file."""
        config_files = {
            "endpoints": self.config_root / "infrastructure" / "macos_endpoints.yaml",
            "tappers": self.config_root / "infrastructure" / "tapper_devices.yaml",
            "stations": self.config_root / "stations" / "station_definitions.yaml",
            "test_config": self.config_root / "test_config.yaml",
        }

        for config_name, config_path in config_files.items():
            if config_path.exists():
                self._loaders[config_name] = YamlLoader(config_path)
                self.logger.debug(f"Initialized loader for {config_name}")
            else:
                self.logger.warning(f"Config file not found: {config_path}")

    def get_station_config(self, station_id: str) -> StationConfig:
        """
        Get complete station configuration with caching.
        Only logs station config building on cache miss.
        """
        # Check cache first
        cache_key = f"station_{station_id}"
        if cache_key in self._config_cache:
            self.logger.debug(f"Using cached config for station: {station_id}")
            return self._config_cache[cache_key]

        # Only log when actually building (cache miss)
        self.logger.debug(f"Building station config for: {station_id}")

        # Build station config (existing logic remains the same)
        station_def = self._get_station_definition(station_id)
        endpoint_id = station_def.get("endpoint")
        if not endpoint_id:
            raise KeyError(f"Station '{station_id}' missing 'endpoint' reference")

        endpoint_config = self._get_endpoint_config(endpoint_id)
        tapper_id = station_def.get("tapper") or station_def.get("tapper_device")
        if not tapper_id:
            raise KeyError(f"Station '{station_id}' missing 'tapper' or 'tapper_device' reference")

        tapper_config = self._get_tapper_config(tapper_id)
        enabled_protocols = station_def.get("enabled_protocols", [])
        protocol_configs = self._build_protocol_configs(enabled_protocols, endpoint_config, tapper_config)
        overrides = self._get_station_overrides(station_id)
        protocol_configs = self._apply_protocol_overrides(protocol_configs, overrides)

        station_config = StationConfig(
            station_id=station_id,
            name=station_def.get("name", f"Station {station_id}"),
            description=station_def.get("description", ""),
            endpoint_config=endpoint_config,
            tapper_config=tapper_config,
            enabled_protocols=enabled_protocols,
            primary_protocol=station_def.get("primary_protocol", enabled_protocols[0] if enabled_protocols else ""),
            protocol_configs=protocol_configs,
            overrides=overrides,
            status=station_def.get("status", "active")
        )

        # Cache the result
        self._config_cache[cache_key] = station_config

        # Only log on cache miss, not every access
        self.logger.debug(f"Cached station config for {station_id}: protocols={enabled_protocols}")
        return station_config

    def get_legacy_station_config(self, station_id: str) -> Dict[str, Any]:
        """
        Get station configuration in legacy format for backward compatibility.

        This method provides the same structure as the old StationLoader
        to maintain compatibility with existing code.

        Args:
            station_id: ID of the station.

        Returns:
            Dict containing station config in legacy format.
        """
        station_config = self.get_station_config(station_id)

        # Build legacy format
        legacy_config = {
            "name": station_config.name,
            "device_id": station_config.tapper_config["device_id"],
            "grpc": {
                "host": station_config.endpoint_config["ip"],
                "port": station_config.endpoint_config["grpc"]["port"],
                "fallback_ports": station_config.endpoint_config["grpc"]["fallback_ports"]
            }
        }

        # Add protocol configurations
        for protocol in station_config.enabled_protocols:
            if protocol in station_config.protocol_configs:
                legacy_config[protocol] = station_config.protocol_configs[protocol]

        return legacy_config

    def get_test_config(self) -> Dict[str, Any]:
        """Get complete test configuration."""
        if "test_config" not in self._loaders:
            raise FileNotFoundError("Test configuration not found")

        return self._loaders["test_config"].get_all()

    def get_test_users(self) -> Dict[str, Any]:
        """Get all test user configurations."""
        test_config = self.get_test_config()
        return test_config.get("users", {})  # Changed from "test_users" to "users"

    def get_test_cards(self) -> Dict[str, Any]:
        """Get all test card configurations."""
        test_config = self.get_test_config()
        return test_config.get("cards", {})  # Changed from "test_cards" to "cards"

    def get_station_groups(self) -> Dict[str, Any]:
        """Get station group configurations."""
        test_config = self.get_test_config()
        return test_config.get("station_groups", {})

    def get_test_suites(self) -> Dict[str, Any]:
        """Get test suite configurations."""
        test_config = self.get_test_config()
        return test_config.get("test_suites", {})

    def get_e2e_defaults(self) -> Dict[str, Any]:
        """Get E2E test default configurations."""
        test_config = self.get_test_config()
        # Handle nested structure in your config
        test_suites = test_config.get("test_suites", {})
        return test_suites.get("e2e_test_defaults", {})

    def get_environment_multipliers(self) -> Dict[str, Any]:
        """Get environment-specific timeout multipliers."""
        test_config = self.get_test_config()
        return test_config.get("environment_multipliers", {})

    def get_test_suite_config(self, suite_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific test suite.

        Args:
            suite_name: Name of the test suite.

        Returns:
            Dict containing suite configuration.
        """
        test_suites = self.get_test_suites()
        if suite_name not in test_suites:
            available = list(test_suites.keys())
            raise KeyError(f"Test suite '{suite_name}' not found. Available: {available}")

        return test_suites[suite_name]

    def get_stations_for_suite(self, suite_name: str) -> List[str]:
        """
        Get list of stations for a test suite.

        Handles both station_group and station_id configurations.

        Args:
            suite_name: Name of the test suite.

        Returns:
            List of station IDs for the suite.
        """
        suite_config = self.get_test_suite_config(suite_name)

        # Check for direct station_id override
        if "station_id" in suite_config:
            return [suite_config["station_id"]]

        # Use station_group
        station_group_name = suite_config.get("station_group")
        if not station_group_name:
            raise KeyError(f"Test suite '{suite_name}' has no station_group or station_id")

        station_groups = self.get_station_groups()
        if station_group_name not in station_groups:
            available = list(station_groups.keys())
            raise KeyError(f"Station group '{station_group_name}' not found. Available: {available}")

        group_config = station_groups[station_group_name]
        stations = group_config.get("stations", [])

        # Apply station_selection logic
        station_selection = suite_config.get("station_selection", "all")
        if station_selection == "any_one":
            return stations[:1] if stations else []
        elif station_selection == "all":
            return stations
        else:
            # Assume station_selection is a specific station name
            return [station_selection] if station_selection in stations else []

    def list_stations(self) -> List[str]:
        """Get list of all configured station IDs."""
        if "stations" not in self._loaders:
            return []

        stations = self._loaders["stations"].get("stations", {})
        return list(stations.keys())

    def list_endpoints(self) -> List[str]:
        """Get list of all configured endpoint IDs."""
        if "endpoints" not in self._loaders:
            return []

        endpoints = self._loaders["endpoints"].get("endpoints", {})
        return list(endpoints.keys())

    def list_tappers(self) -> List[str]:
        """Get list of all configured tapper IDs."""
        if "tappers" not in self._loaders:
            return []

        # Handle both "tappers" and "tapper_devices" keys
        tapper_data = self._loaders["tappers"].get("tappers") or self._loaders["tappers"].get("tapper_devices")
        if not tapper_data:
            return []

        return list(tapper_data.keys())

    def _get_station_definition(self, station_id: str) -> Dict[str, Any]:
        """Get station definition from configuration."""
        if "stations" not in self._loaders:
            raise FileNotFoundError("Station definitions configuration not found")

        stations = self._loaders["stations"].get("stations", {})
        if station_id not in stations:
            available = list(stations.keys())
            raise KeyError(f"Station '{station_id}' not found. Available: {available}")

        return stations[station_id]

    def _get_endpoint_config(self, endpoint_id: str) -> Dict[str, Any]:
        """Get endpoint configuration by ID with defaults applied."""
        if "endpoints" not in self._loaders:
            raise FileNotFoundError("Endpoints configuration not found")

        # Get endpoint data
        endpoints = self._loaders["endpoints"].get("endpoints", {})
        if endpoint_id not in endpoints:
            available = list(endpoints.keys())
            raise KeyError(f"Endpoint '{endpoint_id}' not found. Available: {available}")

        endpoint_config = endpoints[endpoint_id].copy()

        # Apply defaults if gRPC config is not specified
        if "grpc-server" not in endpoint_config:
            defaults = self._loaders["endpoints"].get("defaults", {})
            if "grpc-server" in defaults:
                endpoint_config["grpc-server"] = defaults["grpc-server"].copy()

        # Normalize grpc-server to grpc for compatibility
        if "grpc-server" in endpoint_config:
            endpoint_config["grpc"] = endpoint_config["grpc-server"]

        return endpoint_config

    def _get_tapper_config(self, tapper_id: str) -> Dict[str, Any]:
        """Get tapper configuration by ID with defaults applied."""
        if "tappers" not in self._loaders:
            raise FileNotFoundError("Tappers configuration not found")

        # Get tapper data (handle both "tappers" and "tapper_devices")
        tapper_data = self._loaders["tappers"].get("tappers") or self._loaders["tappers"].get("tapper_devices")
        if not tapper_data or tapper_id not in tapper_data:
            available = list(tapper_data.keys()) if tapper_data else []
            raise KeyError(f"Tapper '{tapper_id}' not found. Available: {available}")

        tapper_config = tapper_data[tapper_id].copy()

        # Get defaults
        defaults = self._loaders["tappers"].get("defaults", {})

        # Build protocol configs if not already present
        if "protocols" not in tapper_config:
            # Determine which protocols this tapper supports
            protocols = tapper_config.get("protocols", ["http", "mqtt"])  # Default to both
            if isinstance(protocols, list):
                # Protocols specified as list, build configs
                tapper_config["protocols"] = {}

                for protocol in protocols:
                    if protocol == "http" and "http_url" in tapper_config:
                        http_config = defaults.get("http", {}).copy()
                        http_config["base_url"] = tapper_config["http_url"]
                        # Apply any http_override
                        if "http_override" in tapper_config:
                            http_config.update(tapper_config["http_override"])
                        tapper_config["protocols"]["http"] = http_config

                    elif protocol == "mqtt":
                        mqtt_config = defaults.get("mqtt", {}).copy()
                        # Generate MQTT topics using device_id
                        if "device_id" in tapper_config:
                            device_id = tapper_config["device_id"]
                            mqtt_config.update({
                                "command_topic": f"tappers/{device_id}/command",
                                "status_topic": f"tappers/{device_id}/status",
                                "device_id": device_id
                            })
                        # Apply any mqtt_override
                        if "mqtt_override" in tapper_config:
                            mqtt_config.update(tapper_config["mqtt_override"])
                        tapper_config["protocols"]["mqtt"] = mqtt_config
            else:
                # Handle case where protocols is not explicitly set but http_url exists
                tapper_config["protocols"] = {}

                # Add HTTP if http_url is present
                if "http_url" in tapper_config:
                    http_config = defaults.get("http", {}).copy()
                    http_config["base_url"] = tapper_config["http_url"]
                    if "http_override" in tapper_config:
                        http_config.update(tapper_config["http_override"])
                    tapper_config["protocols"]["http"] = http_config

                # Add MQTT by default unless explicitly disabled
                mqtt_config = defaults.get("mqtt", {}).copy()
                if "device_id" in tapper_config:
                    device_id = tapper_config["device_id"]
                    mqtt_config.update({
                        "command_topic": f"tappers/{device_id}/command",
                        "status_topic": f"tappers/{device_id}/status",
                        "device_id": device_id
                    })
                if "mqtt_override" in tapper_config:
                    mqtt_config.update(tapper_config["mqtt_override"])
                tapper_config["protocols"]["mqtt"] = mqtt_config

        return tapper_config

    def _build_protocol_configs(self, enabled_protocols: List[str], endpoint_config: Dict[str, Any],
                                tapper_config: Dict[str, Any]) -> Dict[str, Any]:
        """Build protocol configurations for enabled protocols."""
        protocol_configs = {}

        # Get the protocols from tapper config
        tapper_protocols = tapper_config.get("protocols", {})

        for protocol in enabled_protocols:
            if protocol == "http":
                # Check if protocols is a dict and has http config
                if isinstance(tapper_protocols, dict) and protocol in tapper_protocols:
                    protocol_configs["http"] = tapper_protocols["http"].copy()
                # Check if protocols is a list containing http, or if http_url exists
                elif (isinstance(tapper_protocols,
                                 list) and protocol in tapper_protocols) or "http_url" in tapper_config:
                    # Build HTTP config from defaults and tapper_config
                    defaults = self._loaders.get("tappers", {}).get("defaults", {})
                    http_config = defaults.get("http", {}).copy()

                    # Use http_url if available
                    if "http_url" in tapper_config:
                        http_config["base_url"] = tapper_config["http_url"]

                    # Apply any http_override
                    if "http_override" in tapper_config:
                        http_config.update(tapper_config["http_override"])

                    protocol_configs["http"] = http_config

            elif protocol == "mqtt":
                # Check if protocols is a dict and has mqtt config
                if isinstance(tapper_protocols, dict) and protocol in tapper_protocols:
                    protocol_configs["mqtt"] = tapper_protocols["mqtt"].copy()
                # Check if protocols is a list containing mqtt
                elif isinstance(tapper_protocols, list) and protocol in tapper_protocols:
                    # Build MQTT config from defaults and device_id
                    defaults = self._loaders.get("tappers", {}).get("defaults", {})
                    mqtt_config = defaults.get("mqtt", {}).copy()

                    # Generate MQTT topics using device_id
                    if "device_id" in tapper_config:
                        device_id = tapper_config["device_id"]
                        mqtt_config.update({
                            "command_topic": f"tappers/{device_id}/command",
                            "status_topic": f"tappers/{device_id}/status",
                            "device_id": device_id
                        })

                    # Apply any mqtt_override
                    if "mqtt_override" in tapper_config:
                        mqtt_config.update(tapper_config["mqtt_override"])

                    protocol_configs["mqtt"] = mqtt_config

            elif protocol == "grpc":
                protocol_configs["grpc"] = endpoint_config.get("grpc", {}).copy()
            else:
                self.logger.warning(f"Protocol '{protocol}' not available for tapper or endpoint")

        return protocol_configs

    def _get_station_overrides(self, station_id: str) -> Dict[str, Any]:
        """Get station-specific configuration overrides."""
        if "stations" not in self._loaders:
            return {}

        overrides = self._loaders["stations"].get("station_overrides", {})
        return overrides.get(station_id, {})

    def _apply_protocol_overrides(self, protocol_configs: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
        """Apply station-specific overrides to protocol configurations."""
        if not overrides:
            return protocol_configs

        # Apply protocol-specific overrides
        protocol_overrides = overrides.get("protocols", {})
        for protocol, override_config in protocol_overrides.items():
            if protocol in protocol_configs:
                # Deep merge override config
                protocol_configs[protocol] = {**protocol_configs[protocol], **override_config}

        return protocol_configs

    def invalidate_cache(self, station_id: Optional[str] = None):
        """
        Invalidate configuration cache.

        Args:
            station_id: If provided, only invalidate cache for this station.
                       If None, invalidate entire cache.
        """
        if station_id:
            cache_key = f"station_{station_id}"
            if cache_key in self._config_cache:
                del self._config_cache[cache_key]
                self.logger.debug(f"Invalidated cache for station: {station_id}")
        else:
            self._config_cache.clear()
            self.logger.debug("Invalidated entire configuration cache")

    def reload_configurations(self):
        """Reload all configuration files and clear cache."""
        self.logger.info("Reloading all configuration files")

        # Reload all loaders
        for loader in self._loaders.values():
            loader.reload()

        # Clear cache
        self.invalidate_cache()

        self.logger.info("Configuration reload completed")

    @classmethod
    def get_instance(cls) -> 'ConfigurationManager':
        """Get the singleton instance."""
        if cls._instance is None:
            cls()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Reset singleton (mainly for testing)."""
        with cls._lock:
            cls._instance = None
            cls._initialized = False


# Backward compatibility wrapper
class LegacyStationLoader:
    """
    Legacy compatibility wrapper for the old StationLoader interface.

    Provides backward compatibility for existing code while using the new
    ConfigurationManager internally.
    """

    def __init__(self, config_name="stations"):
        """Initialize with legacy interface."""
        self.logger = get_logger("LegacyStationLoader")
        self.config_manager = ConfigurationManager()

        # Log deprecation warning
        self.logger.warning(
            "LegacyStationLoader is deprecated. "
            "Please migrate to ConfigurationManager for new code."
        )

    def get_station_config(self, station_name: str, protocol: str = None) -> Dict[str, Any]:
        """Get station config with defaults merged (legacy interface)."""
        try:
            # Get config in legacy format
            config = self.config_manager.get_legacy_station_config(station_name)

            # Return specific protocol if requested
            if protocol:
                if protocol not in config:
                    raise KeyError(f"Protocol '{protocol}' not found for station '{station_name}'")
                return {protocol: config[protocol]}

            return config

        except Exception as e:
            self.logger.error(f"Failed to get station config for '{station_name}': {e}")
            raise

    def get_grpc_target(self, station_name: str) -> str:
        """Get gRPC target for station (legacy interface)."""
        config = self.get_station_config(station_name, 'grpc')
        grpc = config['grpc']
        host = grpc.get('host', 'localhost')
        port = grpc.get('port', 50051)
        return f"{host}:{port}"

    def list_stations(self) -> List[str]:
        """Get all station names (legacy interface)."""
        return self.config_manager.list_stations()