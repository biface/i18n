"""
Repository module
=================

This module is in charge of repositories management. A repository is seen às the directory hierarchy to store
translations based on languages and domains used in applications' modules.



"""

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
                "creation_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "language": "",
                "language_team": "",
                "flags": {
                    "fuzzy": True,
                    "python-format": True,
                },
                "report-bugs-to": "",
            }
        )
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
