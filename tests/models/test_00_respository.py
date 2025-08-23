"""
Test module for Repository class in module i18n-tools/models
"""

import re

import pytest
from ndict_tools import StrictNestedDictionary

from i18n_tools.models.repository import Repository


class TestRepository:

    @pytest.mark.parametrize(
        "key", ["details", "paths", "domains", "languages", "translators", "authors"]
    )
    def test_repository_empty_init(self, key: str):
        repository = Repository()
        assert repository.get(key) is not None
        assert isinstance(repository.get(key), StrictNestedDictionary)
        assert ("indent", 2) in repository.get(key).__getattribute__("default_setup")

    @pytest.mark.parametrize(
        "parameters, dictionary, control",
        [
            (
                ([["details", "name"], "i18n-tools test"],),
                None,
                (
                    [["details", "name"], "i18n-tools test"],
                    [["details", "version"], ""],
                ),
            ),
            (
                ([["paths", "root"], "/path/to/root"],),
                None,
                ([["paths", "root"], "/path/to/root"], [["details", "version"], ""]),
            ),
            (
                (
                    [["details", "name"], "i18n-tools test"],
                    [["details", "version"], "1.0.0"],
                ),
                None,
                (
                    [["details", "name"], "i18n-tools test"],
                    [["details", "version"], "1.0.0"],
                ),
            ),
            (
                None,
                {"details": {"name": "i18n-tools test", "version": "1.0.0"}},
                (
                    [["details", "name"], "i18n-tools test"],
                    [["details", "version"], "1.0.0"],
                ),
            ),
            (
                (
                    [["details", "name"], "i18n-tools test"],
                    [["details", "version"], "1.0.0"],
                ),
                {"domains": {"test": ["help", "error"]}},
                (
                    [["details", "name"], "i18n-tools test"],
                    [["details", "version"], "1.0.0"],
                    [["domains", "test"], ["help", "error"]],
                ),
            ),
            (
                (["details", {"name": "i18n-tools test", "version": "1.0.0"}],),
                None,
                (
                    [["details", "name"], "i18n-tools test"],
                    [["details", "version"], "1.0.0"],
                ),
            ),
            (
                None,
                {
                    "languages": {
                        "source": "fr-FR",
                        "hierarchy": {
                            "en": ["en-GB", "en-US", "en_IE"],
                            "fr": ["fr-FR", "fr-BE"],
                        },
                        "fallback": "en",
                    }
                },
                (
                    [["languages", "source"], "fr-FR"],
                    [["languages", "hierarchy", "fr"], ["fr-FR", "fr-BE"]],
                    [["languages", "fallback"], "en"],
                ),
            ),
        ],
    )
    def test_repository_init(self, parameters, dictionary, control):
        if dictionary is None:
            repository = Repository(*parameters)
        elif parameters is None:
            repository = Repository(**dictionary)
        else:
            repository = Repository(*parameters, **dictionary)

        for paths, value in control:
            print(paths, "/", value)
            assert repository[paths] == value

    @pytest.mark.parametrize(
        "paths, value, expected",
        [
            ("detail", None, "detail is not a valid path or key"),
            (
                ["details", "version"],
                1.0,
                "['details', 'version'] : 1.0 is not a <class 'str'>",
            ),
            (
                ["paths", "modules"],
                {"test": ["help"]},
                "['paths', 'modules'] : {'test': ['help']} is not a <class 'list'>",
            ),
        ],
    )
    def test_repository_init_args_failed(self, paths, value, expected):
        with pytest.raises((TypeError, KeyError), match=re.escape(expected)):
            Repository([paths, value])

    @pytest.mark.parametrize(
        "key, value, expected",
        [
            (
                "detail",
                "i18n-tools",
                "detail is not a valid key dict_keys(['details', 'paths', 'domains', 'languages', 'translators', 'authors'])",
            ),
            ("details", "i18n-tools", "details : i18n-tools must be a dictionary"),
        ],
    )
    def test_repository_init_kargs_failed(self, key, value, expected):
        with pytest.raises((TypeError, KeyError), match=re.escape(expected)):
            d = dict([(key, value)])
            Repository(**d)
