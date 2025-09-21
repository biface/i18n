"""
Test module for Repository class in module i18n-tools/models
"""

import re

import pytest
from ndict_tools import StrictNestedDictionary

from i18n_tools.models.repository import Repository


@pytest.fixture(scope="class")
def test_repository(tmp_class_repository):
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

    def test_get_name(self, test_repository):
        assert test_repository.name == "fsm-tools"

    def test_set_name(self, test_repository):
        test_repository.name = "automata-tools"
        assert test_repository.name == "automata-tools"

    def test_get_config(self, tmp_class_repository, test_repository):
        assert (
            test_repository.config
            == tmp_class_repository[0][0]
            + "/repository-test/fsm_tools/locales/_i18n_tools/i18n-tools.yaml"
        )

    def test_set_config(self, tmp_class_repository, test_repository):
        old_config = test_repository.config
        old_config_path = test_repository[["paths", "config"]]
        new_config = (
            tmp_class_repository[0][0]
            + "/repository-test/fsm_tools/locales/_i18n_tools/i18n-tools.toml"
        )
        test_repository.config = new_config
        assert test_repository[["paths", "config"]] == old_config_path
        assert test_repository[["paths", "settings"]] == "i18n-tools.toml"
        test_repository.config = old_config
        assert test_repository[["paths", "settings"]] == "i18n-tools.yaml"

    def test_get_repository(self, tmp_class_repository, test_repository):
        print(test_repository)
        assert (
            test_repository.repository
            == tmp_class_repository[0][0] + "/repository-test"
        )

    def test_set_repository(self, tmp_module_repository, test_repository):
        test_repository.repository = tmp_module_repository[0][0] + "/test-function"
        assert (
            test_repository[["paths", "repository"]]
            == tmp_module_repository[0][0] + "/test-function"
        )
        test_repository[["paths", "repository"]] = (
            tmp_module_repository[0][0] + "/repository-test"
        )
        assert (
            test_repository[["paths", "repository"]]
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
    def test_set_repository_failed(self, test_repository, path, error, error_msg):
        with pytest.raises(error, match=re.escape(error_msg)):
            test_repository.repository = path

    def test_get_creation_date(self, test_repository):
        assert test_repository.creation_date == "2024-08-16 14:00"

    def test_get_updated_date(self, test_repository):
        assert test_repository.updated_date == "2025-09-14 14:54"

    def test_set_updated_date(self, test_repository):
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
    def test_get_modules(self, test_repository, module):
        assert module in test_repository.modules

    def test_set_modules(self, test_repository):
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
    def test_get_domains(self, test_repository, module, domains):
        assert test_repository.domains[module] == domains

    def test_set_domains(self, test_repository):
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
    def test_set_domains_failed(self, test_repository, module, domain, error_msg):
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
    def test_control_domain(self, test_repository, module, domains):
        assert test_repository.domains[module] == domains

    @pytest.mark.parametrize(
        "fallback, languages", [("fr", ["fr-FR"]), ("en", ["en-US", "en-GB"])]
    )
    def test_get_hierarchy(self, test_repository, fallback, languages):
        for lang in languages:
            assert lang in test_repository.hierarchy[fallback]

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
    def test_set_hierarchy(self, test_repository, hierarchy, expected):
        test_repository.hierarchy = hierarchy
        for fallback, l_lang in expected:
            for lang in l_lang:
                assert lang in test_repository.hierarchy[fallback]

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
    def test_set_hierarchy_failed(self, test_repository, hierarchy, error_msg):
        with pytest.raises((TypeError, ValueError), match=re.escape(error_msg)):
            test_repository.hierarchy = hierarchy

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
    def test_get_authors(self, test_repository, key, values):
        print(test_repository["paths"])
        for index, value in values:
            assert test_repository.authors[key][index] == value

    def test_set_authors(self, test_repository):
        uuid_1 = "c64673e4-5d7d-4798-a22f-d1ea7cc807c1"
        uuid_2 = "00b482a7-9ace-489c-8c48-6a8ec48d6876"
        test_repository.authors = {
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
        assert test_repository[["authors", uuid_1, "email"]] == "jean@dupond.com"
        assert test_repository[["authors", uuid_2, "languages"]] == ["en"]

    def test_set_authors_failed(self, test_repository):
        uuid_1 = "c64673e4-5d7d-4798-a22f-d1ea7cc807c1"
        uuid_2 = "00b482a7-9ace-489c-8c48-6a8ec48d6876"
        with pytest.raises(
            TypeError,
            match=re.escape("authors must be a dictionary, not <class 'list'>"),
        ):
            test_repository.authors = [
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
    def test_get_translators(self, test_repository, path, values):
        d = test_repository.translators["GoogleTranslate"]
        assert isinstance(d[path], StrictNestedDictionary)
        for key, value in values:
            assert d[path][key] == value

    def test_set_translators(self, test_repository):
        test_repository.translators = {
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
        assert len(test_repository.translators) == 2

    def test_set_translators_failed(self, test_repository):
        with pytest.raises(
            TypeError,
            match=re.escape("translators must be a dictionary, not <class 'list'>"),
        ):
            test_repository.translators = [
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

    def test_add_module(self, test_repository):
        test_repository.add_module("fsm_tools/pda")
        assert "fsm_tools/pda" in test_repository.modules

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
    def test_add_modules_failed(self, test_repository, module, error, error_msg):
        with pytest.raises(error, match=re.escape(error_msg)):
            test_repository.add_module(module)

    def test_remove_module(self, test_repository):
        test_repository.remove_module("fsm_tools/pda")
        assert "fsm_tools/pda" not in test_repository.modules
        assert "fsm_tools/pda" not in test_repository["domains"].keys()

    def test_remove_modules_failed(self, test_repository):
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
    def test_add_domain(self, test_repository, module, domain, expected):
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
    def test_add_domain_failed(self, test_repository, module, domain, error_msg):
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
    def test_remove_domain(self, test_repository, module, domain, expected):
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
    def test_remove_domain_failed(self, test_repository, module, domain, error_msg):
        with pytest.raises(ValueError, match=re.escape(error_msg)):
            test_repository.remove_domain(module, domain)

    @pytest.mark.parametrize(
        "fallback, languages, expected",
        [
            ("fr", "fr-BE", ["fr-FR", "fr-BE"]),
            ("it", ["it-IT", "it-CH"], ["it-IT", "it-CH"]),
            ("se", ["se-FI", "se-NO"], ["se-FI", "se-NO"]),
            ("se", "se-SE", ["se-FI", "se-NO", "se-SE"]),
        ],
    )
    def test_add_hierarchy(self, test_repository, fallback, languages, expected):
        test_repository.add_hierarchy(fallback, languages)
        assert test_repository[["languages", "hierarchy", fallback]] == expected

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
        self, test_repository, fallback, languages, error, error_msg
    ):
        with pytest.raises(error, match=re.escape(error_msg)):
            test_repository.add_hierarchy(fallback, languages)

    @pytest.mark.parametrize(
        "fallback, language, expected",
        [
            ("fr", "fr-BE", ["fr-FR"]),
            ("fr", "fr-FR", []),
            ("en", "en-US", ["en-GB"]),
            ("se", "se-SE", ["se-FI", "se-NO"]),
        ],
    )
    def test_remove_hierarchy(self, test_repository, fallback, language, expected):
        test_repository.remove_hierarchy(fallback, language)
        assert test_repository[["languages", "hierarchy", fallback]] == expected

    def test_remove_empty_fr(self, test_repository):
        assert test_repository[["languages", "hierarchy", "fr"]] == []
        test_repository.remove_hierarchy("fr", None)
        assert "fr" not in test_repository[["languages", "hierarchy"]].keys()

    @pytest.mark.parametrize(
        "fallback, language, error_msg",
        [
            ("sv", "sv-SE", "Base language sv does not exist in hierarchy"),
            ("en", "en-JM", "Language en-JM does not exist for base language en"),
            ("se", "se-SE", "Language se-SE does not exist for base language se"),
        ],
    )
    def test_remove_hierarchy_failed(
        self, test_repository, fallback, language, error_msg
    ):
        with pytest.raises(ValueError, match=re.escape(error_msg)):
            test_repository.remove_hierarchy(fallback, language)

    @pytest.mark.parametrize(
        "fallback, languages, expected",
        [
            ("fr", "fr-FR", ["fr-FR"]),
            ("it", ["it-IT", "it-CH"], ["it-IT", "it-CH"]),
            ("se", ["se-FI", "se-NO"], ["se-FI", "se-NO"]),
        ],
    )
    def test_update_hierarchy(self, test_repository, fallback, languages, expected):
        test_repository.update_hierarchy(fallback, languages)
        assert test_repository[["languages", "hierarchy", fallback]] == expected

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
        self, test_repository, fallback, languages, error, error_msg
    ):
        with pytest.raises(error, match=re.escape(error_msg)):
            test_repository.update_hierarchy(fallback, languages)

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
    def test_add_author(self, test_repository, author_id, auther_desc, expected):
        test_repository.add_author(author_id, auther_desc)
        for key, value in expected:
            assert test_repository[["authors", author_id, key]] == value

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
        self, test_repository, author_id, auther_desc, error, error_msg
    ):
        with pytest.raises(error, match=re.escape(error_msg)):
            test_repository.add_author(author_id, auther_desc)

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
        self, test_repository, author_id, auther_desc, error, error_msg
    ):
        with pytest.raises(error, match=re.escape(error_msg)):
            test_repository.add_author(author_id, auther_desc)

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
        self, test_repository, author_id, auther_desc, error, error_msg
    ):
        with pytest.raises(error, match=re.escape(error_msg)):
            test_repository.add_author(author_id, auther_desc)

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
    def test_update_author(self, test_repository, author_id, auther_desc, expected):
        test_repository.update_author(author_id, auther_desc)
        for key, value in expected:
            assert test_repository[["authors", author_id, key]] == value

    def test_update_author_existant_failed(self, test_repository):
        with pytest.raises(
            ValueError,
            match=re.escape(
                "Author '4b4bbb92-5fa4-4aa4-8c14-84409357bce7' does not exist"
            ),
        ):
            test_repository.update_author(
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
        self, test_repository, author_id, author_desc, error, error_msg
    ):
        with pytest.raises(error, match=re.escape(error_msg)):
            test_repository.update_author(author_id, author_desc)

    def test_remove_author(self, test_repository):
        assert len(test_repository.authors) == 4
        test_repository.remove_author("54d961ad-59dd-41d0-899a-d7ea58170547")
        assert len(test_repository.authors) == 3

    def test_remove_repository(self, test_repository):
        print(repr(test_repository.repository))
        assert len(test_repository.repository) != 0
        test_repository.remove_repository()
        assert len(test_repository.repository) == 0

    def test_remove_repository_failed(self, test_repository):
        with pytest.raises(
            ValueError, match=re.escape("Repository path is already empty")
        ):
            test_repository.remove_repository()

    def test_add_repository(self, tmp_class_repository, test_repository):
        test_repository.add_repository(tmp_class_repository[1][0])
        assert test_repository.repository is not None

    def test_add_repository_failed(self, tmp_class_repository, test_repository):
        with pytest.raises(ValueError, match=re.escape("Repository path already set")):
            test_repository.add_repository(tmp_class_repository[1][0])

    def test_update_repository(self, tmp_class_repository, test_repository):
        test_repository.update_repository(tmp_class_repository[2][0])
        print(test_repository.repository)
        assert test_repository.repository is not None

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
    def test_update_repository_failed(self, test_repository, false_path, error_msg):
        with pytest.raises(FileNotFoundError, match=re.escape(error_msg)):
            test_repository.update_repository(false_path)

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
    def test_add_translator(self, test_repository, translator_name, content, expected):
        test_repository.add_translator(translator_name, content)
        for path, values in expected:
            for key, value in values:
                assert test_repository.translators[path][key] == value

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
        self, test_repository, translator_name, content, error, error_msg
    ):
        with pytest.raises(error, match=re.escape(error_msg)):
            test_repository.add_translator(translator_name, content)


