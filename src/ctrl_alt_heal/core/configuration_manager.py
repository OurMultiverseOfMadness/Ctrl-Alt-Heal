"""Configuration manager with environment validation, feature flags, and dynamic updates."""

from __future__ import annotations

import os
import json
import logging
import threading
from typing import Dict, Any, Optional, List, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import yaml
from pathlib import Path

from ctrl_alt_heal.utils.constants import ENV_VARS, DEFAULT_CONFIG


logger = logging.getLogger(__name__)


class ConfigSource(Enum):
    """Configuration source enumeration."""

    ENVIRONMENT = "environment"
    FILE = "file"
    SECRETS = "secrets"
    DEFAULT = "default"


@dataclass
class ConfigItem:
    """Configuration item with metadata."""

    key: str
    value: Any
    source: ConfigSource
    description: Optional[str] = None
    required: bool = False
    validated: bool = False
    last_updated: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FeatureFlag:
    """Feature flag configuration."""

    name: str
    enabled: bool
    description: str
    rollout_percentage: float = 100.0
    target_users: Set[str] = field(default_factory=set)
    target_environments: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None


class EnvironmentValidator:
    """Validates environment configuration."""

    def __init__(self):
        self._validation_rules: Dict[str, Dict[str, Any]] = {}
        self._init_validation_rules()

    def _init_validation_rules(self):
        """Initialize validation rules for environment variables."""
        self._validation_rules = {
            "AWS_REGION": {
                "required": True,
                "pattern": r"^[a-z0-9-]+$",
                "description": "AWS region identifier",
            },
            "BEDROCK_MODEL_ID": {
                "required": True,
                "pattern": r"^[a-zA-Z0-9.-]+$",
                "description": "Amazon Bedrock model identifier",
            },
            "TELEGRAM_SECRET_NAME": {
                "required": True,
                "pattern": r"^[a-zA-Z0-9/-]+$",
                "description": "AWS Secrets Manager secret name for Telegram bot token",
            },
            "UPLOADS_BUCKET_NAME": {
                "required": True,
                "pattern": r"^[a-z0-9.-]+$",
                "description": "S3 bucket name for file uploads",
            },
            "CONVERSATIONS_TABLE_NAME": {
                "required": True,
                "pattern": r"^[a-zA-Z0-9_-]+$",
                "description": "DynamoDB table name for conversation history",
            },
            "USERS_TABLE_NAME": {
                "required": True,
                "pattern": r"^[a-zA-Z0-9_-]+$",
                "description": "DynamoDB table name for users",
            },
        }

    def validate_environment(self) -> List[str]:
        """Validate environment configuration."""
        errors = []

        for var_name, rules in self._validation_rules.items():
            value = os.getenv(var_name)

            if rules.get("required", False) and not value:
                errors.append(f"Required environment variable {var_name} is not set")
                continue

            if value and "pattern" in rules:
                import re

                if not re.match(rules["pattern"], value):
                    errors.append(f"Environment variable {var_name} has invalid format")

        return errors

    def get_missing_variables(self) -> List[str]:
        """Get list of missing required environment variables."""
        missing = []
        for var_name, rules in self._validation_rules.items():
            if rules.get("required", False) and not os.getenv(var_name):
                missing.append(var_name)
        return missing

    def get_environment_summary(self) -> Dict[str, Any]:
        """Get environment configuration summary."""
        summary = {"valid": True, "variables": {}, "missing_required": [], "errors": []}

        # Check all variables
        for var_name, rules in self._validation_rules.items():
            value = os.getenv(var_name)
            summary["variables"][var_name] = {
                "set": value is not None,
                "required": rules.get("required", False),
                "description": rules.get("description", ""),
                "value_preview": value[:10] + "..."
                if value and len(value) > 10
                else value,
            }

            if rules.get("required", False) and not value:
                summary["missing_required"].append(var_name)
                summary["valid"] = False

        # Validate format
        errors = self.validate_environment()
        summary["errors"] = errors
        if errors:
            summary["valid"] = False

        return summary


