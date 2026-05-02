"""
Test module for Repository class in module i18n-tools/models
"""

import re

import pytest
from ndict_tools import StrictNestedDictionary

from i18n_tools.models.repository import Repository


@pytest.fixture(scope="class")
def repository_fixture(tmp_class_repository):
    return Repository(**tmp_class_repository[4])


class TestRepositoryInit:

    @pytest.mark.parametrize(
        "key", ["details", "paths", "domains", "languages", "translators", "authors"]
    )
    def test_empty_init(self, key: str):
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
    def test_init(self, parameters, dictionary, control):
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
    def test_init_args_failed(self, paths, value, expected):
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
    def test_init_kargs_failed(self, key, value, expected):
        with pytest.raises((TypeError, KeyError), match=re.escape(expected)):
            d = dict([(key, value)])
            Repository(**d)


class TestRepositoryProperties:

    def test_get_name(self, repository_fixture):
        assert repository_fixture.name == "fsm-tools"

    def test_set_name(self, repository_fixture):
        repository_fixture.name = "automata-tools"
        assert repository_fixture.name == "automata-tools"

    def test_get_config(self, tmp_class_repository, repository_fixture):
        assert (
            repository_fixture.config
            == tmp_class_repository[0][0]
            + "/repository-test/fsm_tools/locales/_i18n_tools/i18n-tools.yaml"
        )

    def test_set_config(self, tmp_class_repository, repository_fixture):
        old_config = repository_fixture.config
        old_config_path = repository_fixture[["paths", "config"]]
        new_config = (
            tmp_class_repository[0][0]
            + "/repository-test/fsm_tools/locales/_i18n_tools/i18n-tools.toml"
        )
        repository_fixture.config = new_config
        assert repository_fixture[["paths", "config"]] == old_config_path
        assert repository_fixture[["paths", "settings"]] == "i18n-tools.toml"
        repository_fixture.config = old_config
        assert repository_fixture[["paths", "settings"]] == "i18n-tools.yaml"

    def test_get_repository(self, tmp_class_repository, repository_fixture):
        print(repository_fixture)
        assert (
            repository_fixture.repository
            == tmp_class_repository[0][0] + "/repository-test"
        )

    def test_set_repository(self, tmp_module_repository, repository_fixture):
        repository_fixture.repository = tmp_module_repository[0][0] + "/test-function"
        assert (
            repository_fixture[["paths", "repository"]]
            == tmp_module_repository[0][0] + "/test-function"
        )
        repository_fixture[["paths", "repository"]] = (
            tmp_module_repository[0][0] + "/repository-test"
        )
        assert (
            repository_fixture[["paths", "repository"]]
            == tmp_module_repository[0][0] + "/repository-test"
        )

    @pytest.mark.parametrize(
        "path, error, error_msg",
        [
            (
                ["/false/path"],
                TypeError,
                "Repository must be a string, not <class 'list'>",
            ),
            (
                "path/../test-function",
                FileNotFoundError,
                "Repository path/../test-function does not exist",
            ),
            (
                "/tmp/absolute_non_existent_path/",
                FileNotFoundError,
                "Repository /tmp/absolute_non_existent_path/ does not exist",
            ),
        ],
    )
    def test_set_repository_failed(self, repository_fixture, path, error, error_msg):
        with pytest.raises(error, match=re.escape(error_msg)):
            repository_fixture.repository = path

    def test_get_creation_date(self, repository_fixture):
        assert repository_fixture.creation_date == "2024-08-16 14:00"

    def test_get_updated_date(self, repository_fixture):
        assert repository_fixture.updated_date == "2025-09-14 14:54"

    def test_set_updated_date(self, repository_fixture):
        repository_fixture.updated_date = "2025-09-14"
        assert repository_fixture.updated_date == "2025-09-14 00:00"
        repository_fixture.updated_date = "2025-09-14 15:01"
        assert repository_fixture.updated_date == "2025-09-14 15:01"
        repository_fixture.updated_date = "2025-09-14 15:02:34"
        assert repository_fixture.updated_date == "2025-09-14 15:02"
        assert repository_fixture.creation_date == "2024-08-16 14:00"
        with pytest.raises(
            ValueError,
            match=re.escape(
                "updated_date must be a string representing a date/time in ISO format or '%Y-%m-%d %H:%M[:%S]'"
            ),
        ):
            repository_fixture.updated_date = "14/09/2025"

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
    def test_get_modules(self, repository_fixture, module):
        assert module in repository_fixture.modules

    def test_set_modules(self, repository_fixture):
        repository_fixture.modules = [
            "fsm_tools",
            "fsm_tools/lba",
            "fsm_tools/turing",
            "fsm_tools/pda",
            "django-fsm_tools",
            "django-fsm_tools/context",
        ]
        assert "fsm_tools/pda" in repository_fixture[["paths", "modules"]]

    @pytest.mark.parametrize(
        "module, domains",
        [
            ("fsm_tools", ["usage", "model"]),
            ("fsm_tools/lba", ["information", "error"]),
            ("fsm_tools/turing", ["information", "error"]),
            ("django-fsm_tools", ["usage", "information", "error"]),
        ],
    )
    def test_get_domains(self, repository_fixture, module, domains):
        assert repository_fixture.domains[module] == domains

    def test_set_domains(self, repository_fixture):
        assert len(repository_fixture.domains) == 5
        repository_fixture["domains"] = repository_fixture._new_section({})
        assert len(repository_fixture["domains"]) == 0
        repository_fixture.domains = {
            "fsm_tools": ["usage", "model"],
            "fsm_tools/lba": ["information", "error"],
            "fsm_tools/turing": ["information", "error"],
            "fsm_tools/pda": ["information", "error"],
            "django-fsm_tools": ["usage", "information", "error"],
            "django-fsm_tools/context": ["usage", "information", "error", "output"],
        }
        assert len(repository_fixture["domains"]) == 6

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
    def test_set_domains_failed(self, repository_fixture, module, domain, error_msg):
        with pytest.raises(ValueError, match=re.escape(error_msg)):
            repository_fixture.domains = {module: [domain]}

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
    def test_control_domain(self, repository_fixture, module, domains):
        assert repository_fixture.domains[module] == domains

    @pytest.mark.parametrize(
        "fallback, languages", [("fr", ["fr-FR"]), ("en", ["en-US", "en-GB"])]
    )
    def test_get_hierarchy(self, repository_fixture, fallback, languages):
        for lang in languages:
            assert lang in repository_fixture.hierarchy[fallback]

    @pytest.mark.parametrize(
        "hierarchy, expected",
        [
            ({"it": ["it-IT"]}, [("it", ["it-IT"])]),
            (
                {"fr": ["fr-FR"], "en": ["en-US", "en-GB"]},
                [("fr", ["fr-FR"]), ("en", ["en-US", "en-GB"])],
            ),
        ],
    )
    def test_set_hierarchy(self, repository_fixture, hierarchy, expected):
        repository_fixture.hierarchy = hierarchy
        for fallback, l_lang in expected:
            for lang in l_lang:
                assert lang in repository_fixture.hierarchy[fallback]

    @pytest.mark.parametrize(
        "hierarchy, error_msg",
        [
            (["it", ["it-IT"]], "hierarchy must be a dictionary, not <class 'list'>"),
            (
                {"fr": [1], "en": ["en-US", "en-GB"]},
                "Language hierarchy must be a list of string, not <class 'int'>",
            ),
            (
                {"fr": ["fr-iso/FR"], "en": ["en-US", "en-GB"]},
                "Language in hierarchy value must be a compliant IETF Tag, not fr-iso/FR",
            ),
        ],
    )
    def test_set_hierarchy_failed(self, repository_fixture, hierarchy, error_msg):
        with pytest.raises((TypeError, ValueError), match=re.escape(error_msg)):
            repository_fixture.hierarchy = hierarchy

    @pytest.mark.parametrize(
        "key, values",
        [
            (
                "7d097ac4-ba77-4333-a63f-76d48a75b38c",
                [
                    ("email", "john@doe.com"),
                    ("languages", ["fr", "en"]),
                ],
            ),
            (
                "baf52b25-d1ed-4651-a3e6-273850901cf0",
                [
                    ("email", "jeanne@doe.com"),
                    ("first_name", "Jeanne"),
                    ("languages", ["fr", "en"]),
                    ("last_name", "Doe"),
                ],
            ),
        ],
    )
    def test_get_authors(self, repository_fixture, key, values):
        print(repository_fixture["paths"])
        for index, value in values:
            assert repository_fixture.authors[key][index] == value

    def test_set_authors(self, repository_fixture):
        uuid_1 = "c64673e4-5d7d-4798-a22f-d1ea7cc807c1"
        uuid_2 = "00b482a7-9ace-489c-8c48-6a8ec48d6876"
        repository_fixture.authors = {
            uuid_1: {
                "email": "jean@dupond.com",
                "first_name": "Jean",
                "last_name": "Dupond",
                "languages": ["fr"],
                "url": "",
            },
            uuid_2: {
                "email": "jeanne@dupond.com",
                "first_name": "Jeanne",
                "last_name": "Dupond",
                "languages": ["en"],
                "url": "",
            },
        }
        assert repository_fixture[["authors", uuid_1, "email"]] == "jean@dupond.com"
        assert repository_fixture[["authors", uuid_2, "languages"]] == ["en"]

    def test_set_authors_failed(self, repository_fixture):
        uuid_1 = "c64673e4-5d7d-4798-a22f-d1ea7cc807c1"
        uuid_2 = "00b482a7-9ace-489c-8c48-6a8ec48d6876"
        with pytest.raises(
            TypeError,
            match=re.escape("authors must be a dictionary, not <class 'list'>"),
        ):
            repository_fixture.authors = [
                uuid_1,
                {
                    "email": "jean@dupond.com",
                    "first_name": "Jean",
                    "last_name": "Dupond",
                    "languages": ["fr"],
                    "url": "",
                },
                uuid_2,
                {
                    "email": "jeanne@dupond.com",
                    "first_name": "Jeanne",
                    "last_name": "Dupond",
                    "languages": ["en"],
                    "url": "",
                },
            ]

    @pytest.mark.parametrize(
        "path, values",
        [
            (
                ["details"],
                [("name", "GoogleTranslate"), ("url", "https://translate.google.com")],
            ),
            (["pricing"], [("cost_per_translation", None), ("payment_plan", None)]),
            (["technical", "api"], [("key", "your_api_key"), ("request_limit", 10000)]),
        ],
    )
    def test_get_translators(self, repository_fixture, path, values):
        d = repository_fixture.translators["GoogleTranslate"]
        assert isinstance(d[path], StrictNestedDictionary)
        for key, value in values:
            assert d[path][key] == value

    def test_set_translators(self, repository_fixture):
        repository_fixture.translators = {
            "GoogleTranslate": {
                "details": {
                    "name": "GoogleTranslate",
                    "status": "Free",
                    "url": "https://translate.google.com",
                },
                "pricing": {"cost_per_translation": None, "payment_plan": None},
                "technical": {
                    "api": {
                        "key": "your_api_key",
                        "key_expiration": "2025-12-31",
                        "request_limit": 10000,
                    },
                    "performance": {
                        "max_text_size": 5000,
                        "priority": 1,
                        "success_rate": 99.5,
                    },
                },
            },
            "DeeplTranslate": {
                "details": {
                    "name": "DeepL Translate",
                    "status": "business",
                    "url": "https://www.deepl.com",
                },
                "pricing": {"cost_per_translation": None, "payment_plan": "Annual"},
                "technical": {
                    "api": {
                        "key": "your_api_key",
                        "key_expiration": "2025-12-31",
                        "request_limit": 10000,
                    },
                    "performance": {
                        "max_text_size": 5000,
                        "priority": 1,
                        "success_rate": 99.5,
                    },
                },
            },
        }
        assert len(repository_fixture.translators) == 2

    def test_set_translators_failed(self, repository_fixture):
        with pytest.raises(
            TypeError,
            match=re.escape("translators must be a dictionary, not <class 'list'>"),
        ):
            repository_fixture.translators = [
                (
                    "GoogleTranslate",
                    {
                        "details": {
                            "name": "GoogleTranslate",
                            "status": "Free",
                            "url": "https://translate.google.com",
                        },
                        "pricing": {"cost_per_translation": None, "payment_plan": None},
                        "technical": {
                            "api": {
                                "key": "your_api_key",
                                "key_expiration": "2025-12-31",
                                "request_limit": 10000,
                            },
                            "performance": {
                                "max_text_size": 5000,
                                "priority": 1,
                                "success_rate": 99.5,
                            },
                        },
                    },
                ),
                (
                    "DeeplTranslate",
                    {
                        "details": {
                            "name": "DeepL Translate",
                            "status": "business",
                            "url": "https://www.deepl.com",
                        },
                        "pricing": {
                            "cost_per_translation": None,
                            "payment_plan": "Annual",
                        },
                        "technical": {
                            "api": {
                                "key": "your_api_key",
                                "key_expiration": "2025-12-31",
                                "request_limit": 10000,
                            },
                            "performance": {
                                "max_text_size": 5000,
                                "priority": 1,
                                "success_rate": 99.5,
                            },
                        },
                    },
                ),
            ]