class TestRepositoryCleanModules:

    def test_clean_modules_control(self, test_repository):
        assert len(test_repository.modules) != 0
        assert len(test_repository.domains) != 0

    def test_clean_modules(self, test_repository):
        test_repository.clean_modules()
        assert len(test_repository[["paths", "modules"]]) == 0
        assert len(test_repository["domains"]) == 0


class TestRepositoryCleanDomains:

    def test_clean_domains_control(self, test_repository):
        assert len(test_repository.domains) != 0
        assert len(test_repository.modules) != 0

    def test_clean_domains(self, test_repository):
        test_repository.clean_domains()
        assert len(test_repository["domains"]) == 0
        assert len(test_repository[["paths", "modules"]]) != 0


class TestRepositoryCleanHierarchy:

    def test_clean_hierarchy_control(self, test_repository):
        assert test_repository[["languages", "hierarchy", "fr"]] == ["fr-FR"]
        assert test_repository[["languages", "hierarchy", "en"]] == ["en-US", "en-GB"]
        assert len(test_repository[["languages", "hierarchy"]]) == 2

    def test_clean_hierarchy(self, test_repository):
        test_repository.clean_hierarchy()
        assert len(test_repository[["languages", "hierarchy"]]) == 0


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
    def test_clean_authors_control(self, test_repository, author_id, expected):
        assert len(test_repository["authors"]) == 2
        for key, value in expected:
            assert test_repository[["authors", author_id, key]] == value

    def test_clean_authors(self, test_repository):
        test_repository.clean_authors()
        assert len(test_repository["authors"]) == 0


class TestRepositoryCleanRepository:
    def test_clean_repository_control(self, test_repository, tmp_class_repository):
        assert len(test_repository.repository) != 0
        assert tmp_class_repository[2][0] in test_repository.leaves()

    def test_clean_repository(self, test_repository):
        test_repository.clean_repository()
        assert len(test_repository.repository) == 0


class TestRepositoryCleanTranslator:
    def test_clean_translator_control(self, test_repository):
        assert len(test_repository.translators) != 0
        assert test_repository.is_key("GoogleTranslate")

    def test_clean_translator(self, test_repository):
        test_repository.clean_translators()
        assert len(test_repository.translators) == 0
