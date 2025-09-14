"""
Repository module
=================

This module defines the Repository class, the in-memory representation of an
i18n repository used by i18n_tools. A repository is modeled as a nested
mapping built on top of ndict_tools.core.StrictNestedDictionary in order to
preserve structure, validate paths, and provide convenient access helpers.

It describes the structure and the organization of translation files and their
metadata (details, paths, languages, domains, translators, authors, etc.).

References
----------
- StrictNestedDictionary: https://ndict-tools.readthedocs.io/en/latest/api.html#ndict_tools.core.StrictNestedDictionary

Quick example
-------------

>>> from i18n_tools.models.repository import Repository
>>> repo = Repository()
>>> repo.name = "My Project"
>>> repo.add_module("src/app")
>>> repo.add_domain("src/app", "messages")
>>> repo.hierarchy  # doctest: +ELLIPSIS
StrictNestedDictionary({...})

The Repository instance can then be serialized via ndict_tools helpers or used
by other components (loaders, handlers, CLI) to manage i18n content.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ndict_tools import StrictNestedDictionary

from ..api import validate_api_url

# Shared default setup to avoid repetition
_DEFAULT_SETUP = {"indent": 2}


class Repository(StrictNestedDictionary):
    """
    Repository
    ----------
    High-level, structured container describing an i18n repository.

    The repository is split into several top-level sections:
    - details: General metadata (name, version, dates, language, flags, etc.).
    - paths: File-system related paths and the list of application modules.
    - domains: Mapping of module -> list of gettext-like domains.
    - languages: Source language, fallback, and variants hierarchy.
    - translators: Registered online translators and their technical/pricing data.
    - authors: Contributors metadata.

    Instances behave like a StrictNestedDictionary while providing friendly
    Python properties and helper methods to keep the underlying structure
    consistent.

    Examples
    --------
    >>> repo = Repository()
    >>> repo.name = "i18n-tools sample"
    >>> repo.add_module("src/web")
    >>> repo.add_domain("src/web", "messages")
    >>> repo.languages["source"]
    ''

    Notes
    -----
    All sections are created with a default ndict_tools setup (indent=2) to
    keep JSON/YAML rendering consistent across the project.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(default_setup=_DEFAULT_SETUP)

        # Initialize sections with a helper to factorize StrictNestedDictionary creation
        self["details"] = self._new_section(
            {
                "name": "",  # Configuration name
                "summary": "",
                "description": "",  # Configuration description
                "version": "",
                "content_type": "text/plain",
                "copyright_holder": "",
                "date": {
                    "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
                },
                "language": "",
                "language_team": "",
                "flags": {
                    "fuzzy": True,
                    "python-format": True,
                },
                "report-bugs-to": "",
            }
        )
        # Ensure a flat alias to the creation date exists for convenience/APIs
        self[["details", "creation_date"]] = self[["details", "date", "created"]]

        self["paths"] = self._new_section(
            {
                "root": "",
                "repository": "",
                "config": "",
                "backup": "",
                "settings": "i18n-tools.yaml",
                # May be changed for .json or .toml
                "modules": [],
            }
        )
        self["domains"] = self._new_section({})
        self["languages"] = self._new_section(
            {
                "source": "",
                "hierarchy": {},
                "fallback": "",
            }
        )
        self["translators"] = self._new_section({})
        self["authors"] = self._new_section({})

        # args content
        self._apply_args(args)

        # kwargs content
        self._apply_kwargs(kwargs)

    # --- Private helpers ---
    def _new_section(self, data: dict) -> StrictNestedDictionary:
        """Create a StrictNestedDictionary section with the shared default setup."""
        return StrictNestedDictionary(data, default_setup=_DEFAULT_SETUP)

    def _apply_args(self, args) -> None:
        for path, value in args:
            if not (isinstance(path, list) and path in self.dict_paths()) and not (
                isinstance(path, str) and self.is_key(path)
            ):
                raise KeyError(f"{path} is not a valid path or key")

            if not isinstance(value, dict):
                if type(value) != type(self[path]):
                    raise TypeError(f"{path} : {value} is not a {type(self[path])}")
                else:
                    self[path] = value
            else:
                if not isinstance(self[path], StrictNestedDictionary):
                    raise TypeError(f"{path} : {value} is not a {type(self[path])}")
                else:
                    self[path].update(value)

    def _apply_kwargs(self, kwargs: dict) -> None:
        for key, value in kwargs.items():
            if key in self.keys():
                if isinstance(value, dict):
                    self[key].update(value)
                else:
                    raise TypeError(f"{key} : {value} must be a dictionary")
            else:
                raise KeyError(f"{key} is not a valid key {self.keys()}")

    # Properties

    @property
    def name(self):
        """
        The name of the repository.
        :return: the string name of the repository
        """
        return self[["details", "name"]]

    @name.setter
    def name(self, value: str):
        """
        The name of the repository.
        :return:
        """
        self[["details", "name"]] = value

    @property
    def config(self) -> str:
        """
        The name of the repository file and directory.
        :return:
        """
        return self[["paths", "config"]] + "/" + self[["paths", "settings"]]

    @config.setter
    def config(self, value: str) -> None:
        """
        The name of the repository file and directory.
        :param value:
        :return:
        """
        file_index = value.rfind("/")
        self[["paths", "config"]] = value[:file_index]
        self[["paths", "settings"]] = value[file_index + 1 :]

    @property
    def creation_date(self) -> str:
        """Alias property for the creation date stored at details.date.created.

        Returns the value located at path ["details", "date", "created"].
        Also kept mirrored to ["details", "creation_date"] for APIs expecting a flat key.
        """
        return str(self[["details", "date", "created"]])

    @property
    def updated_date(self) -> str:
        """Property for the updated date stored at details.date.updated.

        Returns the value located at path ["details", "date", "updated"].
        """
        return str(self[["details", "date", "updated"]])

    @updated_date.setter
    def updated_date(self, value: str) -> None:
        """Set the updated date from a string, converting it to a datetime.

        The accepted formats are, in order:
        - ISO 8601 (datetime.fromisoformat)
        - "%Y-%m-%d %H:%M:%S"
        - "%Y-%m-%d %H:%M"
        - "%Y-%m-%d"
        """
        dt: datetime | None = None
        if isinstance(value, str):
            # Try ISO 8601 first
            try:
                dt = datetime.fromisoformat(value)
            except ValueError:
                # Try common strptime patterns
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
                    try:
                        dt = datetime.strptime(value, fmt)
                        break
                    except ValueError:
                        continue
        if dt is None:
            raise ValueError(
                "updated_date must be a string representing a date/time in ISO format or '%Y-%m-%d %H:%M[:%S]'"
            )
        # Update the nested source of truth with a datetime object
        self[["details", "date", "updated"]] = dt.strftime("%Y-%m-%d %H:%M")

    @property
    def modules(self):
        """
        The list of modules in the repository.
        :return:
        """
        return self[["paths", "modules"]]

    @modules.setter
    def modules(self, value: list):
        """
        The list of domains in the repository.
        :param value:
        :return:
        """
        self[["paths", "modules"]] = value

    def add_module(self, module: str) -> None:
        """
        Adds a specific module to the list of  modules.
        :param module:
        :return:
        :raises ValueError: if module already exists
        """
        if module not in self[["paths", "modules"]]:
            self[["paths", "modules"]].append(module)
        else:
            raise ValueError(f"Module {module} already exists")

    def remove_module(self, module: str) -> None:
        """
        Removes a specific module from the list of  modules.

        :param module:
        :return:
        :raises ValueError: if module does not exist
        """
        if module in self[["paths", "modules"]]:
            self[["paths", "modules"]].remove(module)
            if module in self["domains"]:
                del self[["domains", module]]
        else:
            raise ValueError(f"Module {module} does not exist")

    def clean_modules(self) -> None:
        """
        Removes all modules from the list of modules, and thus reset domains.
        :return:
        """
        self[["paths", "modules"]] = []
        self["domains"] = self._new_section({})

    @property
    def domains(self) -> dict[str, list[str]]:
        """
        The list of domains in the repository.
        :return: an instance of dict containing by modules (keys) the domains as a list of string
        """
        return self["domains"].to_dict()

    @domains.setter
    def domains(self, value: dict) -> None:
        # Accepts an iterable of (module, [domains...]) and merges into self["domains"]
        for module, domains in value.items():
            if module in self[["paths", "modules"]]:
                # Ensure the module key exists under domains
                if module not in self["domains"].keys():
                    self[["domains", module]] = []
                for domain in domains:
                    if domain not in self[["domains", module]]:
                        self[["domains", module]].append(domain)
                    else:
                        raise ValueError(
                            f"Domain {domain} is already in module {module}"
                        )
            else:
                raise ValueError(f"Module {module} does not exist")

    def add_domain(self, module: str, domain: str) -> None:
        """
        Adds a specific domain to the list of domains attached to one module of the rpository.
        :param module:
        :param domain:
        :return:
        :raises ValueError: if module does not exist ou domain already exists
        """
        if module in self.modules:
            if module not in self.domains.keys():
                self[["domains", module]] = [domain]
            elif domain not in self[["domains", module]]:
                self[["domains", module]].append(domain)
            else:
                raise ValueError(f"Domain {domain} already exists in module {module}")
        else:
            raise ValueError(f"Module {module} does not exist")

    def remove_domain(self, module: str, domain: str) -> None:
        """
        Removes a specific domain from the list of domains attached to one module of the repository.
        :param module:
        :param domain:
        :return:
        :raises ValueError: if module does not exist or domain does not exist
        """
        if module in self.domains:
            if domain in self.domains[module]:
                self[["domains", module]].remove(domain)
            else:
                raise ValueError(f"Domain {domain} does not exist in module {module}")
        else:
            raise ValueError(f"Module {module} does not exist")

    def clean_domains(self) -> None:
        """
        Removes all domains from the list of  domains.
        :return:
        """
        self["domains"] = self._new_section({})

    # --- details.flags helpers ---
    @property
    def flags(self) -> dict:
        """
        Property exposing details.flags dictionary.
        """
        return self[["details", "flags"]]

    @flags.setter
    def flags(self, values: dict) -> None:
        if not isinstance(values, dict):
            raise TypeError(f"flags must be a dictionary, not {type(values)}")
        # Replace flags with provided mapping
        self[["details", "flags"]] = values

    def add_flag(self, name: str, value) -> None:
        if name in self[["details", "flags"]]:
            raise ValueError(f"Flag {name} already exists")
        self[["details", "flags", name]] = value

    def remove_flag(self, name: str) -> None:
        if name not in self[["details", "flags"]]:
            raise ValueError(f"Flag {name} does not exist")
        del self[["details", "flags"]][name]

    def update_flag(self, name: str, value) -> None:
        if name not in self[["details", "flags"]]:
            raise ValueError(f"Flag {name} does not exist")
        self[["details", "flags", name]] = value

    def clean_flags(self) -> None:
        self[["details", "flags"]] = self._new_section({})

    # --- paths.repository helpers ---
    @property
    def repository(self) -> str:
        return self[["paths", "repository"]]

    @repository.setter
    def repository(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError(f"repository must be a string, not {type(value)}")
        self[["paths", "repository"]] = value

    def add_repository(self, path: str) -> None:
        if self[["paths", "repository"]]:
            raise ValueError("Repository path already set")
        self[["paths", "repository"]] = path

    def remove_repository(self) -> None:
        if not self[["paths", "repository"]]:
            raise ValueError("Repository path is already empty")
        self[["paths", "repository"]] = ""

    def update_repository(self, path: str) -> None:
        self[["paths", "repository"]] = path

    def clean_repository(self) -> None:
        self[["paths", "repository"]] = ""

    # --- languages.hierarchy helpers ---
    @property
    def hierarchy(self):
        return self[["languages", "hierarchy"]]

    @hierarchy.setter
    def hierarchy(self, value: dict) -> None:
        if not isinstance(value, dict):
            raise TypeError(f"hierarchy must be a dictionary, not {type(value)}")
        self[["languages", "hierarchy"]] = self._new_section(value)

    def add_hierarchy(self, base: str, variants) -> None:
        # Accept a single variant or a list of variants
        if isinstance(variants, str):
            variants = [variants]
        elif not isinstance(variants, list):
            raise TypeError("variants must be a string or a list of strings")

        if base not in self[["languages", "hierarchy"]]:
            self[["languages", "hierarchy", base]] = []
        for v in variants:
            if v not in self[["languages", "hierarchy", base]]:
                self[["languages", "hierarchy", base]].append(v)
            else:
                raise ValueError(f"Variant {v} already exists for base {base}")

    def remove_hierarchy(self, base: str, variant: str | None = None) -> None:
        if base not in self[["languages", "hierarchy"]]:
            raise ValueError(f"Base language {base} does not exist in hierarchy")
        if variant is None:
            # Remove the entire base entry
            del self[["languages", "hierarchy"]][base]
        else:
            if variant in self[["languages", "hierarchy", base]]:
                self[["languages", "hierarchy", base]].remove(variant)
            else:
                raise ValueError(f"Variant {variant} does not exist for base {base}")

    def update_hierarchy(self, base: str, variants: list[str]) -> None:
        if not isinstance(variants, list):
            raise TypeError("variants must be a list of strings")
        self[["languages", "hierarchy", base]] = variants

    def clean_hierarchy(self) -> None:
        self[["languages", "hierarchy"]] = self._new_section({})

    # --- authors helpers ---
    @property
    def authors(self):
        """Property exposing the authors mapping.

        Authors are stored under the top-level "authors" key as a mapping of
        author_id (UUID or any unique string) -> author dictionary having the
        following structure:
          - first_name: str
          - last_name: str
          - email: str
          - url: str
          - languages: list[str]
        """
        return self["authors"]

    @authors.setter
    def authors(self, value: dict) -> None:
        if not isinstance(value, dict):
            raise TypeError(f"authors must be a dictionary, not {type(value)}")
        # Replace the whole authors section
        self["authors"] = self._new_section(value)

    def add_author(self, author_id: str, author: dict) -> None:
        """Add a new author entry.

        This method mirrors the structure expected by Config.add_author outputs,
        but here you explicitly provide the identifier and the author mapping.
        """
        if not isinstance(author, dict):
            raise TypeError("author must be a dictionary")
        required = {"first_name", "last_name", "email", "url", "languages"}
        missing = required - set(author.keys())
        if missing:
            raise KeyError(f"author is missing required keys: {sorted(missing)}")
        if not isinstance(author.get("languages"), list):
            raise TypeError("author['languages'] must be a list of strings")
        if author_id in self["authors"].keys():
            raise ValueError(f"Author '{author_id}' already exists")
        # Ensure authors sub-dicts are StrictNestedDictionary for consistency
        self[["authors", author_id]] = StrictNestedDictionary(
            author, default_setup=_DEFAULT_SETUP
        )

    def remove_author(self, author_id: str) -> None:
        """Remove an author by its identifier."""
        if author_id in self["authors"].keys():
            del self["authors"][author_id]
        else:
            raise ValueError(f"Author '{author_id}' does not exist")

    def update_author(self, author_id: str, updates: dict) -> None:
        """Update fields of an existing author with type checking.

        Only existing keys can be updated and their types must match the current values.
        """
        if author_id not in self["authors"].keys():
            raise ValueError(f"Author '{author_id}' does not exist")
        if not isinstance(updates, dict):
            raise TypeError("updates must be a dictionary")
        current = self[["authors", author_id]]
        for k, v in updates.items():
            if k not in current.keys():
                raise KeyError(f"Key '{k}' is not a valid field for author")
            if type(v) != type(current[k]):
                raise TypeError(
                    f"Type mismatch for '{k}': expected {type(current[k])}, got {type(v)}"
                )
            current[k] = v

    def clean_authors(self) -> None:
        """Remove all authors."""
        self["authors"] = self._new_section({})

    # --- translators helpers ---
    def add_translator(
        self,
        name: str,
        url: str,
        status: str,
        api_key: str,
        supported_languages: list,
        translation_type: str | None = None,
        cost_per_translation: float | None = None,
        request_limit: int | None = None,
        key_expiration: str | None = None,
        priority: int | None = None,
        success_rate: float | None = None,
        max_text_size: int | None = None,
        payment_plan: str | None = None,
    ) -> None:
        """
        Add a new translator entry under the top-level "translators" mapping.

        This mirrors Config.add_translator for consistency across the codebase
        and initializes all nested keys so the structure is predictable.

        :param name: Translator unique name (used as key in the mapping).
        :type name: str
        :param url: Public API base URL of the translator service.
        :type url: str
        :param status: Translator status, typically "free" or "license".
        :type status: str
        :param api_key: API key or token to authenticate calls (can be empty).
        :type api_key: str
        :param supported_languages: List of supported language codes.
        :type supported_languages: list[str]
        :param translation_type: Content specialization, e.g. "general", "technical".
        :type translation_type: str | None
        :param cost_per_translation: Optional unit price.
        :type cost_per_translation: float | None
        :param request_limit: Daily/monthly request limit.
        :type request_limit: int | None
        :param key_expiration: Expiration date of the API key in "YYYY-MM-DD" format.
        :type key_expiration: str | None
        :param priority: Selection priority among translators.
        :type priority: int | None
        :param success_rate: Estimated success rate between 0.0 and 1.0.
        :type success_rate: float | None
        :param max_text_size: Max accepted text length (characters).
        :type max_text_size: int | None
        :param payment_plan: Payment plan label (e.g., "monthly", "annual").
        :type payment_plan: str | None
        :raises ValueError: If the URL is invalid/unreachable or the expiration is in the past.
        :raises KeyError: If a translator with the same name already exists.
        :return: None
        :rtype: None
        """
        # Validate the URL using shared validator
        validation_result = validate_api_url(url)
        if validation_result["error"]:
            raise ValueError(validation_result["error"])

        # Validate key expiration if provided
        if key_expiration:
            expiration_date = datetime.strptime(key_expiration, "%Y-%m-%d")
            if expiration_date < datetime.now():
                raise ValueError(
                    f"The expiration date '{key_expiration}' is in the past."
                )

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

        # Ensure translators section exists as a StrictNestedDictionary
        if not isinstance(self["translators"], StrictNestedDictionary):
            self["translators"] = self._new_section({})

        # Check duplicates
        if name in self["translators"]:
            raise KeyError(f"Translator '{name}' already exists.")

        self[["translators", name]] = StrictNestedDictionary(
            translator_data, default_setup=_DEFAULT_SETUP
        )

    def update_translator(self, name: str, updates: dict) -> None:
        """
        Update an existing translator's details with structural validation.

        The provided updates must match the existing nested structure (keys and
        value types). Unknown keys or type mismatches raise a ValueError.

        :param name: Translator name to update.
        :type name: str
        :param updates: Partial mapping reflecting the translator structure
            (e.g. {"technical": {"api": {"request_limit": 1000}}}).
        :type updates: dict
        :raises KeyError: If the translator does not exist.
        :raises ValueError: If updates contain unknown keys or type mismatches.
        :return: None
        :rtype: None
        """
        translators = self["translators"]
        if name not in translators:
            raise KeyError(f"Translator '{name}' does not exist.")

        existing_translator = translators[name]

        def validate_structure(expected: dict, actual: dict, path: str = ""):
            for key, value in actual.items():
                full_path = f"{path}.{key}" if path else key
                if key not in expected:
                    raise ValueError(f"Invalid key '{full_path}' in updates.")
                if isinstance(expected[key], dict):
                    if not isinstance(value, dict):
                        raise ValueError(
                            f"Expected a dictionary for '{full_path}', but got '{type(value).__name__}'."
                        )
                    validate_structure(expected[key], value, full_path)
                elif not isinstance(value, type(expected[key])):
                    raise ValueError(
                        f"Type mismatch for '{full_path}': expected '{type(expected[key]).__name__}', got '{type(value).__name__}'."
                    )

        validate_structure(existing_translator, updates)

        def apply_updates(target: dict, source: dict):
            for key, value in source.items():
                if isinstance(value, dict):
                    apply_updates(target[key], value)
                else:
                    target[key] = value

        apply_updates(existing_translator, updates)

    def remove_translator(self, name: str) -> bool:
        """
        Remove a translator by name.

        :param name: Translator unique name.
        :type name: str
        :returns: True if the translator was removed, False if it did not exist.
        :rtype: bool
        """
        translators = self["translators"]
        if name in translators:
            translators.pop(name)
            if not translators:
                self["translators"] = self._new_section({})
            return True
        return False

    def clean_translators(self) -> None:
        """
        Remove all translators and reset the section to an empty mapping.

        :return: None
        :rtype: None
        """
        self["translators"] = self._new_section({})

    def add_value(self, path: list[str], value: Any) -> None:
        """
        Add a value in the repository

        :param path: path (hierarchical key of nested dictionary) of the value to add.
        :type path: list[str]
        :param value: value to add.
        :type value: Any
        :return: void function
        :rtype: None
        :raises KeyError: If the value does not exist.
        :raises TypeError: If the value is different from the expected type in the repository.
        :raises ValueError: If the value already exist in the repository or the parameter is empty.
        """

        if not self.dict_paths().__contains__(path):
            raise KeyError(f"Path '{path}' does not exist in the repository.")

        if type(value) != type(self[path]):
            raise TypeError(f"type of {value} must be {type(self[path])}")

        if not self[path] and (value is not None or not value):
            raise ValueError(
                f"Value '{value}' is not a valid value or {path} is not empty."
            )

        self[path] = value

    def update_value(self, path: list[str], value: Any) -> None:
        """
        Update an existing value in the repository.

        :param path: hierarchical key (list of str) pointing to the value to update.
        :type path: list[str]
        :param value: new value to set.
        :type value: Any
        :return: None
        :rtype: None
        :raises KeyError: If the path does not exist in the repository.
        :raises TypeError: If the value type differs from the existing value type.
        :raises ValueError: If the current value is empty (use add_value instead).
        """
        if not self.dict_paths().__contains__(path):
            raise KeyError(f"Path '{path}' does not exist in the repository.")

        if type(value) != type(self[path]):
            raise TypeError(f"type of {value} must be {type(self[path])}")

        # For update, ensure there is already a value (non-empty) present
        if not self[path]:
            raise ValueError(
                f"Cannot update empty value at {path}. Use add_value instead."
            )

        self[path] = value

    def remove_value(self, path: list[str]) -> None:
        """
        Remove a value from the repository by resetting it to its empty/default value.

        This does not delete schema keys; it resets them to an empty placeholder
        according to their type.

        :param path: hierarchical key (list of str) of the value to remove.
        :type path: list[str]
        :return: None
        :rtype: None
        :raises KeyError: If the path does not exist in the repository.
        :raises ValueError: If the value is already empty.
        """
        if not self.dict_paths().__contains__(path):
            raise KeyError(f"Path '{path}' does not exist in the repository.")

        current = self[path]
        # If already empty/falsy, consider it removed
        if not current:
            raise ValueError(f"Value at {path} is already empty.")

        # Compute an empty/default value according to current type
        if isinstance(current, StrictNestedDictionary):
            empty_val = self._new_section({})
        elif isinstance(current, dict):
            empty_val = {}
        elif isinstance(current, list):
            empty_val = []
        elif isinstance(current, str):
            empty_val = ""
        elif isinstance(current, bool):
            empty_val = False
        elif isinstance(current, int):
            empty_val = 0
        elif isinstance(current, float):
            empty_val = 0.0
        else:
            # Fallback to None for unknown types
            empty_val = None

        self[path] = empty_val

    def clean_value(self, path: list[str]) -> None:
        """
        Clean a value in the repository by resetting it to its empty/default value,
        regardless of its current state.

        :param path: hierarchical key (list of str) of the value to clean.
        :type path: list[str]
        :return: None
        :rtype: None
        :raises KeyError: If the path does not exist in the repository.
        """
        if not self.dict_paths().__contains__(path):
            raise KeyError(f"Path '{path}' does not exist in the repository.")

        current = self[path]
        if isinstance(current, StrictNestedDictionary):
            empty_val = self._new_section({})
        elif isinstance(current, dict):
            empty_val = {}
        elif isinstance(current, list):
            empty_val = []
        elif isinstance(current, str):
            empty_val = ""
        elif isinstance(current, bool):
            empty_val = False
        elif isinstance(current, int):
            empty_val = 0
        elif isinstance(current, float):
            empty_val = 0.0
        else:
            empty_val = None

        self[path] = empty_val
