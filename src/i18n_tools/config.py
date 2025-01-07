from ndict_tools import NestedDictionary
from typing import Any, Optional

from i18n_tools import package_path

from .classes import Singleton
from .loader import build_path, load_config, save_config


class Config(metaclass=Singleton):
    """
    Configuration class for managing translation settings and paths.

    This class is designed as a Singleton to ensure that only one configuration
    instance is active at any time. It provides mechanisms for loading, saving,
    and managing configuration settings.

    Attributes:
        name (str): The name of the configuration. (unused)
        setup (dict) : a NestedDictionary object containing the configuration

            - paths (dict): Stores paths for configuration, package, and application files.
            - domains (dict): Stores domains for package, and application files translations.
            - languages (dict): Manages source language, hierarchy, and fallback language settings.
            - translators (dict): Stores API keys or tokens for external translation services.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration with default paths and settings.

        :param config_path: Optional path to the configuration file.
        """
        self.name = ""
        self.setup = NestedDictionary(indent=2, strict=True)
        self.setup.update(
            {
                "paths": {
                    "config": config_path if config_path else None,
                    "package": build_path(
                        package_path, "locales"
                    ),  # Use the loader's build_path function
                    "application": [],
                },
                "domains": {
                    "package": [],  # List of domains in the package
                    "application": [],  # List of domains in the application
                },
                "languages": {
                    "source": "",
                    "hierarchy": {},  # Language hierarchy for fallbacks
                    "fallback": "",  # Default fallback language
                },
                "translators": {},
            }
        )  # Translators API keys or endpoints

    def load(self):
        """
        Load the configuration file and dynamically set attributes based on the configuration dictionary.
        """
        config = load_config(self.setup[["paths", "config"]])

        # Parcourir les clés du fichier de configuration et les affecter aux attributs de l'objet
        for key, value in config.items():
            if key in self.setup.keys():
                self.setup[key].update(value)
            else:
                raise AttributeError(f"Unknown configuration key '{key}' in the file.")

    def save(self) -> None:
        """
        Save the current configuration settings to a file.

        Uses the `loader.save_config` function to write the configuration
        to `self.paths['config']`.
        """
        if not self.setup[["paths", "config"]]:
            raise ValueError("No configuration file path is set.")
        data = self.setup.to_dict()
        save_config(self.setup[["paths", "config"]], data)

    def get(self, key: list, default: Any = None) -> Any:
        """
        Retrieve a configuration value by key.

        :param key: The key to retrieve, in dot-notation (e.g., 'paths.config').
        :param default: The value to return if the key is not found.
        :return: The value corresponding to the key or the default.
        """
        return self.setup[key]

    def set(self, key: list, value: Any) -> None:
        """
        Set a configuration value by key.

        :param key: The key to set, in dot-notation (e.g., 'paths.config').
        :param value: The value to assign.
        """
        self.setup[key] = value

    def __repr__(self):
        """
        Returns a string representation of the Config object.

        :return: A formatted string representation of the configuration.
        """
        return (
            f"<Config("
            f"paths={{'config': '{self.setup[['paths', 'config']]}', 'package': '{self.setup[['paths', 'package']]}', "
            f"'application': {self.setup[['paths', 'application']]}}}, "
            f"languages={{'source': '{self.setup[['languages', 'source']]}', "
            f"'fallback': '{self.setup[['languages', 'fallback']]}', "
            f"'hierarchy': {self.setup[['languages', 'hierarchy']]}}}, "
            f"domains={{'package': {self.setup[['domains', 'package']]}, 'application': {self.setup[['domains', 'application']]}}}, "
            f"translators={list(self.setup['translators'])}"
            f")>"
        )
