"""
Test module for Repository class in module i18n-tools/models
"""

import re

import pytest
from bandit.core.blacklisting import report_issue
from ndict_tools import StrictNestedDictionary

from i18n_tools.models.repository import Repository


@pytest.fixture(scope="class")
def test_repository(tmp_module_repository):
    tmp_module_repository[4].load()
    return tmp_module_repository[4].application


class TestRepositoryInit:

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


class TestRepositoryProperties:

    def test_repository_get_name(self, test_repository):
        assert test_repository.name == "fsm-tools"

    def test_repository_set_name(self, test_repository):
        test_repository.name = "automata-tools"
        assert test_repository.name == "automata-tools"

    def test_repository_get_config(self, tmp_module_repository, test_repository):
        assert (
            test_repository.config
            == tmp_module_repository[0][0]
            + "/repository-test/fsm_tools/locales/_i18n_tools/i18n-tools.yaml"
        )

    def test_repository_set_config(self, tmp_module_repository, test_repository):
        old_config = test_repository.config
        old_config_path = test_repository[["paths", "config"]]
        new_config = (
            tmp_module_repository[0][0]
            + "/repository-test/fsm_tools/locales/_i18n_tools/i18n-tools.toml"
        )
        test_repository.config = new_config
        assert test_repository[["paths", "config"]] == old_config_path
        assert test_repository[["paths", "settings"]] == "i18n-tools.toml"
        test_repository.config = old_config
        assert test_repository[["paths", "settings"]] == "i18n-tools.yaml"

    def test_repository_get_repository(self, tmp_module_repository, test_repository):
        assert (
            test_repository.repository
            == tmp_module_repository[0][0] + "/repository-test"
        )

    def test_repository_set_repository(self, tmp_module_repository, test_repository):
        test_repository.repository = tmp_module_repository[0][0] + "/test-function"
        assert (
            test_repository[["paths", "repository"]]
            == tmp_module_repository[0][0] + "/test-function"
        )
        test_repository[["paths", "repository"]] = (
            tmp_module_repository[0][0] + "/repository-test"
        )

    def test_repository_get_creation_date(self, test_repository):
        assert test_repository.creation_date == "2024-08-16 14:00"

    def test_repository_get_updated_date(self, test_repository):
        assert test_repository.updated_date == "2025-09-14 14:54"

    def test_repository_set_updated_date(self, test_repository):
        test_repository.updated_date = "2025-09-14"
        assert test_repository.updated_date == "2025-09-14 00:00"
        test_repository.updated_date = "2025-09-14 15:01"
        assert test_repository.updated_date == "2025-09-14 15:01"
        test_repository.updated_date = "2025-09-14 15:02:34"
        assert test_repository.updated_date == "2025-09-14 15:02"
        assert test_repository.creation_date == "2024-08-16 14:00"
        with pytest.raises(
            ValueError,
            match=re.escape(
                "updated_date must be a string representing a date/time in ISO format or '%Y-%m-%d %H:%M[:%S]'"
            ),
        ):
            test_repository.updated_date = "14/09/2025"

    @pytest.mark.parametrize(
        "module",
        [
            "fsm_tools",
            "fsm_tools/turing",
            "fsm_tools/lba",
            "django-fsm_tools",
            "django-fsm_tools/context",
        ],
    )
    def test_repository_get_modules(self, test_repository, module):
        assert module in test_repository.modules

    def test_repository_set_modules(self, test_repository):
        test_repository.modules = [
            "fsm_tools",
            "fsm_tools/lba",
            "fsm_tools/turing",
            "fsm_tools/pda",
            "django-fsm_tools",
            "django-fsm_tools/context",
        ]
        assert "fsm_tools/pda" in test_repository[["paths", "modules"]]

    @pytest.mark.parametrize(
        "module, domains",
        [
            ("fsm_tools", ["usage", "model"]),
            ("fsm_tools/lba", ["information", "error"]),
            ("fsm_tools/turing", ["information", "error"]),
            ("django-fsm_tools", ["usage", "information", "error"]),
        ],
    )
    def test_repository_get_domains(self, test_repository, module, domains):
        assert test_repository.domains[module] == domains
        print(test_repository)

    def test_repository_set_domains(self, test_repository):
        assert len(test_repository.domains) == 5
        test_repository["domains"] = test_repository._new_section({})
        assert len(test_repository["domains"]) == 0
        test_repository.domains = {
            "fsm_tools": ["usage", "model"],
            "fsm_tools/lba": ["information", "error"],
            "fsm_tools/turing": ["information", "error"],
            "fsm_tools/pda": ["information", "error"],
            "django-fsm_tools": ["usage", "information", "error"],
            "django-fsm_tools/context": ["usage", "information", "error", "output"],
        }
        assert len(test_repository["domains"]) == 6

    @pytest.mark.parametrize(
        "module, domain, error_msg",
        [
            (
                "fsm_tools/pda",
                "information",
                "Domain information is already in module fsm_tools/pda",
            ),
            ("fsm_tools/fsm", "information", "Module fsm_tools/fsm does not exist"),
        ],
    )
    def test_repository_set_domains_failed(
        self, test_repository, module, domain, error_msg
    ):
        with pytest.raises(ValueError, match=re.escape(error_msg)):
            test_repository.domains = {module: [domain]}

    @pytest.mark.parametrize(
        "module, domains",
        [
            ("fsm_tools", ["usage", "model"]),
            ("fsm_tools/lba", ["information", "error"]),
            ("fsm_tools/turing", ["information", "error"]),
            ("fsm_tools/pda", ["information", "error"]),
            ("django-fsm_tools", ["usage", "information", "error"]),
        ],
    )
    def test_repository_control_domain(self, test_repository, module, domains):
        assert test_repository.domains[module] == domains

    @pytest.mark.parametrize(
        "fallback, languages", [("fr", ["fr-FR"]), ("en", ["en-US", "en-GB"])]
    )
    def test_repository_get_hierarchy(self, test_repository, fallback, languages):
        for lang in languages:
            assert lang in test_repository.hierarchy[fallback]


