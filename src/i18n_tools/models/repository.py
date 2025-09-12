"""
The **Repository** module represents the translation repository as a nested dictionary, inheriting from
`StrictNestedDictionary` (documented `here <https://ndict-tools.readthedocs.io/en/latest/api.html#ndict_tools.core.StrictNestedDictionary>`_).

It describes the structure and organization of translation files.

"""

from __future__ import annotations

from datetime import datetime

from ndict_tools import StrictNestedDictionary

# Shared default setup to avoid repetition
_DEFAULT_SETUP = {"indent": 2}


class Repository(StrictNestedDictionary):
    """
    A class for handling i18n_tools repository structure.

    This class provides functionality to build and organize an i18n_tools repository.
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
            if not ((isinstance(path, list) and path in self.dict_paths())) and not (
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
        return self[["details", "date", "created"]]

    @property
    def updated_date(self) -> datetime:
        """Property for the updated date stored at details.date.updated.

        Returns the value located at path ["details", "date", "updated"].
        """
        return self[["details", "date", "updated"]]

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
        else:
            raise ValueError(f"Module {module} does not exist")

    def clean_modules(self) -> None:
        """
        Removes all modules from the list of  modules.
        :return:
        """
        self.modules.clear()

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
                raise ValueError(f"Domain {domain} already exists in module {module} ")
        else:
            raise ValueError(f"Module {module} does not exist")

    def remove_domain(self, module: str, domain: str) -> None:
        """
        Removes a specific domain from the list of domains attached to one module of the rrepository.
        :param module:
        :param domain:
        :return:
        :raises ValueError: if module does not exist or domain does not exist
        """
        if module in self.domains:
            if domain in self.domains[module]:
                self[["domains", module]].remove(domain)
            else:
                raise ValueError(f"Domain {domain} does not exist in module {module} ")
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
        self[["languages", "hierarchy"]] = value

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