class TestRepositoryMethods:

    def test_add_module(self, repository_fixture):
        repository_fixture.add_module("fsm_tools/pda")
        assert "fsm_tools/pda" in repository_fixture.modules

    @pytest.mark.parametrize(
        "module, error, error_msg",
        [
            (["fsm_tools"], TypeError, "Module must be a string, not <class 'list'>"),
            ("fsm_tools", ValueError, "Module fsm_tools already exists"),
            ("fsm_tools/turing", ValueError, "Module fsm_tools/turing already exists"),
            ("fsm_tools/lba", ValueError, "Module fsm_tools/lba already exists"),
            ("django-fsm_tools", ValueError, "Module django-fsm_tools already exists"),
            (
                "django-fsm_tools/context",
                ValueError,
                "Module django-fsm_tools/context already exists",
            ),
            ("fsm_tools/pda", ValueError, "Module fsm_tools/pda already exists"),
        ],
    )
    def test_add_modules_failed(self, repository_fixture, module, error, error_msg):
        with pytest.raises(error, match=re.escape(error_msg)):
            repository_fixture.add_module(module)

    def test_remove_module(self, repository_fixture):
        repository_fixture.remove_module("fsm_tools/pda")
        assert "fsm_tools/pda" not in repository_fixture.modules
        assert "fsm_tools/pda" not in repository_fixture["domains"].keys()

    def test_remove_modules_failed(self, repository_fixture):
        with pytest.raises(
            ValueError, match=re.escape("Module fsm_tools/pda does not exist")
        ):
            repository_fixture.remove_module("fsm_tools/pda")
        repository_fixture.add_module("fsm_tools/pda")

    @pytest.mark.parametrize(
        "module, domain, expected",
        [
            ("fsm_tools/pda", "information", ["information"]),
            ("fsm_tools/pda", "error", ["information", "error"]),
            ("django-fsm_tools/context", "information", ["information", "error"]),
        ],
    )
    def test_add_domain(self, repository_fixture, module, domain, expected):
        repository_fixture.add_domain(module, domain)
        for d in expected:
            assert d in repository_fixture.domains[module]

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
    def test_add_domain_failed(self, repository_fixture, module, domain, error_msg):
        with pytest.raises(ValueError, match=re.escape(error_msg)):
            repository_fixture.add_domain(module, domain)

    @pytest.mark.parametrize(
        "module, domain, expected",
        [
            ("fsm_tools/pda", "information", ["error"]),
            ("django-fsm_tools", "usage", ["information", "error"]),
            ("django-fsm_tools/context", "output", ["usage", "information"]),
        ],
    )
    def test_remove_domain(self, repository_fixture, module, domain, expected):
        repository_fixture.remove_domain(module, domain)
        for domain in expected:
            assert domain in repository_fixture[["domains", module]]

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
    def test_remove_domain_failed(self, repository_fixture, module, domain, error_msg):
        with pytest.raises(ValueError, match=re.escape(error_msg)):
            repository_fixture.remove_domain(module, domain)

    @pytest.mark.parametrize(
        "fallback, languages, expected",
        [
            ("fr", "fr-BE", ["fr-FR", "fr-BE"]),
            ("it", ["it-IT", "it-CH"], ["it-IT", "it-CH"]),
            ("se", ["se-FI", "se-NO"], ["se-FI", "se-NO"]),
            ("se", "se-SE", ["se-FI", "se-NO", "se-SE"]),
        ],
    )
    def test_add_hierarchy(self, repository_fixture, fallback, languages, expected):
        repository_fixture.add_hierarchy(fallback, languages)
        assert repository_fixture[["languages", "hierarchy", fallback]] == expected

    @pytest.mark.parametrize(
        "fallback, languages, error, error_msg",
        [
            (
                ["rf"],
                "rf-BE",
                TypeError,
                "Fallback must be a string, not <class 'list'>",
            ),
            (
                "rf",
                "rf-BE",
                ValueError,
                "Fallback language must be a compliant IETF Tag, not rf",
            ),
            (
                "fr",
                1,
                TypeError,
                "Languages must be a string or a list of strings, not <class 'int'>",
            ),
            (
                "fr",
                [1, "fr-MO"],
                TypeError,
                "Language hierarchy must be a list of string, not <class 'int'>",
            ),
            (
                "fr",
                "fr-EB",
                ValueError,
                "Language in hierarchy value must be a compliant IETF Tag, not fr-EB",
            ),
            (
                "fr",
                "fr-BE",
                ValueError,
                "Language fr-BE already exists for fallback fr",
            ),
        ],
    )
    def test_add_hierarchy_failed(
        self, repository_fixture, fallback, languages, error, error_msg
    ):
        with pytest.raises(error, match=re.escape(error_msg)):
            repository_fixture.add_hierarchy(fallback, languages)

    @pytest.mark.parametrize(
        "fallback, language, expected",
        [
            ("fr", "fr-BE", ["fr-FR"]),
            ("fr", "fr-FR", []),
            ("en", "en-US", ["en-GB"]),
            ("se", "se-SE", ["se-FI", "se-NO"]),
        ],
    )
    def test_remove_hierarchy(self, repository_fixture, fallback, language, expected):
        repository_fixture.remove_hierarchy(fallback, language)
        assert repository_fixture[["languages", "hierarchy", fallback]] == expected

    def test_remove_empty_fr(self, repository_fixture):
        assert repository_fixture[["languages", "hierarchy", "fr"]] == []
        repository_fixture.remove_hierarchy("fr", None)
        assert "fr" not in repository_fixture[["languages", "hierarchy"]].keys()

    @pytest.mark.parametrize(
        "fallback, language, error_msg",
        [
            ("sv", "sv-SE", "Base language sv does not exist in hierarchy"),
            ("en", "en-JM", "Language en-JM does not exist for base language en"),
            ("se", "se-SE", "Language se-SE does not exist for base language se"),
        ],
    )
    def test_remove_hierarchy_failed(
        self, repository_fixture, fallback, language, error_msg
    ):
        with pytest.raises(ValueError, match=re.escape(error_msg)):
            repository_fixture.remove_hierarchy(fallback, language)

    @pytest.mark.parametrize(
        "fallback, languages, expected",
        [
            ("fr", "fr-FR", ["fr-FR"]),
            ("it", ["it-IT", "it-CH"], ["it-IT", "it-CH"]),
            ("se", ["se-FI", "se-NO"], ["se-FI", "se-NO"]),
        ],
    )
    def test_update_hierarchy(self, repository_fixture, fallback, languages, expected):
        repository_fixture.update_hierarchy(fallback, languages)
        assert repository_fixture[["languages", "hierarchy", fallback]] == expected

    @pytest.mark.parametrize(
        "fallback, languages, error, error_msg",
        [
            (
                ["rf"],
                "rf-BE",
                TypeError,
                "Fallback must be a string, not <class 'list'>",
            ),
            (
                "rf",
                "rf-BE",
                ValueError,
                "Fallback language must be a compliant IETF Tag, not rf",
            ),
            (
                "fr",
                1,
                TypeError,
                "Languages must be a string or a list of strings, not <class 'int'>",
            ),
            (
                "fr",
                [1, "fr-MO"],
                TypeError,
                "Language hierarchy must be a list of string, not <class 'int'>",
            ),
            (
                "fr",
                "fr-EB",
                ValueError,
                "Language in hierarchy value must be a compliant IETF Tag, not fr-EB",
            ),
        ],
    )
    def test_update_hierarchy_failed(
        self, repository_fixture, fallback, languages, error, error_msg
    ):
        with pytest.raises(error, match=re.escape(error_msg)):
            repository_fixture.update_hierarchy(fallback, languages)

    @pytest.mark.parametrize(
        "author_id, auther_desc, expected",
        [
            (
                "54d961ad-59dd-41d0-899a-d7ea58170547",
                {
                    "email": "jean@dupond.com",
                    "first_name": "Jean",
                    "last_name": "Dupond",
                    "languages": ["fr"],
                    "url": "",
                },
                [
                    ("email", "jean@dupond.com"),
                    ("first_name", "Jean"),
                    ("last_name", "Dupond"),
                    ("languages", ["fr"]),
                ],
            ),
            (
                "dab8b521-2588-4eed-8360-85ddaccdfc2f",
                {
                    "email": "jeanne@dupond.com",
                    "first_name": "Jeanne",
                    "last_name": "Dupond",
                    "languages": ["en"],
                    "url": "",
                },
                [
                    ("email", "jeanne@dupond.com"),
                    ("first_name", "Jeanne"),
                    ("last_name", "Dupond"),
                    ("languages", ["en"]),
                ],
            ),
        ],
    )
    def test_add_author(self, repository_fixture, author_id, auther_desc, expected):
        repository_fixture.add_author(author_id, auther_desc)
        for key, value in expected:
            assert repository_fixture[["authors", author_id, key]] == value

    @pytest.mark.parametrize(
        "author_id, auther_desc, error, error_msg",
        [
            (
                1285,
                {
                    "email": "jean@dupond.com",
                    "first_name": "Jean",
                    "last_name": "Dupond",
                    "languages": ["fr"],
                    "url": "",
                },
                TypeError,
                "author_id must be a string",
            ),
            (
                "54d961ad-__dd-41d0-899a-d7ea58170547",
                {
                    "email": "jean@dupond.com",
                    "first_name": "Jean",
                    "last_name": "Dupond",
                    "languages": ["fr"],
                    "url": "",
                },
                ValueError,
                "author_id must be a valid UUID4 string",
            ),
            (
                "380a6cb2-962f-11f0-874a-d93c4922b5f2",
                {
                    "email": "jean@dupond.com",
                    "first_name": "Jean",
                    "last_name": "Dupond",
                    "languages": ["fr"],
                    "url": "",
                },
                ValueError,
                "author_id must be a valid UUID4 string",
            ),
        ],
    )
    def test_add_author_id_failed(
        self, repository_fixture, author_id, auther_desc, error, error_msg
    ):
        with pytest.raises(error, match=re.escape(error_msg)):
            repository_fixture.add_author(author_id, auther_desc)

    @pytest.mark.parametrize(
        "author_id, auther_desc, error, error_msg",
        [
            (
                "0b97f269-d168-408e-9e82-519800643f3f",
                {
                    "email": "jean@dupond.com",
                    "first_name": "Jean",
                    "last_name": "Dupond",
                    "languages": ["fr"],
                },
                KeyError,
                "author is missing required keys: ['url']",
            ),
            (
                "0b97f269-d168-408e-9e82-519800643f3f",
                {
                    "email": "jean@dupond.com",
                    "first_name": "Jean",
                    "languages": ["fr"],
                },
                KeyError,
                "author is missing required keys: ['last_name', 'url']",
            ),
            (
                "0b97f269-d168-408e-9e82-519800643f3f",
                {
                    "email": "jean@dupond.com",
                    "first_name": "Jean",
                    "last_name": "Dupond",
                    "languages": "fr",
                    "url": "",
                },
                TypeError,
                "author['languages'] must be a list of strings",
            ),
            (
                "0b97f269-d168-408e-9e82-519800643f3f",
                [
                    "email",
                    "jean@dupond.com",
                    "first_name",
                    "Jean",
                    "last_name",
                    "Dupond",
                    "languages",
                    ["fr"],
                    "url",
                    "",
                ],
                TypeError,
                "author must be a dictionary",
            ),
        ],
    )
    def test_add_author_payload_failed(
        self, repository_fixture, author_id, auther_desc, error, error_msg
    ):
        with pytest.raises(error, match=re.escape(error_msg)):
            repository_fixture.add_author(author_id, auther_desc)

    @pytest.mark.parametrize(
        "author_id, auther_desc, error, error_msg",
        [
            (
                "7d097ac4-ba77-4333-a63f-76d48a75b38c",
                {
                    "email": "jean@dupond.com",
                    "first_name": "Jean",
                    "last_name": "Dupond",
                    "languages": ["fr"],
                    "url": "",
                },
                ValueError,
                "Author '7d097ac4-ba77-4333-a63f-76d48a75b38c' already exists",
            ),
            (
                "baf52b25-d1ed-4651-a3e6-273850901cf0",
                {
                    "email": "jeanne@dupond.com",
                    "first_name": "Jeanne",
                    "last_name": "Dupond",
                    "languages": ["en"],
                    "url": "",
                },
                ValueError,
                "Author 'baf52b25-d1ed-4651-a3e6-273850901cf0' already exists",
            ),
        ],
    )
    def test_add_author_non_existant_failed(
        self, repository_fixture, author_id, auther_desc, error, error_msg
    ):
        with pytest.raises(error, match=re.escape(error_msg)):
            repository_fixture.add_author(author_id, auther_desc)

    @pytest.mark.parametrize(
        "author_id, auther_desc, expected",
        [
            (
                "54d961ad-59dd-41d0-899a-d7ea58170547",
                {
                    "languages": ["fr", "fr-FR", "it-IT", "en-GB"],
                    "url": "https://dupont.org",
                },
                [
                    ("first_name", "Jean"),
                    ("languages", ["fr", "fr-FR", "it-IT", "en-GB"]),
                    ("url", "https://dupont.org"),
                ],
            ),
            (
                "dab8b521-2588-4eed-8360-85ddaccdfc2f",
                {
                    "last_name": "Dupont",
                    "url": "https://dupont.org",
                },
                [
                    ("last_name", "Dupont"),
                    ("url", "https://dupont.org"),
                    ("languages", ["en"]),
                ],
            ),
            (
                "dab8b521-2588-4eed-8360-85ddaccdfc2f",
                {
                    "languages": ["fr", "fr-FR", "en", "en-GB"],
                },
                [
                    ("last_name", "Dupont"),
                    ("url", "https://dupont.org"),
                    ("languages", ["fr", "fr-FR", "en", "en-GB"]),
                ],
            ),
        ],
    )
    def test_update_author(self, repository_fixture, author_id, auther_desc, expected):
        repository_fixture.update_author(author_id, auther_desc)
        for key, value in expected:
            assert repository_fixture[["authors", author_id, key]] == value

    def test_update_author_existant_failed(self, repository_fixture):
        with pytest.raises(
            ValueError,
            match=re.escape(
                "Author '4b4bbb92-5fa4-4aa4-8c14-84409357bce7' does not exist"
            ),
        ):
            repository_fixture.update_author(
                "4b4bbb92-5fa4-4aa4-8c14-84409357bce7", {"last_name": "Dupont"}
            )

    @pytest.mark.parametrize(
        "author_id, author_desc, error, error_msg",
        [
            (
                "54d961ad-59dd-41d0-899a-d7ea58170547",
                {"firs_name": "Jean"},
                KeyError,
                "Key 'firs_name' is not a valid field for author",
            ),
            (
                "54d961ad-59dd-41d0-899a-d7ea58170547",
                ["first_name", "Jean"],
                TypeError,
                "updates must be a dictionary",
            ),
            (
                "54d961ad-59dd-41d0-899a-d7ea58170547",
                {"first_name": "Jean", "languages": "fr"},
                TypeError,
                "Type mismatch for 'languages': expected <class 'list'>, got <class 'str'>",
            ),
        ],
    )
    def test_update_author_payload_failed(
        self, repository_fixture, author_id, author_desc, error, error_msg
    ):
        with pytest.raises(error, match=re.escape(error_msg)):
            repository_fixture.update_author(author_id, author_desc)

    def test_remove_author(self, repository_fixture):
        assert len(repository_fixture.authors) == 4
        repository_fixture.remove_author("54d961ad-59dd-41d0-899a-d7ea58170547")
        assert len(repository_fixture.authors) == 3

    def test_remove_repository(self, repository_fixture):
        print(repr(repository_fixture.repository))
        assert len(repository_fixture.repository) != 0
        repository_fixture.remove_repository()
        assert len(repository_fixture.repository) == 0

    def test_remove_repository_failed(self, repository_fixture):
        with pytest.raises(
            ValueError, match=re.escape("Repository path is already empty")
        ):
            repository_fixture.remove_repository()

    def test_add_repository(self, tmp_class_repository, repository_fixture):
        repository_fixture.add_repository(tmp_class_repository[1][0])
        assert repository_fixture.repository is not None

    def test_add_repository_failed(self, tmp_class_repository, repository_fixture):
        with pytest.raises(ValueError, match=re.escape("Repository path already set")):
            repository_fixture.add_repository(tmp_class_repository[1][0])

    def test_update_repository(self, tmp_class_repository, repository_fixture):
        repository_fixture.update_repository(tmp_class_repository[2][0])
        print(repository_fixture.repository)
        assert repository_fixture.repository is not None

    @pytest.mark.parametrize(
        "false_path, error_msg",
        [
            (
                "../test-function/../package-configuration",
                "Repository '../test-function/../package-configuration' does not exist or is relative",
            ),
            (
                "test-function/fsm_tools",
                "Repository 'test-function/fsm_tools' does not exist or is relative",
            ),
        ],
    )
    def test_update_repository_failed(self, repository_fixture, false_path, error_msg):
        with pytest.raises(FileNotFoundError, match=re.escape(error_msg)):
            repository_fixture.update_repository(false_path)

    @pytest.mark.parametrize(
        "translator_name, content, expected",
        [
            (
                "DeeplTranslate",
                {
                    "details": {
                        "name": "DeepL Translate",
                        "status": "business",
                        "url": "https://www.deepl.com",
                    },
                    "pricing": {"cost_per_translation": None, "payment_plan": "Annual"},
                    "technical": {
                        "api": {
                            "key": "your_api_key",
                            "key_expiration": "2025-12-31",
                            "request_limit": 10000,
                        },
                        "performance": {
                            "max_text_size": 5000,
                            "priority": 1,
                            "success_rate": 99.5,
                        },
                    },
                },
                [
                    (
                        ["GoogleTranslate", "details"],
                        [("name", "GoogleTranslate"), ("status", "free")],
                    ),
                    (
                        ["DeeplTranslate", "pricing"],
                        [("cost_per_translation", None), ("payment_plan", "Annual")],
                    ),
                    (
                        ["DeeplTranslate", "details"],
                        [("name", "DeepL Translate"), ("status", "business")],
                    ),
                ],
            )
        ],
    )
    def test_add_translator(
        self, repository_fixture, translator_name, content, expected
    ):
        repository_fixture.add_translator(translator_name, content)
        for path, values in expected:
            for key, value in values:
                assert repository_fixture.translators[path][key] == value

    @pytest.mark.parametrize(
        "translator_name, content, error, error_msg",
        [
            (
                1000,
                {
                    "details": {
                        "name": "DeepL Translate",
                        "status": "business",
                        "url": "https://www.deepl.com",
                    },
                    "pricing": {"cost_per_translation": None, "payment_plan": "Annual"},
                    "technical": {
                        "api": {
                            "key": "your_api_key",
                            "key_expiration": "2025-12-31",
                            "request_limit": 10000,
                        },
                        "performance": {
                            "max_text_size": 5000,
                            "priority": 1,
                            "success_rate": 99.5,
                        },
                    },
                },
                TypeError,
                "Translator name must be a string",
            ),
            (
                "DeeplTranslate",
                [
                    "details",
                    {
                        "name": "DeepL Translate",
                        "status": "business",
                        "url": "https://www.deepl.com",
                    },
                    "pricing",
                    {"cost_per_translation": None, "payment_plan": "Annual"},
                    "technical",
                    {
                        "api": {
                            "key": "your_api_key",
                            "key_expiration": "2025-12-31",
                            "request_limit": 10000,
                        },
                        "performance": {
                            "max_text_size": 5000,
                            "priority": 1,
                            "success_rate": 99.5,
                        },
                    },
                ],
                TypeError,
                "Translator content must be a dictionary",
            ),
            (
                "DeeplTranslate",
                {
                    "details": {
                        "name": "DeepL Translate",
                        "status": "business",
                        "url": "https://www.deepl.com",
                    }
                },
                KeyError,
                "Translator is missing required keys: ['pricing', 'technical']",
            ),
            (
                "DeeplTranslate",
                {
                    "details": [
                        "name",
                        "DeepL Translate",
                        "status",
                        "business",
                        "url",
                        "https://www.deepl.com",
                    ],
                    "pricing": {"cost_per_translation": None, "payment_plan": "Annual"},
                    "technical": {
                        "api": {
                            "key": "your_api_key",
                            "key_expiration": "2025-12-31",
                            "request_limit": 10000,
                        },
                        "performance": {
                            "max_text_size": 5000,
                            "priority": 1,
                            "success_rate": 99.5,
                        },
                    },
                },
                TypeError,
                "Translator['details'] must be a dictionary",
            ),
            (
                "DeeplTranslate",
                {
                    "details": {
                        "name": "DeepL Translate",
                    },
                    "pricing": {"cost_per_translation": None, "payment_plan": "Annual"},
                    "technical": {
                        "api": {
                            "key": "your_api_key",
                            "key_expiration": "2025-12-31",
                            "request_limit": 10000,
                        },
                        "performance": {
                            "max_text_size": 5000,
                            "priority": 1,
                            "success_rate": 99.5,
                        },
                    },
                },
                KeyError,
                "Translator['details'] is missing required keys: ['status', 'url']",
            ),
            (
                "DeeplTranslate",
                {
                    "details": {
                        "name": ["DeepL Translate"],
                        "status": "business",
                        "url": "https://www.deepl.com",
                    },
                    "pricing": {"cost_per_translation": None, "payment_plan": "Annual"},
                    "technical": {
                        "api": {
                            "key": "your_api_key",
                            "key_expiration": "2025-12-31",
                            "request_limit": 10000,
                        },
                        "performance": {
                            "max_text_size": 5000,
                            "priority": 1,
                            "success_rate": 99.5,
                        },
                    },
                },
                TypeError,
                "Translator[['details', 'name']] must be a string",
            ),
            (
                "DeeplTranslate",
                {
                    "details": {
                        "name": "DeepL Translate",
                        "status": ["business"],
                        "url": "https://www.deepl.com",
                    },
                    "pricing": {"cost_per_translation": None, "payment_plan": "Annual"},
                    "technical": {
                        "api": {
                            "key": "your_api_key",
                            "key_expiration": "2025-12-31",
                            "request_limit": 10000,
                        },
                        "performance": {
                            "max_text_size": 5000,
                            "priority": 1,
                            "success_rate": 99.5,
                        },
                    },
                },
                TypeError,
                "Translator[['details', 'status']] must be a string",
            ),
            (
                "DeeplTranslate",
                {
                    "details": {
                        "name": "DeepL Translate",
                        "status": "business",
                        "url": ["https://www.deepl.com"],
                    },
                    "pricing": {"cost_per_translation": None, "payment_plan": "Annual"},
                    "technical": {
                        "api": {
                            "key": "your_api_key",
                            "key_expiration": "2025-12-31",
                            "request_limit": 10000,
                        },
                        "performance": {
                            "max_text_size": 5000,
                            "priority": 1,
                            "success_rate": 99.5,
                        },
                    },
                },
                TypeError,
                "Translator[['details', 'url']] must be a string",
            ),
            (
                "DeeplTranslate",
                {
                    "details": {
                        "name": "DeepL Translate",
                        "status": "business",
                        "url": "https://www_unvalide_url",
                    },
                    "pricing": {"cost_per_translation": None, "payment_plan": "Annual"},
                    "technical": {
                        "api": {
                            "key": "your_api_key",
                            "key_expiration": "2025-12-31",
                            "request_limit": 10000,
                        },
                        "performance": {
                            "max_text_size": 5000,
                            "priority": 1,
                            "success_rate": 99.5,
                        },
                    },
                },
                ValueError,
                "URL 'https://www_unvalide_url' is not a valid format.",
            ),
            (
                "DeeplTranslate",
                {
                    "details": {
                        "name": "DeepL Translate",
                        "status": "business",
                        "url": "https://www.deepl.com",
                    },
                    "pricing": ["cost_per_translation", None, "payment_plan", "Annual"],
                    "technical": {
                        "api": {
                            "key": "your_api_key",
                            "key_expiration": "2025-12-31",
                            "request_limit": 10000,
                        },
                        "performance": {
                            "max_text_size": 5000,
                            "priority": 1,
                            "success_rate": 99.5,
                        },
                    },
                },
                TypeError,
                "Translator['pricing'] must be a dictionary",
            ),
            (
                "DeeplTranslate",
                {
                    "details": {
                        "name": "DeepL Translate",
                        "status": "business",
                        "url": "https://www.deepl.com",
                    },
                    "pricing": {"payment_plan": "Annual"},
                    "technical": {
                        "api": {
                            "key": "your_api_key",
                            "key_expiration": "2025-12-31",
                            "request_limit": 10000,
                        },
                        "performance": {
                            "max_text_size": 5000,
                            "priority": 1,
                            "success_rate": 99.5,
                        },
                    },
                },
                KeyError,
                "Translator['pricing'] is missing required keys: ['cost_per_translation']",
            ),
            (
                "DeeplTranslate",
                {
                    "details": {
                        "name": "DeepL Translate",
                        "status": "business",
                        "url": "https://www.deepl.com",
                    },
                    "pricing": {
                        "cost_per_translation": "1000",
                        "payment_plan": "Annual",
                    },
                    "technical": {
                        "api": {
                            "key": "your_api_key",
                            "key_expiration": "2025-12-31",
                            "request_limit": 10000,
                        },
                        "performance": {
                            "max_text_size": 5000,
                            "priority": 1,
                            "success_rate": 99.5,
                        },
                    },
                },
                TypeError,
                "Translator[['pricing', 'cost_per_translation']] must be a number or None",
            ),
            (
                "DeeplTranslate",
                {
                    "details": {
                        "name": "DeepL Translate",
                        "status": "business",
                        "url": "https://www.deepl.com",
                    },
                    "pricing": {
                        "cost_per_translation": None,
                        "payment_plan": ["Monthly", "Annual"],
                    },
                    "technical": {
                        "api": {
                            "key": "your_api_key",
                            "key_expiration": "2025-12-31",
                            "request_limit": 10000,
                        },
                        "performance": {
                            "max_text_size": 5000,
                            "priority": 1,
                            "success_rate": 99.5,
                        },
                    },
                },
                TypeError,
                "Translator[['pricing', 'payment_plan']] must be a string or None",
            ),
            (
                "DeeplTranslate",
                {
                    "details": {
                        "name": "DeepL Translate",
                        "status": "business",
                        "url": "https://www.deepl.com",
                    },
                    "pricing": {"cost_per_translation": None, "payment_plan": "Annual"},
                    "technical": [
                        "api",
                        {
                            "key": "your_api_key",
                            "key_expiration": "2025-12-31",
                            "request_limit": 10000,
                        },
                        "performance",
                        {"max_text_size": 5000, "priority": 1, "success_rate": 99.5},
                    ],
                },
                TypeError,
                "Translator['technical'] must be a dictionary",
            ),
            (
                "DeeplTranslate",
                {
                    "details": {
                        "name": "DeepL Translate",
                        "status": "business",
                        "url": "https://www.deepl.com",
                    },
                    "pricing": {"cost_per_translation": None, "payment_plan": "Annual"},
                    "technical": {},
                },
                KeyError,
                "Translator['technical'] is missing required keys: ['api', 'performance']",
            ),
            (
                "DeeplTranslate",
                {
                    "details": {
                        "name": "DeepL Translate",
                        "status": "business",
                        "url": "https://www.deepl.com",
                    },
                    "pricing": {"cost_per_translation": None, "payment_plan": "Annual"},
                    "technical": {
                        "api": [
                            "key",
                            "your_api_key",
                            "key_expiration",
                            "2025-12-31",
                            "request_limit",
                            10000,
                        ],
                        "performance": {
                            "max_text_size": 5000,
                            "priority": 1,
                            "success_rate": 99.5,
                        },
                    },
                },
                TypeError,
                "Translator[['technical', 'api']] must be a dictionary",
            ),
            (
                "DeeplTranslate",
                {
                    "details": {
                        "name": "DeepL Translate",
                        "status": "business",
                        "url": "https://www.deepl.com",
                    },
                    "pricing": {"cost_per_translation": None, "payment_plan": "Annual"},
                    "technical": {
                        "api": {"request_limit": 10000},
                        "performance": {
                            "max_text_size": 5000,
                            "priority": 1,
                            "success_rate": 99.5,
                        },
                    },
                },
                KeyError,
                "Translator[['technical', 'api']] is missing required keys: ['key', 'key_expiration']",
            ),
            (
                "DeeplTranslate",
                {
                    "details": {
                        "name": "DeepL Translate",
                        "status": "business",
                        "url": "https://www.deepl.com",
                    },
                    "pricing": {"cost_per_translation": None, "payment_plan": "Annual"},
                    "technical": {
                        "api": {
                            "key": ["your_api_key"],
                            "key_expiration": "2025-12-31",
                            "request_limit": 10000,
                        },
                        "performance": {
                            "max_text_size": 5000,
                            "priority": 1,
                            "success_rate": 99.5,
                        },
                    },
                },
                TypeError,
                "Translator[['technical', 'api', 'key']] must be a string",
            ),
            (
                "DeeplTranslate",
                {
                    "details": {
                        "name": "DeepL Translate",
                        "status": "business",
                        "url": "https://www.deepl.com",
                    },
                    "pricing": {"cost_per_translation": None, "payment_plan": "Annual"},
                    "technical": {
                        "api": {
                            "key": "your_api_key",
                            "key_expiration": ["2025-12-31"],
                            "request_limit": 10000,
                        },
                        "performance": {
                            "max_text_size": 5000,
                            "priority": 1,
                            "success_rate": 99.5,
                        },
                    },
                },
                TypeError,
                "Translator[['technical', 'api', 'key_expiration']] must be a string or None",
            ),
            (
                "DeeplTranslate",
                {
                    "details": {
                        "name": "DeepL Translate",
                        "status": "business",
                        "url": "https://www.deepl.com",
                    },
                    "pricing": {"cost_per_translation": None, "payment_plan": "Annual"},
                    "technical": {
                        "api": {
                            "key": "your_api_key",
                            "key_expiration": "12-31-2025",
                            "request_limit": 10000,
                        },
                        "performance": {
                            "max_text_size": 5000,
                            "priority": 1,
                            "success_rate": 99.5,
                        },
                    },
                },
                ValueError,
                "Translator[['technical', 'api', 'key_expiration']] must be in 'YYYY-MM-DD' format",
            ),
            (
                "DeeplTranslate",
                {
                    "details": {
                        "name": "DeepL Translate",
                        "status": "business",
                        "url": "https://www.deepl.com",
                    },
                    "pricing": {"cost_per_translation": None, "payment_plan": "Annual"},
                    "technical": {
                        "api": {
                            "key": "your_api_key",
                            "key_expiration": "2025-12-31",
                            "request_limit": [10000],
                        },
                        "performance": {
                            "max_text_size": 5000,
                            "priority": 1,
                            "success_rate": 99.5,
                        },
                    },
                },
                TypeError,
                "Translator[['technical', 'api', 'request_limit']] must be an integer",
            ),
            (
                "DeeplTranslate",
                {
                    "details": {
                        "name": "DeepL Translate",
                        "status": "business",
                        "url": "https://www.deepl.com",
                    },
                    "pricing": {"cost_per_translation": None, "payment_plan": "Annual"},
                    "technical": {
                        "api": {
                            "key": "your_api_key",
                            "key_expiration": "2025-12-31",
                            "request_limit": 10000,
                        },
                        "performance": [
                            "max_text_size",
                            5000,
                            "priority",
                            1,
                            "success_rate",
                            99.5,
                        ],
                    },
                },
                TypeError,
                "Translator[['technical', 'performance']] must be a dictionary",
            ),
            (
                "DeeplTranslate",
                {
                    "details": {
                        "name": "DeepL Translate",
                        "status": "business",
                        "url": "https://www.deepl.com",
                    },
                    "pricing": {"cost_per_translation": None, "payment_plan": "Annual"},
                    "technical": {
                        "api": {
                            "key": "your_api_key",
                            "key_expiration": "2025-12-31",
                            "request_limit": 10000,
                        },
                        "performance": {
                            "max_text_size": 5000,
                        },
                    },
                },
                KeyError,
                "Translator[['technical', 'performance']] is missing required keys: ['priority', 'success_rate']",
            ),
            (
                "DeeplTranslate",
                {
                    "details": {
                        "name": "DeepL Translate",
                        "status": "business",
                        "url": "https://www.deepl.com",
                    },
                    "pricing": {"cost_per_translation": None, "payment_plan": "Annual"},
                    "technical": {
                        "api": {
                            "key": "your_api_key",
                            "key_expiration": "2025-12-31",
                            "request_limit": 10000,
                        },
                        "performance": {
                            "max_text_size": "5000",
                            "priority": 1,
                            "success_rate": 99.5,
                        },
                    },
                },
                TypeError,
                "Translator[['technical', 'performance', 'max_text_size']] must be an integer",
            ),
            (
                "DeeplTranslate",
                {
                    "details": {
                        "name": "DeepL Translate",
                        "status": "business",
                        "url": "https://www.deepl.com",
                    },
                    "pricing": {"cost_per_translation": None, "payment_plan": "Annual"},
                    "technical": {
                        "api": {
                            "key": "your_api_key",
                            "key_expiration": "2025-12-31",
                            "request_limit": 10000,
                        },
                        "performance": {
                            "max_text_size": 5000,
                            "priority": "1",
                            "success_rate": 99.5,
                        },
                    },
                },
                TypeError,
                "Translator[['technical', 'performance', 'priority']] must be an integer",
            ),
            (
                "DeeplTranslate",
                {
                    "details": {
                        "name": "DeepL Translate",
                        "status": "business",
                        "url": "https://www.deepl.com",
                    },
                    "pricing": {"cost_per_translation": None, "payment_plan": "Annual"},
                    "technical": {
                        "api": {
                            "key": "your_api_key",
                            "key_expiration": "2025-12-31",
                            "request_limit": 10000,
                        },
                        "performance": {
                            "max_text_size": 5000,
                            "priority": 1,
                            "success_rate": "99.5",
                        },
                    },
                },
                TypeError,
                "Translator[['technical', 'performance', 'success_rate']] must be a number",
            ),
            (
                "DeeplTranslate",
                {
                    "details": {
                        "name": "DeepL Translate",
                        "status": "business",
                        "url": "https://www.deepl.com",
                    },
                    "pricing": {"cost_per_translation": None, "payment_plan": "Annual"},
                    "technical": {
                        "api": {
                            "key": "your_api_key",
                            "key_expiration": "2025-12-31",
                            "request_limit": 10000,
                        },
                        "performance": {
                            "max_text_size": 5000,
                            "priority": 1,
                            "success_rate": 99.5,
                        },
                    },
                },
                ValueError,
                "Translator 'DeeplTranslate' already exists",
            ),
        ],
    )
    def test_add_translator_failed(
        self, repository_fixture, translator_name, content, error, error_msg
    ):
        with pytest.raises(error, match=re.escape(error_msg)):
            repository_fixture.add_translator(translator_name, content)