class FeatureFlagManager:
    """Manages feature flags with rollout controls."""

    def __init__(self):
        self._flags: Dict[str, FeatureFlag] = {}
        self._listeners: Dict[str, List[Callable]] = {}
        self._lock = threading.RLock()

        # Initialize default feature flags
        self._init_default_flags()

    def _init_default_flags(self):
        """Initialize default feature flags."""
        self.add_flag(
            FeatureFlag(
                name="enhanced_logging",
                enabled=True,
                description="Enable enhanced structured logging",
            )
        )

        self.add_flag(
            FeatureFlag(
                name="health_monitoring",
                enabled=True,
                description="Enable health monitoring and metrics collection",
            )
        )

        self.add_flag(
            FeatureFlag(
                name="security_scanning",
                enabled=True,
                description="Enable enhanced security scanning and validation",
            )
        )

        self.add_flag(
            FeatureFlag(
                name="caching",
                enabled=True,
                description="Enable caching for improved performance",
            )
        )

    def add_flag(self, flag: FeatureFlag):
        """Add a feature flag."""
        with self._lock:
            self._flags[flag.name] = flag

    def remove_flag(self, flag_name: str):
        """Remove a feature flag."""
        with self._lock:
            self._flags.pop(flag_name, None)

    def is_enabled(
        self,
        flag_name: str,
        user_id: Optional[str] = None,
        environment: Optional[str] = None,
    ) -> bool:
        """Check if a feature flag is enabled."""
        with self._lock:
            flag = self._flags.get(flag_name)
            if not flag:
                return False

            # Check if flag is expired
            if flag.expires_at and datetime.now() > flag.expires_at:
                return False

            # Check if flag is enabled
            if not flag.enabled:
                return False

            # Check environment targeting
            if flag.target_environments and environment:
                if environment not in flag.target_environments:
                    return False

            # Check user targeting
            if flag.target_users and user_id:
                if user_id not in flag.target_users:
                    return False

            # Check rollout percentage
            if flag.rollout_percentage < 100.0:
                import random

                if random.random() * 100 > flag.rollout_percentage:
                    return False

            return True

    def get_flag(self, flag_name: str) -> Optional[FeatureFlag]:
        """Get a feature flag."""
        with self._lock:
            return self._flags.get(flag_name)

    def get_all_flags(self) -> Dict[str, FeatureFlag]:
        """Get all feature flags."""
        with self._lock:
            return self._flags.copy()

    def update_flag(self, flag_name: str, **kwargs):
        """Update a feature flag."""
        with self._lock:
            if flag_name in self._flags:
                flag = self._flags[flag_name]
                for key, value in kwargs.items():
                    if hasattr(flag, key):
                        setattr(flag, key, value)

                # Notify listeners
                if flag_name in self._listeners:
                    for listener in self._listeners[flag_name]:
                        try:
                            listener(flag)
                        except Exception as e:
                            logger.error(f"Feature flag listener error: {e}")

    def add_listener(self, flag_name: str, listener: Callable[[FeatureFlag], None]):
        """Add a listener for feature flag changes."""
        with self._lock:
            if flag_name not in self._listeners:
                self._listeners[flag_name] = []
            self._listeners[flag_name].append(listener)


