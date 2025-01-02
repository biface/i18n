from i18n_tools import package_path
from typing import Any, Optional
from .classes import Singleton
from .loader import load_config, save_config, build_path


class Config(metaclass=Singleton):
    """
    Configuration class for managing translation settings and paths.

    This class is designed as a Singleton to ensure that only one configuration
    instance is active at any time. It provides mechanisms for loading, saving,
    and managing configuration settings.

    Attributes:
        paths (dict): Stores paths for configuration, package, and application files.
        domains (dict): Stores domains for package, and application files translations.
        languages (dict): Manages source language, hierarchy, and fallback language settings.
        translators (dict): Stores API keys or tokens for external translation services.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration with default paths and settings.

        :param config_path: Optional path to the configuration file.
        """
        self.paths = {
            'config': config_path if config_path else None,
            'package': build_path(package_path, "locales"),  # Use the loader's build_path function
            'application': []
        }
        self.domains = {
            'package': [],  # List of domains in the package
            'application': []  # List of domains in the application
        }
        self.languages = {
            'source': "",
            'hierarchy': {},  # Language hierarchy for fallbacks
            'fallback': ""  # Default fallback language
        }
        self.translators = {}  # Translators API keys or endpoints

    def load(self) -> None:
        """
        Load configuration settings from a file.

        Uses the `loader.load_config` function to read the configuration
        from `self.paths['config']`.
        """
        if not self.paths['config']:
            raise ValueError("No configuration file path is set.")
        data = load_config(self.paths['config'])
        if data:
            self.paths.update(data.get('paths', {}))
            self.languages.update(data.get('languages', {}))
            self.translators.update(data.get('translators', {}))

    def save(self) -> None:
        """
        Save the current configuration settings to a file.

        Uses the `loader.save_config` function to write the configuration
        to `self.paths['config']`.
        """
        if not self.paths['config']:
            raise ValueError("No configuration file path is set.")
        data = {
            'paths': self.paths,
            'domains': self.domains,
            'languages': self.languages,
            'translators': self.translators
        }
        save_config(self.paths['config'], data)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a configuration value by key.

        :param key: The key to retrieve, in dot-notation (e.g., 'paths.config').
        :param default: The value to return if the key is not found.
        :return: The value corresponding to the key or the default.
        """
        keys = key.split('.')
        result = self
        for k in keys:
            result = getattr(result, k, None) or result.get(k, None)
            if result is None:
                return default
        return result

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value by key.

        :param key: The key to set, in dot-notation (e.g., 'paths.config').
        :param value: The value to assign.
        """
        keys = key.split('.')
        obj = self
        for k in keys[:-1]:
            obj = obj.get(k, None)
            if obj is None:
                raise KeyError(f"Invalid configuration key: {key}")
        obj[keys[-1]] = value