class TestRepositoryCleanModules:

    def test_clean_modules_control(self, repository_fixture):
        assert len(repository_fixture.modules) != 0
        assert len(repository_fixture.domains) != 0

    def test_clean_modules(self, repository_fixture):
        repository_fixture.clean_modules()
        assert len(repository_fixture[["paths", "modules"]]) == 0
        assert len(repository_fixture["domains"]) == 0


class TestRepositoryCleanDomains:

    def test_clean_domains_control(self, repository_fixture):
        assert len(repository_fixture.domains) != 0
        assert len(repository_fixture.modules) != 0

    def test_clean_domains(self, repository_fixture):
        repository_fixture.clean_domains()
        assert len(repository_fixture["domains"]) == 0
        assert len(repository_fixture[["paths", "modules"]]) != 0


class TestRepositoryCleanHierarchy:

    def test_clean_hierarchy_control(self, repository_fixture):
        assert repository_fixture[["languages", "hierarchy", "fr"]] == ["fr-FR"]
        assert repository_fixture[["languages", "hierarchy", "en"]] == [
            "en-US",
            "en-GB",
        ]
        assert len(repository_fixture[["languages", "hierarchy"]]) == 2

    def test_clean_hierarchy(self, repository_fixture):
        repository_fixture.clean_hierarchy()
        assert len(repository_fixture[["languages", "hierarchy"]]) == 0


