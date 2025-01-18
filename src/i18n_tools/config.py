"""
config.py
=========

This module defines the `Config` class, a singleton that manages the global
configuration of the i18n-tools package.

**Key Features:**
- Load and save configuration settings.
- Manage paths for translations, applications, and package locales.
- Handle language settings, domains, and translator mappings.

**License:**
This file is distributed under the `CeCILL-C Free Software License Agreement
<https://cecill.info/licences/Licence_CeCILL-C_V1-en.html>`_. By using or
modifying this file, you agree to abide by the terms of this license.

**Author(s):**
This module is authored and maintained as part of the i18n-tools package.
"""

from datetime import datetime
from typing import Any, Optional, Union
from uuid import UUID, uuid4

import requests
import validators
from email_validator import EmailNotValidError, validate_email
from ndict_tools import NestedDictionary

from i18n_tools import package_path

from .classes import Singleton
from .loader import build_path, load_config, save_config
from .locale import validate_and_normalize_language_tags


class Config(metaclass=Singleton):
    """
    Configuration class for managing translation settings and paths.

    This class is designed as a Singleton to ensure that only one configuration
    instance is active at any time. It provides mechanisms for loading, saving,
    and managing configuration settings.

    Attributes:
        setup (dict): A NestedDictionary object containing the main configuration.
        details (dict): Contains metadata about the configuration (name, description).
        authors (dict): A dictionary of authors, each with their details and associated languages.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration with default paths and settings.

        :param config_path: Optional path to the configuration file.
        """
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
                "translators": {},  # Translators API keys or endpoints
            }
        )

        self.details = NestedDictionary(
            {
                "name": "",  # Configuration name
                "description": "",  # Configuration description
            },
            indent=2,
            strict=True,
        )

        self.authors = NestedDictionary({}, indent=2, strict=True)  # Author details
        self._email_index = NestedDictionary({}, indent=2, strict=True)

    def load(self):
        """
        Load the configuration file and dynamically set attributes based on the configuration dictionary.
        """
        config = load_config(self.setup[["paths", "config"]])

        # Load general setup
        for key, value in config.get("setup", {}).items():
            if key in self.setup.keys():
                self.setup[key].update(value)
            else:
                raise AttributeError(f"Unknown configuration key '{key}' in setup.")

        # Load details
        self.details.update(config.get("details", {}))

        # Load authors
        self.authors.update(config.get("authors", {}))

        # Rebuild email index
        self._email_index = {
            author_data["email"]: author_id
            for author_id, author_data in self.authors.items()
        }

    def save(self) -> None:
        """
        Save the current configuration settings to a file.

        Uses the `loader.save_config` function to write the configuration
        to `self.paths['config']`.
        """
        if not self.setup[["paths", "config"]]:
            raise ValueError("No configuration file path is set.")

        data = {
            "setup": self.setup.to_dict(),
            "details": self.details.to_dict(),
            "authors": self.authors.to_dict(),
        }
        save_config(self.setup[["paths", "config"]], data)

    def get(self, key: list) -> Any:
        """
        Retrieve a configuration value by key.

        :param key: The key to retrieve, in dot-notation (e.g., 'paths.config').
        :return: The value corresponding to the key or the default.
        """
        if hasattr(self, key[0]):
            return self.__getattribute__(key[0])[key[1:]]
        else:
            raise KeyError(f"Key '{key[0]}' not found.")

    def set(self, path: Union[list[Any], str], value: Any, check: bool = True) -> None:
        """
        Set or update a configuration attribute or its nested keys.

        :param path: A string or list representing the attribute and/or nested keys.
                     If a string or a list of size 1, it is treated as a direct attribute.
        :param value: The value to assign or update.
        :raises ValueError: If the path is invalid or empty.
        :raises KeyError: If the attribute or key does not exist.
        :raises TypeError: If the value type does not match the attribute type.
        """
        # Normalize path to a list
        if isinstance(path, str):
            if len(path) > 0:
                path = [path]
            else:
                raise ValueError("Path must be a non-empty string the attribute.")
        elif not isinstance(path, list) or len(path) == 0:
            raise ValueError(
                "Path must be a non-empty list or list representing the attribute or nested key."
            )

        attr_name = path[0]
        if not hasattr(self, attr_name):
            raise KeyError(f"Attribute '{attr_name}' not found in configuration.")

        attr = getattr(self, attr_name)

        # Case 1: Direct attribute update (string path or list of size 1)
        if len(path) == 1:
            if isinstance(attr, NestedDictionary):
                if not isinstance(value, dict):
                    raise TypeError(
                        f"Cannot assign non-dict value to NestedDictionary attribute '{attr_name}'."
                    )
                # Verify keys in the value dictionary
                if check:
                    for key in value.keys():
                        if not attr.is_key(key):
                            raise KeyError(
                                f"Key '{key}' is not valid for NestedDictionary attribute '{attr_name}'."
                            )
                    # Update using NestedDictionary's update
                attr.update(value)
            else:
                # Verify type compatibility
                if not isinstance(value, type(attr)):
                    raise TypeError(
                        f"Type mismatch: Cannot assign value of type '{type(value).__name__}' "
                        f"to attribute '{attr_name}' of type '{type(attr).__name__}'."
                    )
                setattr(self, attr_name, value)

        # Case 2: Nested key update in NestedDictionary (path length > 1)
        else:
            if not isinstance(attr, NestedDictionary):
                raise TypeError(
                    f"Cannot update a sub-key of attribute '{attr_name}' because it is not a NestedDictionary."
                )
            # Verify nested keys
            nested_path = path[1:]
            if not attr.is_key(nested_path[0]):
                raise KeyError(
                    f"Key '{nested_path[0]}' is not valid for NestedDictionary attribute '{attr_name}'."
                )
            # Update the nested key
            try:
                attr[nested_path] = value
            except Exception as e:
                # Re-raise any ndict-tools specific exception directly
                raise e

    def add_author(
        self, first_name: str, last_name: str, email: str, url: str, languages: list
    ):
        """
        Add a new author to the authors dictionary.

        :param first_name: First name of the author.
        :param last_name: Last name of the author.
        :param email: Email address of the author.
        :param url: URL for the author's profile.
        :param languages: List of languages for which the author provides translations.
        """
        try:
            validate_email(email)
        except EmailNotValidError as e:
            raise e

        normalized_languages = validate_and_normalize_language_tags(languages)

        if email in self._email_index:
            existing_uuid = self._email_index[email]
            raise KeyError(
                f"Email address '{email}' is already registered in the authors dictionary (UUID: {existing_uuid})."
            )

        author_id = str(uuid4())
        self.authors[author_id] = NestedDictionary(
            {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "url": url,
                "languages": normalized_languages,
            },
            indent=2,
            strict=True,
        )

        self._email_index[email] = author_id

    def get_author(self, index: str) -> Optional[dict]:
        """
        Retrieve an author's details by UUID or email.

        :param index: The index to search by, either a UUID or an email address.
        :type index: str
        :return: The author's details as a dictionary, or None if not found.
        :rtype: dict
        :raises ValueError: If the email format is invalid or the index is neither a UUID nor a valid email.
        """
        # Check if the input is a valid UUID
        try:
            uuid_obj = UUID(index)
            if index in self.authors:
                return self.get(["authors", index])
            else:
                raise KeyError(
                    f"Index '{index}' does not exist in the authors dictionary."
                )  # UUID not found
        except ValueError:
            # Not a valid UUID, proceed to check for email
            pass

        # Validate the email format
        try:
            validate_email(index)  # Throws EmailNotValidError if invalid
        except EmailNotValidError as e:
            raise ValueError(f"Invalid email format: {e}")

        # Search by email in the email index
        author_id = self._email_index.get(index)
        if author_id:
            return self.get(["authors", author_id])

        # If the email doesn't exist, return None
        return None

    def remove_author(self, index: str) -> bool:
        """
        Remove an author from the configuration by UUID or email.

        :param index: The index to search by, either a UUID or an email address.
        :return: True if the author was successfully removed, False if not found.
        :raises ValueError: If the email format is invalid or the index is neither a UUID nor a valid email.
        """
        # Check if the input is a valid UUID
        try:
            uuid_obj = UUID(index)
            # Remove by UUID if it exists
            if index in self.authors:
                # Remove the author
                author = self.authors.pop(index)
                # Remove from the email index
                self._email_index.pop(author["email"], None)
                return True
            else:
                return False  # UUID not found
        except ValueError:
            # Not a valid UUID, proceed to check for email
            pass

        # Validate the email format
        try:
            validate_email(index)  # Throws EmailNotValidError if invalid
        except EmailNotValidError as e:
            raise ValueError(f"Invalid email format: {e}")

        # Search by email in the email index
        author_id = self._email_index.get(index)
        if author_id:
            # Remove the author and the email index entry
            self.authors.pop(author_id, None)
            self._email_index.pop(index, None)
            return True

        # If no match found, return False
        return False

    def add_translator(
        self,
        name: str,
        url: str,
        status: str,
        api_key: str,
        supported_languages: list,
        translation_type: Optional[str] = None,
        cost_per_translation: Optional[float] = None,
        request_limit: Optional[int] = None,
        key_expiration: Optional[str] = None,
        priority: Optional[int] = None,
        success_rate: Optional[float] = None,
        max_text_size: Optional[int] = None,
        payment_plan: Optional[str] = None,
    ):
        """
        Add a new translator to the configuration, organized in nested dictionaries under technical.

        :param name: The name of the translator.
        :param url: The URL for the translator's API.
        :param status: The status of the translator, either 'free' or 'license'.
        :param api_key: The API key for the translator's service.
        :param supported_languages: List of supported languages by the translator.
        :param translation_type: Type of content the translator is best for (e.g., "general", "technical").
        :param cost_per_translation: Cost per translation (if applicable).
        :param request_limit: Limit on the number of requests per day or month.
        :param key_expiration: Expiration date of the API key (string, format "YYYY-MM-DD").
        :param priority: The priority of the translator (for sorting purposes).
        :param success_rate: Estimated success rate of translations (as a percentage).
        :param max_text_size: Maximum size of text for translation (in characters).
        :param payment_plan: The payment plan for licensed translators (e.g., "monthly", "annual").
        """

        # 1. Validation de l'URL
        if not validators.url(url):
            raise ValueError(f"L'URL '{url}' n'est pas valide.")

        # Vérification de l'accessibilité de l'URL
        try:
            response = requests.get(url, timeout=5)
            if response.status_code != 200:
                raise ValueError(
                    f"L'URL '{url}' est accessible, mais a retourné un code d'erreur {response.status_code}."
                )
        except requests.exceptions.RequestException as e:
            raise ValueError(f"L'URL '{url}' n'est pas accessible. Erreur : {e}")

        # 2. Validation de la date d'expiration de la clé API
        if key_expiration:
            try:
                expiration_date = datetime.strptime(key_expiration, "%Y-%m-%d")
                if expiration_date < datetime.now():
                    raise ValueError(
                        f"La date d'expiration '{key_expiration}' est dans le passé."
                    )
            except ValueError:
                raise ValueError(
                    f"Le format de la date d'expiration '{key_expiration}' est invalide. Utilisez 'YYYY-MM-DD'."
                )

        # 3. Ajout du traducteur
        if name in self.setup["translators"]:
            raise KeyError(f"Translator '{name}' already exists.")

        translator_data = {
            "details": {
                "name": name,
                "url": url,
                "status": status,
            },
            "technical": {
                "api": {
                    "key": api_key,
                    "key_expiration": key_expiration,
                    "request_limit": request_limit,
                },
                "performance": {
                    "max_text_size": max_text_size,
                    "priority": priority,
                    "success_rate": success_rate,
                },
            },
            "pricing": {
                "cost_per_translation": cost_per_translation,
                "payment_plan": payment_plan,
            },
        }

        # Ajout du traducteur au dictionnaire
        self.setup["translators"][name] = NestedDictionary(
            translator_data, indent=2, strict=True
        )

    def get_translator(self, name: str) -> NestedDictionary:
        """
        Retrieve the details of a translator by name.

        :param name: The name of the translator.
        :return: The translator's details as a dictionary, or None if not found.
        """
        return self.get(["setup", "translators", name])

    def list_translators(self) -> list:
        """
        List all the translators currently in the configuration.

        :return: A list of translator names.
        """
        return list(self.setup["translators"].keys())

    def remove_translator(self, name: str) -> bool:
        """
        Remove a translator from the setup['translators'] dictionary by its ID.

        :param name: The unique ID of the translator to remove.
        :return: True if the translator was successfully removed, False if not found.
        """
        # Access the translators dictionary
        translators = self.setup["translators"]

        if name in translators:
            # Remove the translator
            translators.pop(name)

            # Ensure the translators dictionary remains a valid empty dictionary if no translators remain
            if not translators:
                self.setup["translators"] = NestedDictionary({}, indent=2, strict=True)

            return True

        return False

    def __repr__(self):
        """
        Returns a string representation of the Config object.

        :return: A formatted string representation of the configuration.
        """
        return (
            f"<Config("
            f"paths={{'config': '{self.get(['setup','paths', 'config'])}', "
            f"'package': '{self.get(['setup','paths', 'package'])}', "
            f"'application': {self.get(['setup','paths', 'application'])}}}, "
            f"languages={{'source': '{self.setup['languages', 'source']}', "
            f"'fallback': '{self.setup['languages', 'fallback']}', "
            f"'hierarchy': {self.setup['languages', 'hierarchy']}}}, "
            f"domains={{'package': {self.setup['domains', 'package']}, 'application': {self.setup['domains', 'application']}}}, "
            f"details={{'name': '{self.details['name']}', 'description': '{self.details['description']}'}}, "
            f"authors={list(self.authors.keys())}"
            f")>"
        )
