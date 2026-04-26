"""
This module is responsible for managing the configuration parameters for both the i18n-tools package and the application utilizing it. It ensures that the structure of localized messages is maintained and that all configuration details are accurate and easily accessible.

Key Responsibilities:
    - Manage configuration parameters for the module and application.
    - Maintain the structure of localized messages.
    - Ensure configuration details are accurate and accessible.

Main Data Structure
-------------------

The configuration is structured as a nested dictionary with the following format:

.. code-block:: python

    {
        "details": {
            "name": "Configuration name (*String*)",
            "summary": "Brief summary of the configuration (*String*)",
            "description": "Detailed description of the configuration (*String*)",
            "version": "Version of the configuration (*String*)",
            "content_type": "Type of content (default is *'text/plain'*)",
            "copyright_holder": "Holder of the copyright (*String*)",
            "creation_date": "Creation date and time (a *datetime* with hour and minute precision)",
            "language": "Language of the configuration (*String*)",
            "language_team": "Team responsible for the language (an email address)",
            "flags": {
                "fuzzy": "Flag indicating if the translation is fuzzy (default is ``True``)",
                "python-format": "Flag indicating if Python formatting is used (default is ``True``)",
            },
            "report-bugs-to": "Contact for reporting bugs (an email address)",
        },
        "paths": {
            "root": "Root path (a *String* which represents an absolute path)",
            "repository": "Repository path (a *String* which represents an absolute path)",
            "config": "Configuration directory if given (a *String* which represents an absolute path, '' as default)",
            "backup": "Backup path (a *String* which represents an absolute path, '' as default)",
            "settings": "Settings file if given (a *String*, 'i18n-tools.yaml' as default)",
            "modules": "List of modules (a *List* of *Strings* which represent relative paths)",
        },
        "domains": {
            # A dictionary where modules are keys and a list of domains as values.
            # Each domain represents a translation container related to the domain in the translation repository.
        },
        "languages": {
            "source": "Source language (a *String* as language tag)",
            "hierarchy": "Hierarchy of languages where each key is a language tag as a fallback of a list of language tags available in each domain of translations.",
            "fallback": "Fallback language (a *String* as language tag)",
        },
        "translators": {
            "details": {
                "name": "Name of the translator (a *String* as name)",
                "summary": "Summary of the translator (a *String* as summary)",
                "description": "Description of the translator (a *String* as description)",
                "version": "Version of the translator (a *String* as version)",
                "content_type": "Content type of the translator (a *String* as content type)",
            },
            "modules": [
                # A list of modules (a *List* of *Strings* as list of modules)
                {
                    "name": "name",
                    "url": "url",
                    "status": "status",
                    "translation_type": "translation_type if translation_type is not None else ''",
                }
            ],
            "technical": {
                "api": {
                    "key": "api_key if api_key else ''",
                    "key_expiration": "key_expiration if key_expiration else ''",
                    "request_limit": "request_limit if request_limit is not None else 0",
                    "supported_languages": "supported_languages if supported_languages else []",
                },
                "performance": {
                    "max_text_size": "max_text_size if max_text_size is not None else 0",
                    "priority": "priority if priority is not None else 0",
                    "success_rate": "success_rate if success_rate is not None else 0.0",
                },
            },
            "pricing": {
                "cost_per_translation": "cost_per_translation if cost_per_translation is not None else 0.0",
                "payment_plan": "payment_plan if payment_plan else ''",
            },
        },
        "authors": {
            # A dictionary where each key is a UUID4 and the value is a dictionary with the following structure:
            # {
            #     "first_name": first_name,
            #     "last_name": last_name,
            #     "email": email,
            #     "url": url,  # Link to the profile on a translation site (e.g., https://hosted.weblate.org/user/biface/)
            #     "languages": normalized_languages,  # List of IETF language tags for which the person has translated or can translate
            #
        }
    }

Multiple Data Structures
------------------------

Currently, the configuration handles only two translation configurations:

1. **i18n-tools Package Configuration**: This is managed through the ``package`` attribute of the ``Config`` class.
2. **Application Configuration**: This is managed through the ``application`` attribute of the ``Config`` class.

Only one configuration is managed at a given time.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from email_validator import EmailNotValidError, validate_email
from ndict_tools import StrictNestedDictionary

from .__static__ import (
    I18N_TOOLS_CONFIG,
    I18N_TOOLS_CONFIG_DIR,
    I18N_TOOLS_CONFIG_FILE,
    I18N_TOOLS_LOCALE,
)
from .api import validate_api_url
from .loaders.handler import build_path, file_exists, load_config, save_config
from .locale import validate_and_normalize_language_tags
from .models.repository import Repository
from .patterns import Singleton


class Config(metaclass=Singleton):
    """
    Configuration class for managing translation settings and paths.

    This class centralizes the configuration for translation tools,
    providing mechanisms for loading, saving, and managing various
    settings related to translations, translators, authors, and modules.

    Attributes:
        package (StrictNestedDictionary): A nested dictionary which contains the default i18n-tools package translation repository configuration settings.

        application (StrictNestedDictionary): A nested dictionary which contains the default application translation repository configuration settings.

        _email_index (StrictNestedDictionary):
            An internal index for tracking authors by email address.

        _current_config (str): store the current configuration to manage.
    """

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the configuration with default paths and settings.

        :param config_file: Optional path to the configuration file. If config file is a directory, the default
        settings `i18n-tools.yaml` format  will be used.
        :type config_file: str
        :return: nothing
        :rtype: None
        :raise FileNotFoundError: if the configuration file does not exist.
        """

        def _setup_configuration(
            config_dir: Optional[str] = "", settings_file: Optional[str] = ""
        ) -> StrictNestedDictionary:
            """
            This private initialization function is de dedicated to set up configuration parameters and initializes the
            nested dictionary with spécific keys which will be used as to verify while loading the configuration.

            :param config_dir: directory part of configuration file
            :type config_dir: str
            :param settings_file: file part of configuration file
            :type settings_file: str
            :return: an initialized nested dictionary with used keys
            :rtype: StrictNestedDictionary
            """
            # Initialize using Repository class instead of raw StrictNestedDictionary
            repo = Repository()
            # Set initial config directory and settings file name
            repo[["paths", "config"]] = config_dir if config_dir else ""
            repo[["paths", "settings"]] = (
                settings_file if settings_file else "i18n-tools.yaml"
            )
            return repo

        self.package = _setup_configuration(
            I18N_TOOLS_CONFIG_DIR, I18N_TOOLS_CONFIG_FILE
        )

        if config_file:
            if not file_exists(config_file):
                raise FileNotFoundError(f"File {config_file} does not exist.")

            self.application = _setup_configuration(
                config_dir=config_file.rsplit("/", 1)[0],
                settings_file=config_file.rsplit("/", 1)[1],
            )
        else:
            self.application = _setup_configuration()

        # TODO(ndict-tools-v1.2.0): replace direct StrictNestedDictionary({}) construction
        # with Repository delegation once ndict-tools v1.2.0 is available. See #17 on GitHub.
        self._email_index = StrictNestedDictionary({})
        self._current_config = "application"

    def load(self):
        """
        Load the configuration file and dynamically set attributes based on the configuration dictionary.
        """
        current_config = self.__getattribute__(self._current_config)
        config_file = (
            current_config[["paths", "config"]]
            + "/"
            + current_config[["paths", "settings"]]
        )
        config = load_config(config_file)

        if config.get("configuration") != self._current_config:
            raise IndexError(
                f"Configuration file {config_file} does not match current configuration {self._current_config}"
            )

        # Load general setup
        for key, value in config.get(self._current_config, {}).items():
            if key in current_config.keys():
                current_config[key].update(value)
            else:
                raise AttributeError(f"Unknown configuration key '{key}' in setup.")

        # Rebuild email index

        self._email_index.update(
            {
                author_data["email"]: author_id
                for author_id, author_data in self.__getattribute__(
                    self._current_config
                )["authors"].items()
            }
        )

    def save(self) -> None:
        """
        Save the current configuration settings to a file.

        Uses the `loaders.save_config` function to write the configuration
        to `self.paths['config']`.
        """
        current_config = self.__getattribute__(self._current_config)
        config_file = current_config[["paths", "settings"]]
        if config_file == "":
            raise ValueError("No configuration file path is set.")

        data = {
            "configuration": self._current_config,
            self._current_config: current_config.to_dict(),
        }

        try:
            save_path = current_config[["paths", "config"]] + "/" + config_file
            save_config(save_path, data)
        except Exception as e:
            raise e

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
            if isinstance(attr, StrictNestedDictionary):
                if not isinstance(value, dict):
                    raise TypeError(
                        f"Cannot assign non-dict value to StrictNestedDictionary attribute '{attr_name}'."
                    )
                # Verify keys in the value dictionary
                if check:
                    for key in value.keys():
                        if not attr.is_key(key):
                            raise KeyError(
                                f"Key '{key}' is not valid for StrictNestedDictionary attribute '{attr_name}'."
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
            if not isinstance(attr, StrictNestedDictionary):
                raise TypeError(
                    f"Cannot update a sub-key of attribute '{attr_name}' because it is not a StrictNestedDictionary."
                )
            # Verify nested keys
            nested_path = path[1:]
            if not all(attr.is_key(k) for k in nested_path):
                raise KeyError(
                    f"Path '{nested_path}' is not valid for StrictNestedDictionary attribute '{attr_name}'."
                )
            # Update the nested key
            try:
                attr[nested_path] = value
            except Exception as e:
                # Re-raise any ndict-tools specific exception directly
                raise e

    def get_repository(self) -> StrictNestedDictionary:
        """
        Build the repository dictionary from configuration.

        :return: a configured repository
        :rtype: StrictNestedDictionary
        """
        return self.__getattribute__(self._current_config)

    def set_repository(
        self,
        repository_path: str,
        setting_file_ext: str,
        main_module: str,
        additional_modules: Optional[List[str]] = None,
    ) -> None:
        """
        Set the application repository paths and modules with validation.

        :param repository_path: Base path for the application.
        :param setting_file_ext: File extension of the settings file.
        :param main_module: Main module of the application.
        :param additional_modules: List of module paths.
        :raises FileNotFoundError: If base_path does not exist or is not a directory.
        """
        current_repository = self.__getattribute__(self._current_config)

        if not os.path.isdir(repository_path):
            raise FileNotFoundError(
                f"The base path '{repository_path}' does not exist or is not a directory."
            )

        locale_path = build_path(repository_path, main_module, I18N_TOOLS_LOCALE)
        config_path = build_path(
            repository_path, main_module, I18N_TOOLS_LOCALE, I18N_TOOLS_CONFIG
        )
        setting_file_ext = setting_file_ext.lower()
        if setting_file_ext in ["json", "yaml", "toml"]:
            settings_file = "i18n-tools." + setting_file_ext.lower()
        else:
            raise ValueError(
                f"The file format is not supported : {setting_file_ext} not in ['json', 'yaml', 'toml']."
            )

        current_repository[["paths", "root"]] = repository_path
        current_repository[["paths", "repository"]] = locale_path
        current_repository[["paths", "config"]] = config_path
        current_repository[["paths", "settings"]] = settings_file
        current_repository[["paths", "modules"]] = (
            additional_modules if additional_modules is not None else []
        )

    def update_repository(
        self,
        root_path: Optional[str] = None,
        setting_file_ext: Optional[str] = None,
        main_module: str = None,
        modules: Optional[List[str]] = None,
    ) -> None:
        """
        Update the application repository paths and modules with validation.

        :param root_path: New base path for the application.
        :param setting_file_ext: File extension of the settings file.
        :param main_module: Main module of the application.
        :param modules: New list of module paths.
        :raises ValueError: If base_path does not exist.
        """

        current_repository = self.__getattribute__(self._current_config)

        if root_path is not None:
            if not os.path.isdir(root_path):
                raise FileNotFoundError(
                    f"This path '{root_path}' does not exist or is not a directory."
                )
            if setting_file_ext in ["json", "yaml", "toml"]:
                current_repository[["paths", "root"]] = root_path
                current_repository[["paths", "repository"]] = root_path
                if main_module:
                    current_repository[["paths", "config"]] = build_path(
                        root_path, main_module, I18N_TOOLS_LOCALE, I18N_TOOLS_CONFIG
                    )
                setting_file = "i18n-tools." + setting_file_ext.lower()
                current_repository[["paths", "settings"]] = setting_file
            else:
                raise ValueError(
                    f"The file format is not supported : {setting_file_ext} not in ['json', 'yaml', 'toml']."
                )

        if modules is not None:
            if main_module is None:
                current_repository[["paths", "modules"]] = modules
            else:
                current_repository[["paths", "modules"]] = [main_module] + modules

    def add_details(
        self,
        name: Optional[str] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        version: Optional[str] = None,
        content_type: Optional[str] = None,
        copyright_holder: Optional[str] = None,
    ) -> None:
        """
        This function adds the details of the application to the configuration.
        :param name:
        :param summary:
        :param description:
        :param version:
        :param content_type:
        :param copyright_holder:
        :return:
        """
        current_repository = self.__getattribute__(self._current_config)
        if name is not None:
            current_repository[["details", "name"]] = name
        if summary is not None:
            current_repository[["details", "summary"]] = summary
        if description is not None:
            current_repository[["details", "description"]] = description
        if version is not None:
            current_repository[["details", "version"]] = version
        if content_type is not None:
            current_repository[["details", "content_type"]] = content_type
        if copyright_holder is not None:
            current_repository[["details", "copyright_holder"]] = copyright_holder

    def update_details(self, d_key: str, d_value: Any) -> None:
        """
        update the details of the repository to the configuration..
        :param d_key:
        :param d_value:
        :return:
        """
        current_repository = self.__getattribute__(self._current_config)
        if d_key in current_repository["details"].keys():
            if type(d_value) == type(current_repository["details"][d_key]):
                current_repository["details"][d_key] = d_value
            else:
                raise TypeError(
                    f"The type of the value for {d_key} is not the same as the existing value."
                )
        else:
            raise KeyError(f"The key {d_key} is not in the details of the repository.")

    def add_author(
        self, first_name: str, last_name: str, email: str, url: str, languages: list
    ) -> None:
        """
        Add a new author to the authors dictionary.

        :param first_name: First name of the author.
        :param last_name: Last name of the author.
        :param email: Email address of the author.
        :param url: URL for the author's profile.
        :param languages: List of languages for which the author provides translations.
        :raises EmailNotValidError: if email is malformed
        :raises ValueError: If at least one of the languages is not an IETF tag
        """
        try:
            validate_email(email)
            normalized_languages = validate_and_normalize_language_tags(languages)
        except Exception as e:
            raise e

        if email in self._email_index:
            existing_uuid = self._email_index[email]
            if (
                existing_uuid
                in self.__getattribute__(self._current_config)["authors"].keys()
            ):
                raise KeyError(
                    f"Email address '{email}' is already registered in the authors dictionary (UUID: {existing_uuid})."
                )
            else:
                author_id = existing_uuid
                if self._current_config == "application":
                    author = self.package[["authors", existing_uuid]]
                else:
                    author = self.application[["authors", existing_uuid]]
        else:
            author_id = str(uuid4())
            author = StrictNestedDictionary(
                {
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "url": url,
                    "languages": normalized_languages,
                }
            )
            self._email_index[email] = author_id

        self.__getattribute__(self._current_config)[["authors", author_id]] = author

    def get_author(self, index: str) -> Optional[dict]:
        """
        Retrieve an author's details by UUID or email.

        :param index: The index to search by, either a UUID or an email address.
        :type index: str
        :return: The author's details as a dictionary, or None if not found.
        :rtype: dict
        :raises ValueError: If the email format is invalid or the index is neither a UUID nor a valid email.
        """
        current_config = self.__getattribute__(self._current_config)

        # Check if the input is a valid UUID

        try:
            uuid_obj = UUID(index)
            if index in current_config["authors"]:
                return current_config[["authors", index]]
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
            return current_config[["authors", author_id]]

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
            if index in self.__getattribute__(self._current_config)["authors"]:
                # Remove the author
                author = self.__getattribute__(self._current_config)["authors"].pop(
                    index
                )
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
            self.__getattribute__(self._current_config)["authors"].pop(author_id, None)
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
    ) -> None:
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

        current_repository = self.__getattribute__(self._current_config)

        # Validate the URL
        validation_result = validate_api_url(url)
        if validation_result["error"]:
            raise ValueError(validation_result["error"])

        # 1. Validate the API key expiration date
        if key_expiration:
            try:
                expiration_date = datetime.strptime(key_expiration, "%Y-%m-%d")
                if expiration_date < datetime.now():
                    raise ValueError(
                        f"The expiration date '{key_expiration}' is in the past."
                    )
            except ValueError as e:
                raise e

        # 2. Initialize all translator keys, even if they are empty
        translator_data = {
            "details": {
                "name": name,
                "url": url,
                "status": status,
                "translation_type": (
                    translation_type if translation_type is not None else ""
                ),
            },
            "technical": {
                "api": {
                    "key": api_key if api_key else "",
                    "key_expiration": key_expiration if key_expiration else "",
                    "request_limit": request_limit if request_limit is not None else 0,
                    "supported_languages": (
                        supported_languages if supported_languages else []
                    ),
                },
                "performance": {
                    "max_text_size": max_text_size if max_text_size is not None else 0,
                    "priority": priority if priority is not None else 0,
                    "success_rate": success_rate if success_rate is not None else 0.0,
                },
            },
            "pricing": {
                "cost_per_translation": (
                    cost_per_translation if cost_per_translation is not None else 0.0
                ),
                "payment_plan": payment_plan if payment_plan else "",
            },
        }

        # 3. Check if the translator already exists
        if name in current_repository["translators"]:
            raise KeyError(f"Translator '{name}' already exists.")

        # 4. Add the translator to the dictionary
        current_repository["translators"][name] = StrictNestedDictionary(
            translator_data
        )

    def get_translator(self, name: str) -> StrictNestedDictionary:
        """
        Retrieve the details of a translator by name.

        :param name: The name of the translator.
        :return: The translator's details as a dictionary, or None if not found.
        """

        return self.get([self._current_config, "translators", name])

    def list_translators(self) -> list:
        """
        List all the translators currently in the configuration.

        :return: A list of translator names.
        """

        return list(self.__getattribute__(self._current_config)["translators"].keys())

    def update_translator(self, name: str, updates: dict) -> None:
        """
        Update an existing translator's details while ensuring the structure remains valid.

        :param name: The name of the translator to update.
        :param updates: A dictionary containing the updated data.
        :raises KeyError: If the translator does not exist.
        :raises ValueError: If the updates contain invalid keys or structure.
        """

        current_repository = self.__getattribute__(self._current_config)

        # Check if the translator exists
        if name not in current_repository["translators"]:
            raise KeyError(f"Translator '{name}' does not exist.")

        # Fetch the existing translator's data
        existing_translator = current_repository["translators"][name]

        # Recursive function to validate the updates against the existing structure
        def validate_structure(expected: dict, actual: dict, path: str = ""):
            for key, value in actual.items():
                full_path = f"{path}.{key}" if path else key

                if key not in expected:
                    raise ValueError(f"Invalid key '{full_path}' in updates.")

                # Check for nested dictionaries
                if isinstance(expected[key], dict):
                    if not isinstance(value, dict):
                        raise ValueError(
                            f"Expected a dictionary for '{full_path}', but got '{type(value).__name__}'."
                        )
                    # Recursive validation
                    validate_structure(expected[key], value, full_path)

                # Ensure type matches for non-dict values
                elif not isinstance(value, type(expected[key])):
                    raise ValueError(
                        f"Type mismatch for '{full_path}': "
                        f"expected '{type(expected[key]).__name__}', got '{type(value).__name__}'."
                    )

        # Validate updates against the existing translator structure
        validate_structure(existing_translator, updates)

        # Apply the updates
        def apply_updates(target: dict, source: dict):
            for key, value in source.items():
                if isinstance(value, dict):
                    apply_updates(target[key], value)
                else:
                    target[key] = value

        apply_updates(existing_translator, updates)

    def remove_translator(self, name: str) -> bool:
        """
        Remove a translator from the setup['translators'] dictionary by its ID.

        :param name: The unique ID of the translator to remove.
        :return: True if the translator was successfully removed, False if not found.
        """
        # Access the translators dictionary
        translators = self.__getattribute__(self._current_config)["translators"]

        if name in translators:
            # Remove the translator
            translators.pop(name)

            # Ensure the translators dictionary remains a valid empty dictionary if no translators remain
            # TODO(ndict-tools-v1.2.0): replace direct StrictNestedDictionary({}) construction
            # with Repository delegation once ndict-tools v1.2.0 is available. See #17.
            if not translators:
                self.__getattribute__(self._current_config)["translators"] = (
                    StrictNestedDictionary({})
                )

            return True

        return False

    def add_module(self, module_path: str) -> None:
        """
        Adds a module path to the application's modules list.

        If the path contains "locales" or "locale", these parts are removed.
        If the path is already registered, an exception is raised.

        :param module_path: Path to the module directory.
        :raises ValueError: If the module path is already registered.
        """

        cleaned_path = (
            module_path.replace("locales", "").replace("locale", "").strip("/")
        )
        modules = self.__getattribute__(self._current_config)[["paths", "modules"]]

        if cleaned_path in modules:
            raise ValueError(
                f"The path '{cleaned_path}' is already registered as a module."
            )

        modules.append(cleaned_path)

    def remove_module(self, module_path: str) -> bool:
        """
        Removes a module from the list and cleans up associated domains.

        :param module_path: Path to the module directory to remove.
        :return: True if the module was removed, False if it was not found.
        """

        cleaned_path = (
            module_path.replace("locales", "").replace("locale", "").strip("/")
        )

        modules = self.__getattribute__(self._current_config)[["paths", "modules"]]

        if cleaned_path in modules:
            modules.remove(cleaned_path)
            self.clean_domains(module=cleaned_path)
            return True
        return False

    def clean_modules(self) -> None:
        """
        Resets the list of modules and removes all associated domains.
        """
        self.__getattribute__(self._current_config)[["paths", "modules"]] = []
        self.__getattribute__(self._current_config)["domains"] = {}

    def add_domain(self, module: str, domain: str) -> None:
        """
        Adds a domain to a specific module.

        :param module: Path of the module.
        :param domain: Name of the domain (e.g., 'messages').
        :raises ValueError: If the module is not registered or the domain already exists.
        """
        modules = self.__getattribute__(self._current_config)[["paths", "modules"]]
        if module not in modules:
            raise ValueError(f"The module '{module}' is not registered.")

        domains = self.__getattribute__(self._current_config)["domains"]

        if module not in domains.keys():
            domains[module] = [domain]
        elif domain in domains[module]:
            raise ValueError(
                f"The domain '{domain}' is already associated with the module '{module}'."
            )
        else:
            domains[module].append(domain)

    def remove_domain(self, module: str, domain: str) -> bool:
        """
        Removes a domain from a specific module.

        :param module: Path of the module.
        :param domain: Name of the domain.
        :return: True if the domain was removed, False otherwise.
        """
        domains = self.__getattribute__(self._current_config)["domains"]

        if module in domains.keys():
            if domain in domains[module]:
                domains[module].remove(domain)
                return True

        return False

    def clean_domains(self, module: Optional[str] = None) -> None:
        """
        Resets domains for a specific module or all modules.

        :param module: Path of the module. If None, all domains are removed.
        """
        if module:
            domains = self.__getattribute__(self._current_config)["domains"]
            if module in domains.keys():
                del domains[module]
        else:
            self.__getattribute__(self._current_config)["domains"] = {}

    def switch_to_package_config(self) -> None:
        """
        Switch the current configuration context to the package configuration.
        """
        self._current_config = "package"

    def switch_to_application_config(self) -> None:
        """
        Switch the current configuration context to the application configuration.
        """
        self._current_config = "application"

    def toggle_config(self) -> None:
        """
        Toggle the current configuration context between package and application.
        """
        self._current_config = (
            "application" if self._current_config == "package" else "package"
        )

    def __repr__(self) -> str:
        """
        Represent the `Config` object as a human-readable string.

        This method provides a concise and informative string representation of the
        `Config` instance, displaying key configuration details for quick reference.
        It includes the name and description of the configuration, the paths for
        package and application locales, and the list of source and fallback languages.

        :return: A string summarizing the main configuration details.
        """
        configuration = self._current_config
        current_repository = self.__getattribute__(configuration)

        return (
            f"<Config(name='{current_repository[['details']].get('name', 'None')}',\n"
            f"paths={{'repository': '{current_repository['paths'].get('repository', 'Not specified')}',\n"
            f"'settings': '{current_repository['paths'].get('settings', 'Not specified')}"
        )
