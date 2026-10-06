import os
from typing import Any, Dict

import yaml

from .logger import logger

class ConfigLoader:
    """Loads configuration settings from YAML files based on the environment."""

    def __init__(self, config_dir: str = "configs") -> None:
        self.config_dir = config_dir
        self.env = os.environ.get("ENVIRONMENT", "dev").lower()
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Loads common config and environment-specific config, merging them."""
        common_config_path = os.path.join(self.config_dir, "common", "config.yml")
        env_config_path = os.path.join(self.config_dir, self.env, "config.yml")

        config: Dict[str, Any] = {}

        if os.path.exists(common_config_path):
            with open(common_config_path, "r") as f:
                config.update(yaml.safe_load(f) or {})
        else:
            logger.warning(f"Common config file not found at {common_config_path}")

        if os.path.exists(env_config_path):
            with open(env_config_path, "r") as f:
                env_config = yaml.safe_load(f) or {}
                # Simple shallow merge, env overrides common
                config.update(env_config)
        else:
            logger.warning(f"Environment config file not found at {env_config_path}")

        return config

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieves a configuration value by key."""
        return self.config.get(key, default)

# Global config instance for easy access
app_config = ConfigLoader()
