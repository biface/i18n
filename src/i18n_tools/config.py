"""
config.py
=========

This module defines the `Config` class, a singleton that centralizes and manages
the global configuration for the i18n-tools package.

**Key Features:**
- Load and save configuration settings to/from files.
- Manage paths for translations, applications, and package-specific locales.
- Configure language settings, translation domains, and translator API details.
- Facilitate author and module metadata management.

**License:**
This file is distributed under the terms of the `CeCILL-C Free Software License Agreement
<https://cecill.info/licences/Licence_CeCILL-C_V1-en.html>`_. By using, modifying, or
redistributing this file, you agree to comply with the terms of this license.

**Author(s):**
This module is authored and maintained as part of the i18n-tools package.
"""

from datetime import datetime
from typing import Any, Optional, Union
from uuid import UUID, uuid4

from email_validator import EmailNotValidError, validate_email
from ndict_tools import NestedDictionary

from i18n_tools import base_path, module_name, package_path

from .api import validate_api_url
from .classes import Singleton
from .loader import build_path, load_config, save_config
from .locale import validate_and_normalize_language_tags


class Config(metaclass=Singleton):
    """
    Configuration class for managing translation settings and paths.

    This class centralizes the configuration for translation tools,
    providing mechanisms for loading, saving, and managing various
    settings related to translations, translators, authors, and modules.

    Attributes:
        setup (NestedDictionary):
            Contains the main configuration settings:
            - `paths`:
                - `config`: Path to the configuration file (if provided).
                - `package`: Default path for package locales.
                - `application`: Includes:
                    - `base`: Base path for the application.
                    - `modules`: List of module paths.
            - `domains`:
                - `package`: dictionary where i18n-tools' modules are keys, and value is a list of associated domains.
                - `application`: dictionary where app's modules are keys, and value is a list of associated domains.
            - `languages`:
                - `source`: Source language of translations.
                - `hierarchy`: Language fallback hierarchy.
                - `fallback`: Default fallback language.
            - `translators`: Translator details like API keys or endpoints.

        details (NestedDictionary):
            Metadata about the configuration:
            - `name`: Name of the configuration.
            - `description`: Description of the configuration.

        authors (NestedDictionary):
            Contains author metadata. Each key corresponds to an author and contains:
            - `email`: Author's email.
            - `languages`: List of languages the author is associated with.
            - Additional optional details.

        _email_index (NestedDictionary):
            An internal index for tracking authors by email address.
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
                    "package": {
                        "locale": build_path(package_path, "locales"),
                        "base": base_path,
                        "modules": [module_name],
                    },  # Use the loader's build_path function
                    "application": {"base": "", "modules": []},
                },
                "domains": {
                    # Originally, domains were simply managed by a list of lists, but this format is not very compatible
                    # with toml. It was therefore changed to a dictionary format, with modules as keys and domains
                    # contained in lists. This applies to the i18n_tools package and to application modules.
                    "package": {},
                    "application": {},
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

        # Validation de l'URL
        validation_result = validate_api_url(url)
        if validation_result["error"]:
            raise ValueError(validation_result["error"])

        # 1. Validation de la date d'expiration de la clé API
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

        # 2. Initialisation de toutes les clés du traducteur, même si elles sont vides
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

        # 3. Vérification de l'existence du traducteur
        if name in self.setup["translators"]:
            raise KeyError(f"Le traducteur '{name}' existe déjà.")

        # 4. Ajout du traducteur au dictionnaire
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

    def update_translator(self, name: str, updates: dict) -> None:
        """
        Update an existing translator's details while ensuring the structure remains valid.

        :param name: The name of the translator to update.
        :param updates: A dictionary containing the updated data.
        :raises KeyError: If the translator does not exist.
        :raises ValueError: If the updates contain invalid keys or structure.
        """
        # Check if the translator exists
        if name not in self.setup["translators"]:
            raise KeyError(f"Translator '{name}' does not exist.")

        # Fetch the existing translator's data
        existing_translator = self.setup["translators"][name]

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
        translators = self.setup["translators"]

        if name in translators:
            # Remove the translator
            translators.pop(name)

            # Ensure the translators dictionary remains a valid empty dictionary if no translators remain
            if not translators:
                self.setup["translators"] = NestedDictionary({}, indent=2, strict=True)

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
        modules = self.setup[["paths", "application", "modules"]]

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

        modules = self.setup[["paths", "application", "modules"]]

        if cleaned_path in modules:
            modules.remove(cleaned_path)
            self.clean_domains(module=cleaned_path)
            return True
        return False

    def clean_modules(self) -> None:
        """
        Resets the list of modules and removes all associated domains.
        """
        self.setup[["paths", "application", "modules"]] = []
        self.setup[["domains", "application"]] = {}

    def add_domain(self, module: str, domain: str) -> None:
        """
        Adds a domain to a specific module.

        :param module: Path of the module.
        :param domain: Name of the domain (e.g., 'messages').
        :raises ValueError: If the module is not registered or the domain already exists.
        """
        modules = self.setup[["paths", "application", "modules"]]
        if module not in modules:
            raise ValueError(f"The module '{module}' is not registered.")

        domains = self.setup[["domains", "application"]]

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
        domains = self.setup[["domains", "application"]]

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
            domains = self.setup[["domains", "application"]]
            if module in domains.keys():
                del domains[module]
        else:
            self.setup[["domains", "application"]] = {}

    def __repr__(self) -> str:
        """
        Represent the `Config` object as a human-readable string.

        This method provides a concise and informative string representation of the
        `Config` instance, displaying key configuration details for quick reference.
        It includes the name and description of the configuration, the paths for
        package and application locales, and the list of source and fallback languages.

        :return: A string summarizing the main configuration details.
        """
        return (
            f"<Config(name='{self.details.get('name', 'Unnamed')}', "
            f"description='{self.details.get('description', 'No description')}', "
            f"paths={{'package': '{self.setup['paths']['package']}', "
            f"'application_base': '{self.setup['paths']['application']['base']}' }}, "
            f"languages={{'source': '{self.setup['languages']['source']}', "
            f"'fallback': '{self.setup['languages']['fallback']}'}})>"
        )
