"""
Repository module
=================

This module is in charge of repositories management. A repository is seen às the directory hierarchy to store
translations based on languages and domains used in applications' modules.



"""
from datetime import datetime
from ndict_tools import StrictNestedDictionary


class Repository(StrictNestedDictionary):
    """
    A class for handling i18n_tools repository structure.

    This class provides functionality to build and organize an i18n_tools repository.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(default_setup={"indent": 2})
        self["details"] = StrictNestedDictionary({
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
                    }, default_setup={"indent": 2})
        self["paths"] = StrictNestedDictionary({
                        "root": "",
                        "repository": "",
                        "config": "",
                        "backup": "",
                        "settings": "i18n-tools.yaml",
                        # May be changed for .json or .toml
                        "modules": [],
                    }, default_setup={"indent": 2})
        self["domains"] = StrictNestedDictionary({}, default_setup={"indent": 2})
        self["languages"] =StrictNestedDictionary({
            "source": "",
            "hierarchy": {},
            "fallback": "",
        }, default_setup={"indent": 2})
        self["translators"] =StrictNestedDictionary({}, default_setup={"indent": 2})
        self["authors"] =StrictNestedDictionary({}, default_setup={"indent": 2})