class TestRepositoryCleanAuthors:

    @pytest.mark.parametrize(
        "author_id, expected",
        [
            (
                "baf52b25-d1ed-4651-a3e6-273850901cf0",
                [
                    ("email", "jeanne@doe.com"),
                    ("first_name", "Jeanne"),
                    ("languages", ["fr", "en"]),
                    ("last_name", "Doe"),
                ],
            ),
            (
                "7d097ac4-ba77-4333-a63f-76d48a75b38c",
                [
                    ("email", "john@doe.com"),
                    ("first_name", "John"),
                    ("languages", ["fr", "en"]),
                    ("last_name", "Doe"),
                ],
            ),
        ],
    )
    def test_clean_authors_control(self, repository_fixture, author_id, expected):
        assert len(repository_fixture["authors"]) == 2
        for key, value in expected:
            assert repository_fixture[["authors", author_id, key]] == value

    def test_clean_authors(self, repository_fixture):
        repository_fixture.clean_authors()
        assert len(repository_fixture["authors"]) == 0


class TestRepositoryCleanRepository:
    def test_clean_repository_control(self, repository_fixture, tmp_class_repository):
        assert len(repository_fixture.repository) != 0
        assert tmp_class_repository[2][0] in repository_fixture.leaves()

    def test_clean_repository(self, repository_fixture):
        repository_fixture.clean_repository()
        assert len(repository_fixture.repository) == 0


class TestRepositoryCleanTranslator:
    def test_clean_translator_control(self, repository_fixture):
        assert len(repository_fixture.translators) != 0
        assert repository_fixture.is_key("GoogleTranslate")

    def test_clean_translator(self, repository_fixture):
        repository_fixture.clean_translators()
        assert len(repository_fixture.translators) == 0