class ConfigurationManager:
    """Main configuration manager."""

    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = config_dir or "config"
        self._config: Dict[str, ConfigItem] = {}
        self._secrets_cache: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self._watchers: List[Callable] = []

        # Initialize components
        self.validator = EnvironmentValidator()
        self.feature_flags = FeatureFlagManager()

        # Load configuration
        self._load_configuration()

    def _load_configuration(self):
        """Load configuration from all sources."""
        # Load from environment variables
        self._load_from_environment()

        # Load from configuration files
        self._load_from_files()

        # Load from secrets
        self._load_from_secrets()

        # Set defaults
        self._set_defaults()

        # Validate configuration
        self._validate_configuration()

    def _load_from_environment(self):
        """Load configuration from environment variables."""
        for var_name in ENV_VARS.values():
            value = os.getenv(var_name)
            if value is not None:
                self._config[var_name] = ConfigItem(
                    key=var_name,
                    value=value,
                    source=ConfigSource.ENVIRONMENT,
                    description=f"Environment variable: {var_name}",
                )

    def _load_from_files(self):
        """Load configuration from files."""
        config_path = Path(self.config_dir)
        if not config_path.exists():
            return

        # Load YAML files
        for yaml_file in config_path.glob("*.yml"):
            try:
                with open(yaml_file, "r") as f:
                    config_data = yaml.safe_load(f)
                    if config_data:
                        for key, value in config_data.items():
                            self._config[key] = ConfigItem(
                                key=key,
                                value=value,
                                source=ConfigSource.FILE,
                                description=f"From file: {yaml_file.name}",
                            )
            except Exception as e:
                logger.error(f"Error loading config file {yaml_file}: {e}")

        # Load JSON files
        for json_file in config_path.glob("*.json"):
            try:
                with open(json_file, "r") as f:
                    config_data = json.load(f)
                    if config_data:
                        for key, value in config_data.items():
                            self._config[key] = ConfigItem(
                                key=key,
                                value=value,
                                source=ConfigSource.FILE,
                                description=f"From file: {json_file.name}",
                            )
            except Exception as e:
                logger.error(f"Error loading config file {json_file}: {e}")

    def _load_from_secrets(self):
        """Load configuration from AWS Secrets Manager."""
        try:
            from ctrl_alt_heal.infrastructure.secrets import get_secret

            # Load Telegram secret
            telegram_secret_name = os.getenv("TELEGRAM_SECRET_NAME")
            if telegram_secret_name:
                try:
                    secret_data = get_secret(telegram_secret_name)
                    self._config["TELEGRAM_BOT_TOKEN"] = ConfigItem(
                        key="TELEGRAM_BOT_TOKEN",
                        value=secret_data.get("bot_token") or secret_data.get("value"),
                        source=ConfigSource.SECRETS,
                        description=f"From secret: {telegram_secret_name}",
                    )
                except Exception as e:
                    logger.warning(f"Could not load Telegram secret: {e}")

            # Load Serper API key
            serper_secret_name = os.getenv("SERPER_SECRET_NAME")
            if serper_secret_name:
                try:
                    secret_data = get_secret(serper_secret_name)
                    self._config["SERPER_API_KEY"] = ConfigItem(
                        key="SERPER_API_KEY",
                        value=secret_data.get("api_key") or secret_data.get("value"),
                        source=ConfigSource.SECRETS,
                        description=f"From secret: {serper_secret_name}",
                    )
                except Exception as e:
                    logger.warning(f"Could not load Serper secret: {e}")

        except ImportError:
            logger.warning("Secrets module not available")
        except Exception as e:
            logger.error(f"Error loading secrets: {e}")

    def _set_defaults(self):
        """Set default configuration values."""
        for key, value in DEFAULT_CONFIG.items():
            if key not in self._config:
                self._config[key] = ConfigItem(
                    key=key,
                    value=value,
                    source=ConfigSource.DEFAULT,
                    description="Default configuration value",
                )

    def _validate_configuration(self):
        """Validate configuration."""
        # Validate environment
        env_errors = self.validator.validate_environment()
        if env_errors:
            logger.error(f"Environment validation errors: {env_errors}")

        # Mark configuration as validated
        for config_item in self._config.values():
            config_item.validated = True

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        with self._lock:
            config_item = self._config.get(key)
            return config_item.value if config_item else default

    def set(
        self,
        key: str,
        value: Any,
        source: ConfigSource = ConfigSource.FILE,
        description: Optional[str] = None,
    ):
        """Set configuration value."""
        with self._lock:
            self._config[key] = ConfigItem(
                key=key,
                value=value,
                source=source,
                description=description or "Set programmatically",
            )

            # Notify watchers
            self._notify_watchers(key, value)

    def has(self, key: str) -> bool:
        """Check if configuration key exists."""
        with self._lock:
            return key in self._config

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values."""
        with self._lock:
            return {key: item.value for key, item in self._config.items()}

    def get_metadata(self, key: str) -> Optional[ConfigItem]:
        """Get configuration item with metadata."""
        with self._lock:
            return self._config.get(key)

    def reload(self):
        """Reload configuration from all sources."""
        with self._lock:
            self._config.clear()
            self._secrets_cache.clear()

        self._load_configuration()
        logger.info("Configuration reloaded")

    def add_watcher(self, watcher: Callable[[str, Any], None]):
        """Add a configuration change watcher."""
        with self._lock:
            self._watchers.append(watcher)

    def _notify_watchers(self, key: str, value: Any):
        """Notify configuration change watchers."""
        for watcher in self._watchers:
            try:
                watcher(key, value)
            except Exception as e:
                logger.error(f"Configuration watcher error: {e}")

    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get comprehensive configuration summary."""
        with self._lock:
            # Environment validation
            env_summary = self.validator.get_environment_summary()

            # Configuration sources
            source_counts = {}
            for source in ConfigSource:
                source_counts[source.value] = len(
                    [item for item in self._config.values() if item.source == source]
                )

            # Feature flags
            feature_flags = self.feature_flags.get_all_flags()
            flag_summary = {
                flag_name: {
                    "enabled": flag.enabled,
                    "description": flag.description,
                    "rollout_percentage": flag.rollout_percentage,
                }
                for flag_name, flag in feature_flags.items()
            }

            return {
                "environment_valid": env_summary["valid"],
                "environment_errors": env_summary["errors"],
                "missing_required": env_summary["missing_required"],
                "configuration_sources": source_counts,
                "total_config_items": len(self._config),
                "feature_flags": flag_summary,
                "timestamp": datetime.now().isoformat(),
            }

    def export_configuration(self, format: str = "json") -> str:
        """Export configuration to string."""
        with self._lock:
            config_data = {
                key: {
                    "value": item.value,
                    "source": item.source.value,
                    "description": item.description,
                    "validated": item.validated,
                }
                for key, item in self._config.items()
            }

            if format.lower() == "json":
                return json.dumps(config_data, indent=2, default=str)
            elif format.lower() == "yaml":
                return yaml.dump(config_data, default_flow_style=False)
            else:
                raise ValueError(f"Unsupported format: {format}")