class TestRepositoryCleanModules:

    def test_repository_clean_modules(self, test_repository):
        assert len(test_repository.modules) != 0
        assert len(test_repository.domains) != 0
        test_repository.clean_modules()
        assert len(test_repository[["paths", "modules"]]) == 0
        assert len(test_repository["domains"]) == 0


class TestRepositoryCleanDomains:

    def test_repository_clean_domains(self, test_repository):
        assert len(test_repository.domains) != 0
        assert len(test_repository.modules) != 0
        test_repository.clean_domains()
        assert len(test_repository["domains"]) == 0
        assert len(test_repository[["paths", "modules"]]) != 0


class TestRepositoryMethods:

    def test_repository_add_module(self, test_repository):
        test_repository.add_module("fsm_tools/pda")
        assert "fsm_tools/pda" in test_repository.modules

    @pytest.mark.parametrize(
        "module, error_msg",
        [
            ("fsm_tools", "Module fsm_tools already exists"),
            ("fsm_tools/turing", "Module fsm_tools/turing already exists"),
            ("fsm_tools/lba", "Module fsm_tools/lba already exists"),
            ("django-fsm_tools", "Module django-fsm_tools already exists"),
            (
                "django-fsm_tools/context",
                "Module django-fsm_tools/context already exists",
            ),
            ("fsm_tools/pda", "Module fsm_tools/pda already exists"),
        ],
    )
    def test_repository_add_modules_failed(self, test_repository, module, error_msg):
        with pytest.raises(ValueError, match=re.escape(error_msg)):
            test_repository.add_module(module)

    def test_repository_remove_module(self, test_repository):
        test_repository.remove_module("fsm_tools/pda")
        assert "fsm_tools/pda" not in test_repository.modules
        assert "fsm_tools/pda" not in test_repository["domains"].keys()

    def test_repository_remove_modules_failed(self, test_repository):
        with pytest.raises(
            ValueError, match=re.escape("Module fsm_tools/pda does not exist")
        ):
            test_repository.remove_module("fsm_tools/pda")
        test_repository.add_module("fsm_tools/pda")

    @pytest.mark.parametrize(
        "module, domain, expected",
        [
            ("fsm_tools/pda", "information", ["information"]),
            ("fsm_tools/pda", "error", ["information", "error"]),
            ("django-fsm_tools/context", "information", ["information", "error"]),
        ],
    )
    def test_repository_add_domains(self, test_repository, module, domain, expected):
        test_repository.add_domain(module, domain)
        for d in expected:
            assert d in test_repository.domains[module]

    @pytest.mark.parametrize(
        "module, domain, error_msg",
        [
            (
                "fsm_tools/pda",
                "information",
                "Domain information already exists in module fsm_tools/pda",
            ),
            (
                "fsm_tools/pda",
                "error",
                "Domain error already exists in module fsm_tools/pda",
            ),
            ("fsm_tools/fsm", "error", "Module fsm_tools/fsm does not exist"),
        ],
    )
    def test_repository_add_domains_failed(
        self, test_repository, module, domain, error_msg
    ):
        with pytest.raises(ValueError, match=re.escape(error_msg)):
            test_repository.add_domain(module, domain)

    @pytest.mark.parametrize(
        "module, domain, expected",
        [
            ("fsm_tools/pda", "information", ["error"]),
            ("django-fsm_tools", "usage", ["information", "error"]),
            ("django-fsm_tools/context", "output", ["usage", "information"]),
        ],
    )
    def test_repository_remove_domains(self, test_repository, module, domain, expected):
        test_repository.remove_domain(module, domain)
        for domain in expected:
            assert domain in test_repository[["domains", module]]

    @pytest.mark.parametrize(
        "module, domain, error_msg",
        [
            (
                "fsm_tools/pda",
                "information",
                "Domain information does not exist in module fsm_tools/pda",
            ),
            (
                "django-fsm_tools",
                "usage",
                "Domain usage does not exist in module django-fsm_tools",
            ),
            (
                "django-fsm_tools/context",
                "output",
                "Domain output does not exist in module django-fsm_tools/context",
            ),
            ("fsm_tools/fsm", "information", "Module fsm_tools/fsm does not exist"),
        ],
    )
    def test_repository_remove_domains_failed(
        self, test_repository, module, domain, error_msg
    ):
        with pytest.raises(ValueError, match=re.escape(error_msg)):
            test_repository.remove_domain(module, domain)