# Global configuration manager instance
_config_manager: Optional[ConfigurationManager] = None


def get_config_manager(config_dir: Optional[str] = None) -> ConfigurationManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager(config_dir)
    return _config_manager


def get_config(key: str, default: Any = None) -> Any:
    """Get configuration value."""
    manager = get_config_manager()
    return manager.get(key, default)


def set_config(
    key: str,
    value: Any,
    source: ConfigSource = ConfigSource.FILE,
    description: Optional[str] = None,
):
    """Set configuration value."""
    manager = get_config_manager()
    manager.set(key, value, source, description)


def has_config(key: str) -> bool:
    """Check if configuration key exists."""
    manager = get_config_manager()
    return manager.has(key)


def reload_config():
    """Reload configuration."""
    manager = get_config_manager()
    manager.reload()


def is_feature_enabled(
    flag_name: str, user_id: Optional[str] = None, environment: Optional[str] = None
) -> bool:
    """Check if a feature flag is enabled."""
    manager = get_config_manager()
    return manager.feature_flags.is_enabled(flag_name, user_id, environment)


def get_configuration_summary() -> Dict[str, Any]:
    """Get configuration summary."""
    manager = get_config_manager()
    return manager.get_configuration_summary()


def validate_environment() -> List[str]:
    """Validate environment configuration."""
    manager = get_config_manager()
    return manager.validator.validate_environment()
