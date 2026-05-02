import os
from datetime import datetime, timedelta

import pytest

# from conftest import conf_tests, tmp_module_repository
from email_validator import EmailNotValidError

from i18n_tools.config import Config
from i18n_tools.patterns import Singleton


class TestConfigInit:
    def test_config_failed_path(self, tmp_module_repository):
        true_singleton = Singleton._instances
        Singleton._instances = {}
        with pytest.raises(FileNotFoundError):
            Config(tmp_module_repository[3][0] + "/" + "config.toml")
        Singleton._instances = true_singleton

    def test_config_init(self, tmp_module_repository):
        true_singleton = Singleton._instances
        Singleton._instances = {}
        config = Config(
            tmp_module_repository[4].get_repository()[["paths", "config"]]
            + "/"
            + tmp_module_repository[4].get_repository()[["paths", "settings"]]
        )
        assert (
            config.application[["paths", "config"]]
            == tmp_module_repository[4].get_repository()[["paths", "config"]]
        )
        assert (
            config.application[["paths", "settings"]]
            == tmp_module_repository[4].get_repository()[["paths", "settings"]]
        )
        Singleton._instances = true_singleton

    def test_config_singleton(self, tmp_module_repository):
        config_2 = Config()
        assert config_2 == tmp_module_repository[4]


class TestConfigLoadSave:
    @pytest.mark.parametrize(
        "source, destination, valid",
        [
            ("i18n-tools.yaml", "config.toml", True),
            ("config.toml", "i18n-settings.json", True),
            ("i18n-settings.json", "config.text", False),
            ("i18n-settings.json", "i18n-tools.toml", True),
            ("config.toml", "i18n-tools.csv", False),
            ("config.toml", "config.yaml", True),
        ],
    )
    def test_load_and_save_config_file(
        self, tmp_module_repository, source, destination, valid
    ):
        """Test loading configuration files in different formats."""
        tmp_module_repository[4].get_repository()[["paths", "settings"]] = source
        tmp_module_repository[4].load()
        destination_file = (
            tmp_module_repository[4].get_repository()[["paths", "config"]]
            + "/"
            + destination
        )
        tmp_module_repository[4].get_repository()[["paths", "settings"]] = destination
        assert not os.path.exists(destination_file)
        if valid:
            tmp_module_repository[4].save()
            assert os.path.exists(destination_file)
        else:
            with pytest.raises(Exception):
                tmp_module_repository[4].save()
        tmp_module_repository[4].get_repository()[
            ["paths", "settings"]
        ] = "i18n-tools.yaml"

    def test_load_config_file_not_found(self, conf_tests, tmp_module_repository):
        """Test loading a configuration file that does not exist."""
        tmp_module_repository[4].get_repository()[["paths", "config"]] = conf_tests[
            "repository"
        ]["other"]

        with pytest.raises(
            FileNotFoundError,
            match="Configuration file not found: test-function/i18n-tools.yaml",
        ):
            tmp_module_repository[4].load()

        tmp_module_repository[4].get_repository()[
            ["paths", "settings"]
        ] = "non-existent.csv"

    def test_save_config_unknown_directory(self, conf_tests, tmp_module_repository):
        """Test loading a configuration file that does not exist."""
        tmp_module_repository[4].get_repository()[["paths", "config"]] = conf_tests[
            "repository"
        ]["other"]
        with pytest.raises(Exception):
            tmp_module_repository[4].save()
        tmp_module_repository[4].get_repository()[["paths", "settings"]] = ""
        with pytest.raises(ValueError):
            tmp_module_repository[4].save()
        tmp_module_repository[4].get_repository()[["paths", "config"]] = conf_tests[
            "repository"
        ]["application"]["config"]
        tmp_module_repository[4].get_repository()[["paths", "settings"]] = conf_tests[
            "repository"
        ]["application"]["settings"]


class TestConfigSetGet:
    @pytest.mark.parametrize(
        "path, value, exp_value, valid, exp_except",
        [
            (["application", "details", "name"], "another", "another", True, None),
            (["applications", "details", "name"], "another", "", False, KeyError),
            (["application", "detail", "name"], "another", "", False, KeyError),
            ("", "unexpected empty string", "", False, ValueError),
            ([], "unexpected empty list", "", False, ValueError),
            ("non-existent-attribute", "unexpected attribute", "", False, KeyError),
            (["non-existent-attribute"], "unexpected attribute", "", False, KeyError),
            (["package", "details", "name"], "another", "another", True, None),
            (["package"], ["non expected data format"], "", False, TypeError),
        ],
    )
    def test_set_config(
        self,
        conf_tests,
        tmp_function_repository,
        path,
        value,
        exp_value,
        valid,
        exp_except,
    ):
        config = tmp_function_repository[4]
        if valid:
            config.set(path, value)
            assert config.get(path) == exp_value
        else:
            with pytest.raises(exp_except):
                config.set(path, value)

    @pytest.mark.parametrize(
        "path, expected_value, valid, exp_except",
        [
            (["application", "details", "name"], "fsm-tools", True, None),
            (["package", "details", "name"], "another", True, None),
            (["application", "details", "version"], "0.0.1", True, None),
            (["applications", "details", "name"], None, False, KeyError),
            (["application", "detail", "name"], None, False, KeyError),
            (["non-existent-attribute"], None, False, KeyError),
        ],
    )
    def test_get_config(
        self,
        conf_tests,
        tmp_function_repository,
        path,
        expected_value,
        valid,
        exp_except,
    ):
        config = tmp_function_repository[4]
        if valid:
            assert config.get(path) == expected_value
        else:
            with pytest.raises(exp_except):
                config.get(path)


class TestConfigRepository:
    @pytest.mark.parametrize(
        "switch, valid, module, extension, expected_name, exception",
        [
            ("application", True, "discotheque", "json", "discotheque", None),
            ("package", True, "i18n_tools", "yaml", "fsm-tools", None),
            ("application", False, "discotheque", "csv", "discotheque", ValueError),
            (
                "application",
                False,
                "discotheque",
                "yaml",
                "discotheque",
                FileNotFoundError,
            ),
            ("package", False, "i18n-tools", "json", "", IOError),
        ],
    )
    def test_set_config_repository(
        self,
        conf_tests,
        tmp_function_repository,
        switch,
        valid,
        module,
        extension,
        expected_name,
        exception,
    ):
        config = Config()
        if valid:
            if switch == "application":
                config.switch_to_application_config()
                config.set_repository(
                    tmp_function_repository[2][0],
                    extension,
                    module,
                )
            else:
                config.switch_to_package_config()
                config.set_repository(
                    tmp_function_repository[1][0],
                    extension,
                    module,
                )
            config.load()
            assert config.get(["application", "details", "name"]) == expected_name
        else:
            with pytest.raises(exception):
                if switch == "application":
                    config.switch_to_application_config()
                    config.set_repository(
                        tmp_function_repository[2][0],
                        extension,
                        module,
                    )
                else:
                    config.switch_to_package_config()
                    config.set_repository(
                        tmp_function_repository[1][0],
                        extension,
                        module,
                    )
                config.load()

    @pytest.mark.parametrize(
        "switch, valid, module, extension, modules, expected_name, exception",
        [
            (
                "application",
                True,
                "discotheque",
                "json",
                ["disco" "disco/author"],
                "discotheque",
                None,
            ),
            (
                "application",
                True,
                None,
                "yaml",
                ["disco" "disco/author"],
                "fsm-tools",
                None,
            ),
            ("application", True, None, "yaml", None, "fsm-tools", None),
            ("package", True, "i18n_tools", "yaml", None, "fsm-tools", None),
            ("application", False, "discotheque", "csv", None, "", ValueError),
            ("application", False, "discotheque", "yaml", None, "", FileNotFoundError),
            ("package", False, "i18n-tools", "json", None, "", IOError),
        ],
    )
    def test_update_config_repository(
        self,
        conf_tests,
        tmp_function_repository,
        switch,
        valid,
        module,
        extension,
        modules,
        expected_name,
        exception,
    ):
        config = Config()
        if valid:
            if switch == "application":
                config.switch_to_application_config()
                config.update_repository(
                    tmp_function_repository[2][0], extension, module, modules
                )
            else:
                config.switch_to_package_config()
                config.update_repository(
                    tmp_function_repository[1][0], extension, module, modules
                )
            config.load()
            assert config.get(["application", "details", "name"]) == expected_name
        else:
            with pytest.raises(exception):
                if switch == "application":
                    print("application")
                    config.switch_to_application_config()
                    config.update_repository(
                        tmp_function_repository[2][0], extension, module, modules
                    )
                else:
                    config.switch_to_package_config()
                    config.update_repository(
                        tmp_function_repository[1][0], extension, module, modules
                    )
                config.load()

    def test_update_repository_nothing(self, tmp_function_repository):
        tmp_function_repository[4].switch_to_application_config()
        tmp_function_repository[4].update_repository()
        assert (
            tmp_function_repository[4].get_repository()["details"]["name"]
            == "fsm-tools"
        )

    def test_set_config_repository_failed_directory(
        self, conf_tests, tmp_function_repository
    ):
        config = Config()
        with pytest.raises(FileNotFoundError):
            config.switch_to_application_config()
            config.set_repository(
                tmp_function_repository[2][0]
                + "/discotheque/locales/_i18n_tools/i18n-tools.json",
                "json",
                "discotheque",
            )

    def test_update_config_repository_failed_file(
        self, conf_tests, tmp_function_repository
    ):
        config = Config()
        with pytest.raises(FileNotFoundError):
            config.switch_to_application_config()
            config.update_repository(
                tmp_function_repository[2][0]
                + "/discotheque/locales/_i18n_tools/i18n-tools.json",
                "json",
                "discotheque",
            )


class TestConfigAuthors:
    @pytest.mark.parametrize(
        "repository, first_name, last_name, email, url, languages, valid, exception",
        [
            (
                "application",
                "Albert",
                "Dupont",
                "albert@dupont.org",
                "",
                ["en", "fr"],
                True,
                None,
            ),
            (
                "application",
                "Albert",
                "Dupont",
                "albert@dupont",
                "",
                ["en", "fr"],
                False,
                EmailNotValidError,
            ),
            (
                "application",
                "Albert",
                "Dupont",
                "albert@dupont.org",
                "",
                ["scot", "fr"],
                False,
                ValueError,
            ),
            (
                "package",
                "Albert",
                "Dupont",
                "albert@dupont.org",
                "",
                ["en", "fr"],
                True,
                None,
            ),
            (
                "package",
                "Jeanine",
                "Durand",
                "jeanine.durand@dupont.org",
                "",
                ["en", "fr"],
                True,
                None,
            ),
            (
                "application",
                "Albert",
                "Dupont",
                "albert@dupont.org",
                "",
                ["en", "fr"],
                False,
                KeyError,
            ),
            ("package", "John", "Doe", "john@doe.com", "", ["en", "fr"], True, None),
            (
                "application",
                "Jeanine",
                "Durand",
                "jeanine.durand@dupont.org",
                "https://dupont.org/",
                ["en", "fr"],
                True,
                None,
            ),
        ],
    )
    def test_add_author(
        self,
        conf_tests,
        tmp_module_repository,
        repository,
        first_name,
        last_name,
        email,
        url,
        languages,
        valid,
        exception,
    ):
        config = tmp_module_repository[4]

        if repository == "application":
            config.switch_to_application_config()
            config.set(
                ["application", "paths", "config"],
                tmp_module_repository[2][0] + "/fsm_tools/locales/_i18n_tools",
            )
            config.set(["application", "paths", "settings"], "i18n-tools.yaml")
        elif repository == "package":
            config.switch_to_package_config()
            config.set(
                ["package", "paths", "config"],
                tmp_module_repository[1][0] + "/i18n_tools/locales/_i18n_tools",
            )
            config.set(["package", "paths", "settings"], "i18n-tools.yaml")
        else:
            config.switch_to_application_config()

        config.load()

        if valid:
            config.add_author(first_name, last_name, email, url, languages)
            assert config.get_author(email)["email"] == email
        else:
            with pytest.raises(exception):
                config.add_author(first_name, last_name, email, url, languages)

        config.save()

    @pytest.mark.parametrize(
        "repository, index, valid, first_name, last_name, email, languages, exception",
        [
            (
                "application",
                "7d097ac4-ba77-4333-a63f-76d48a75b38c",
                True,
                "John",
                "Doe",
                "john@doe.com",
                ["en", "fr"],
                None,
            ),
            (
                "application",
                "john@doe.com",
                True,
                "John",
                "Doe",
                "john@doe.com",
                ["en", "fr"],
                None,
            ),
            (
                "application",
                "baf52b25-d1ed-4651-a3e6-273850901cf0",
                True,
                "Jeanne",
                "Doe",
                "jeanne@doe.com",
                ["en, fr"],
                None,
            ),
            (
                "package",
                "baf52b25-d1ed-4651-a3e6-273850901cf0",
                False,
                "",
                "",
                "",
                [],
                KeyError,
            ),
            ("package", "jeanne@doe", False, "", "", "", [], ValueError),
            (
                "application",
                "7d097ac4-ba77-4333-a63f-76d49a75b38c",
                False,
                "",
                "",
                "",
                [],
                KeyError,
            ),
            (
                "application",
                "albert@dupont.org",
                True,
                "Albert",
                "Dupont",
                "albert@dupont.org",
                ["en", "fr"],
                None,
            ),
            (
                "package",
                "albert@dupont.org",
                True,
                "Albert",
                "Dupont",
                "albert@dupont.org",
                ["en", "fr"],
                None,
            ),
        ],
    )
    def test_get_author(
        self,
        conf_tests,
        tmp_module_repository,
        repository,
        index,
        valid,
        first_name,
        last_name,
        email,
        languages,
        exception,
    ):
        config = tmp_module_repository[4]
        if repository == "application":
            config.switch_to_application_config()
            config.set(
                ["application", "paths", "config"],
                tmp_module_repository[2][0] + "/fsm_tools/locales/_i18n_tools",
            )
            config.set(["application", "paths", "settings"], "i18n-tools.yaml")
        elif repository == "package":
            config.switch_to_package_config()
            config.set(
                ["package", "paths", "config"],
                tmp_module_repository[1][0] + "/i18n_tools/locales/_i18n_tools",
            )
            config.set(["package", "paths", "settings"], "i18n-tools.yaml")

        config.load()
        if valid:
            author = config.get_author(index)
            assert author["email"] == email
        else:
            with pytest.raises(exception):
                config.get_author(index)

    @pytest.mark.parametrize(
        "repository, index, valid, expected_data, exception",
        [
            (
                "application",
                "51e7a015-d78e-4bdc-abb9-6ce43e8ce2c4",
                True,
                [
                    "mike.l.fakeuphead@gmail.com",
                    4,
                    ["john@doe.com", "John", "Doe", ["fr", "en"]],
                ],
                None,
            ),
            (
                "application",
                "51e7a015-d78e-4bdc-abb9-6ce43e8ce2c4",
                False,
                [
                    "mike.l.fakeuphead@gmail.com",
                    4,
                    ["john@doe.com", "John", "Doe", ["fr", "en"]],
                ],
                None,
            ),
            (
                "application",
                "mike.l.fakeuphead@gmail",
                False,
                [
                    "mike.l.fakeuphead@gmail.com",
                    4,
                    ["john@doe.com", "John", "Doe", ["fr", "en"]],
                ],
                ValueError,
            ),
            (
                "package",
                "albert@dupont.org",
                True,
                ["albert@dupont.org", 3, ["john@doe.com", "John", "Doe", ["fr", "en"]]],
                None,
            ),
            (
                "application",
                "albert@dupont.org",
                True,
                ["albert@dupont.org", 3, ["john@doe.com", "John", "Doe", ["fr", "en"]]],
                None,
            ),
            (
                "application",
                "jeanine.durand@dupont.org",
                True,
                [
                    "jeanine.durand@dupont.org",
                    2,
                    ["john@doe.com", "John", "Doe", ["fr", "en"]],
                ],
                None,
            ),
        ],
    )
    def test_remove_author(
        self, tmp_module_repository, repository, index, valid, expected_data, exception
    ):
        config = tmp_module_repository[4]
        if repository == "application":
            config.switch_to_application_config()
            config.set(
                ["application", "paths", "config"],
                tmp_module_repository[2][0] + "/fsm_tools/locales/_i18n_tools",
            )
            config.set(["application", "paths", "settings"], "i18n-tools.yaml")
        elif repository == "package":
            config.switch_to_package_config()
            config.set(
                ["package", "paths", "config"],
                tmp_module_repository[1][0] + "/i18n_tools/locales/_i18n_tools",
            )
            config.set(["package", "paths", "settings"], "i18n-tools.yaml")

        config.load()

        if valid:
            assert config.get_author(index)["email"] == expected_data[0]
            assert config.remove_author(index)
            assert len(config.get_repository()["authors"]) == expected_data[1]
            verified_author = config.get_author(expected_data[2][0])
            assert verified_author["email"] == expected_data[2][0]
            assert verified_author["first_name"] == expected_data[2][1]
            assert verified_author["last_name"] == expected_data[2][2]
            assert all(
                language in verified_author["languages"]
                for language in expected_data[2][3]
            )
        else:
            if exception is None:
                assert not config.remove_author(index)
            else:
                with pytest.raises(exception):
                    config.remove_author(index)

        config.save()


class TestConfigModulesDomain:
    @pytest.mark.parametrize(
        "repository, module,",
        [
            ("package", "i18n_tools"),
            ("application", "fsm_tools"),
            ("package", "i18n_tools/loaders"),
            ("application", "fsm_tools/turing"),
            ("application", "fsm_tools/lba"),
            ("application", "django-fsm_tools"),
            ("application", "django-fsm_tools/context"),
        ],
    )
    def test_existing_module(self, tmp_module_repository, repository, module):
        config = tmp_module_repository[4]

        if repository == "application":
            config.switch_to_application_config()
        elif repository == "package":
            config.switch_to_package_config()

        assert module in config.get_repository()[["paths", "modules"]]

    @pytest.mark.parametrize(
        "repository, module, expected",
        [
            ("package", "i18n_tools/core/locales", "i18n_tools/core"),
            ("package", "locales/i18n_tools/converter", "i18n_tools/converter"),
            ("application", "locales/fsm_tools/pda/locale", "fsm_tools/pda"),
            ("application", "disco", "disco"),
            ("application", "disco/authors", "disco/authors"),
        ],
    )
    def test_add_module(self, tmp_module_repository, repository, module, expected):
        config = tmp_module_repository[4]

        if repository == "application":
            config.switch_to_application_config()
        elif repository == "package":
            config.switch_to_package_config()

        config.add_module(module)
        assert expected in config.get_repository()[["paths", "modules"]]
        config.save()

    @pytest.mark.parametrize(
        "repository, module, expected",
        [
            ("package", "i18n_tools/core/locales", "i18n_tools/core"),
            ("package", "locales/i18n_tools/converter", "i18n_tools/converter"),
            ("application", "locales/fsm_tools/pda/locale", "fsm_tools/pda"),
        ],
    )
    def test_add_module_failure(
        self, tmp_module_repository, repository, module, expected
    ):
        config = tmp_module_repository[4]

        if repository == "application":
            config.switch_to_application_config()
        elif repository == "package":
            config.switch_to_package_config()

        with pytest.raises(ValueError):
            config.add_module(module)

        assert expected in config.get_repository()[["paths", "modules"]]

    @pytest.mark.parametrize(
        "repository, module, domains",
        [
            ("package", "i18n_tools", ["api", "config", "sync"]),
            ("application", "fsm_tools", ["usage", "model"]),
            (
                "package",
                "i18n_tools/loaders",
                ["utils", "repository", "handler", "config"],
            ),
            ("application", "fsm_tools/turing", ["information", "error"]),
            ("application", "fsm_tools/lba", ["information", "error"]),
            ("application", "django-fsm_tools", ["usage", "information", "error"]),
            ("application", "disco", ["place", "play"]),
            ("application", "disco/authors", ["utils", "usage", "register"]),
        ],
    )
    def test_existing_domains(self, tmp_module_repository, repository, module, domains):
        config = tmp_module_repository[4]

        if repository == "application":
            config.switch_to_application_config()

        elif repository == "package":
            config.switch_to_package_config()

        assert all(
            domain in config.get_repository()[["domains", module]] for domain in domains
        )

    @pytest.mark.parametrize(
        "repository, module, contains, domain, expected",
        [
            (
                "package",
                "i18n_tools",
                True,
                "usage",
                ["api", "config", "sync", "usage"],
            ),
            (
                "package",
                "i18n_tools",
                True,
                "errors",
                ["api", "config", "sync", "usage", "errors"],
            ),
            ("package", "i18n_tools/core", False, "usage", ["usage"]),
            ("application", "disco", True, "concert", ["place", "play", "concert"]),
            ("package", "i18n_tools/core", True, "errors", ["usage", "errors"]),
        ],
    )
    def test_add_domain(
        self, tmp_module_repository, repository, module, contains, domain, expected
    ):
        config = tmp_module_repository[4]

        if repository == "application":
            config.switch_to_application_config()

        elif repository == "package":
            config.switch_to_package_config()

        if not contains:
            assert module not in config.get_repository()[["domains"]].keys()
        else:
            assert module in config.get_repository()[["domains"]].keys()

        config.add_domain(module, domain)
        assert all(
            domain in config.get_repository()[["domains", module]]
            for domain in expected
        )
        config.save()

    @pytest.mark.parametrize(
        "repository, module, domain, error",
        [
            (
                "package",
                "i18n_tool",
                "usage",
                "The module 'i18n_tool' is not registered.",
            ),
            (
                "package",
                "i18n_tools",
                "errors",
                "The domain 'errors' is already associated with the module 'i18n_tools'.",
            ),
            (
                "application",
                "disco",
                "concert",
                "The domain 'concert' is already associated with the module 'disco'.",
            ),
            (
                "application",
                "disco/author",
                "utils",
                "The module 'disco/author' is not registered.",
            ),
        ],
    )
    def test_add_domain_with_failure(
        self, tmp_module_repository, repository, module, domain, error
    ):
        config = tmp_module_repository[4]

        if repository == "application":
            config.switch_to_application_config()

        elif repository == "package":
            config.switch_to_package_config()

        with pytest.raises(ValueError, match=str(error)):
            config.add_domain(module, domain)

    @pytest.mark.parametrize(
        "repository, module, domain, expected",
        [
            ("package", "i18n_tools", "errors", True),
            ("package", "i18n_tools", "errors", False),
            ("application", "discot", "concert", False),
            ("application", "disco", "concert", True),
            ("application", "django-fsm_tools/context", "output", True),
        ],
    )
    def test_remove_domain(
        self, tmp_module_repository, repository, module, domain, expected
    ):
        config = tmp_module_repository[4]

        if repository == "application":
            config.switch_to_application_config()

        elif repository == "package":
            config.switch_to_package_config()

        if expected:
            assert config.remove_domain(module, domain)
        else:
            assert not config.remove_domain(module, domain)

        config.save()

    def test_clean_domain(self, tmp_module_repository):
        config = tmp_module_repository[4]
        config.clean_domains("disco/authors")
        assert "disco/authors" not in config.get_repository()["domains"].keys()

    @pytest.mark.parametrize(
        "repository, module, expected",
        [
            ("application", "disco/locale", True),
            ("application", "locales/disco/authors", True),
            ("application", "locales/disco/authors", False),
        ],
    )
    def test_remove_module(self, tmp_module_repository, repository, module, expected):
        config = tmp_module_repository[4]
        if repository == "application":
            config.switch_to_application_config()
        elif repository == "package":
            config.switch_to_package_config()

        if expected:
            assert config.remove_module(module)
            assert module not in config.get_repository()[["paths", "modules"]]
            assert module not in config.get_repository()["domains"].keys()
            config.save()
        else:
            assert not config.remove_module(module)


class TestConfigTranslators:
    @pytest.mark.parametrize(
        "repository, translator_data, valid, exception, error_message",
        [
            (
                "application",
                {
                    "name": "Translator1",
                    "url": "https://dupont.org",
                    "status": "free",
                    "api_key": "apikey123",
                    "supported_languages": ["en", "fr", "es"],
                    "translation_type": "general",
                    "cost_per_translation": 0.0,
                    "request_limit": 1000,
                    "key_expiration": (datetime.now() + timedelta(days=30)).strftime(
                        "%Y-%m-%d"
                    ),
                    "priority": 1,
                    "success_rate": 99.0,
                    "max_text_size": 1000,
                    "payment_plan": None,
                },
                True,
                None,
                "",
            ),
            (
                "application",
                {
                    "name": "Translator1",
                    "url": "https://dupont.org",
                    "status": "free",
                    "api_key": "apikey123",
                    "supported_languages": ["en", "fr", "es"],
                    "translation_type": "general",
                    "cost_per_translation": 0.0,
                    "request_limit": 1000,
                    "key_expiration": (datetime.now() + timedelta(days=30)).strftime(
                        "%Y-%m-%d"
                    ),
                    "priority": 1,
                    "success_rate": 99.0,
                    "max_text_size": 1000,
                    "payment_plan": None,
                },
                False,
                KeyError,
                "Translator 'Translator1' already exists.",
            ),
            (
                "package",
                {
                    "name": "Translator2",
                    "url": "https://dupont.org",
                    "status": "license",
                    "api_key": "apikey456",
                    "supported_languages": ["de", "it"],
                    "translation_type": "technical",
                    "cost_per_translation": 0.5,
                    "request_limit": 500,
                    "key_expiration": (datetime.now() + timedelta(days=60)).strftime(
                        "%Y-%m-%d"
                    ),
                    "priority": 2,
                    "success_rate": 95.0,
                    "max_text_size": 5000,
                    "payment_plan": "monthly",
                },
                True,
                None,
                "",
            ),
            (
                "package",
                {
                    "name": "Translator3",
                    "url": "https://dupont.com",
                    "status": "license",
                    "api_key": "apikey456",
                    "supported_languages": ["de", "it"],
                    "translation_type": "technical",
                    "cost_per_translation": 0.5,
                    "request_limit": 500,
                    "key_expiration": (datetime.now() + timedelta(days=60)).strftime(
                        "%Y-%m-%d"
                    ),
                    "priority": 2,
                    "success_rate": 95.0,
                    "max_text_size": 5000,
                    "payment_plan": "monthly",
                },
                False,
                ValueError,
                "Unable to connect to server.",
            ),
            (
                "package",
                {
                    "name": "Translator4",
                    "url": "https://joe.com",
                    "status": "license",
                    "api_key": "apikey456",
                    "supported_languages": ["de", "it"],
                    "translation_type": "technical",
                    "cost_per_translation": 0.5,
                    "request_limit": 500,
                    "key_expiration": "2025-01-01",
                    "priority": 2,
                    "success_rate": 95.0,
                    "max_text_size": 5000,
                    "payment_plan": "monthly",
                },
                False,
                ValueError,
                "The expiration date '2025-01-01' is in the past.",
            ),
            (
                "application",
                {
                    "name": "Translator3",
                    "url": "https://doe.com",
                    "status": "private",
                    "api_key": "apikey456",
                    "supported_languages": ["fr", "en", "ga", "it"],
                    "translation_type": "technical",
                    "cost_per_translation": 0.5,
                    "request_limit": 500,
                    "priority": 2,
                    "success_rate": 95.0,
                    "max_text_size": 5000,
                    "payment_plan": "monthly",
                },
                True,
                None,
                "",
            ),
        ],
    )
    def test_add_translator(
        self,
        tmp_module_repository,
        repository,
        translator_data,
        valid,
        exception,
        error_message,
    ):
        config = tmp_module_repository[4]
        if repository == "application":
            config.switch_to_application_config()
        elif repository == "package":
            config.switch_to_package_config()

        if valid:
            config.add_translator(**translator_data)
            assert translator_data["name"] in config.get_repository()["translators"]
            config.save()
        else:
            expected_msg = error_message

    @pytest.mark.parametrize(
        "repository, translator, status, performance, cost",
        [
            ("application", "GoogleTranslate", "free", 99.5, None),
            ("application", "Translator3", "private", 95.0, 0.5),
        ],
    )
    def test_get_translator(
        self, tmp_module_repository, repository, translator, status, performance, cost
    ):
        config = tmp_module_repository[4]
        if repository == "application":
            config.switch_to_application_config()
        elif repository == "package":
            config.switch_to_package_config()

        translator = config.get_translator(translator)

        assert translator[["details", "status"]] == status
        assert translator[["technical", "performance", "success_rate"]] == performance
        assert translator[["pricing", "cost_per_translation"]] == cost

    def test_lists_translators(self, tmp_module_repository):
        list_translators = tmp_module_repository[4].list_translators()
        assert len(list_translators) == 3

    @pytest.mark.parametrize(
        "repository, translator, data, valid, expected, exception, error_message",
        [
            (
                "application",
                "Translator1",
                {"details": {"translation_type": "Technical"}},
                True,
                [["details", "translation_type"], "Technical"],
                None,
                "",
            ),
            (
                "package",
                "Translator4",
                {},
                False,
                [],
                KeyError,
                "Translator 'Translator4' does not exist.",
            ),
            (
                "package",
                "Translator2",
                {"details": {"technical_type": "Technical"}},
                False,
                [],
                ValueError,
                "Invalid key 'details.technical_type' in updates.",
            ),
            (
                "package",
                "Translator2",
                {"technical": {"performance": [1000, 1]}},
                False,
                [],
                ValueError,
                "Expected a dictionary for 'technical.performance', but got 'list'.",
            ),
            (
                "package",
                "Translator2",
                {"details": {"translation_type": ("Technical", "Free")}},
                False,
                [],
                ValueError,
                "Type mismatch for 'details.translation_type': expected 'str', got 'tuple'.",
            ),
        ],
    )
    def test_update_translator(
        self,
        tmp_module_repository,
        repository,
        translator,
        data,
        valid,
        expected,
        exception,
        error_message,
    ):
        config = tmp_module_repository[4]
        if repository == "application":
            config.switch_to_application_config()
        elif repository == "package":
            config.switch_to_package_config()

        if valid:
            config.update_translator(translator, data)
            expected_translator = config.get_translator(translator)
            assert expected_translator[expected[0]] == expected[1]
            config.save()
        else:
            with pytest.raises(exception, match=error_message):
                config.update_translator(translator, data)

    @pytest.mark.parametrize(
        "repository, translator, valid",
        [
            ("package", "Translator2", True),
            ("package", "Translator4", False),
            ("package", "Translator2", False),
            ("application", "Translator1", True),
            ("application", "Translator3", True),
            ("application", "Translator1", False),
        ],
    )
    def test_remove_translator(
        self, tmp_module_repository, repository, translator, valid
    ):
        config = tmp_module_repository[4]
        if repository == "application":
            config.switch_to_application_config()
        elif repository == "package":
            config.switch_to_package_config()

        if valid:
            assert config.remove_translator(translator)
            assert translator not in config.get_repository()["translators"]
            config.save()
        else:
            assert not config.remove_translator(translator)


class TestConfigEdgeCases:
    def test_config_with_malformed_file(self, conf_tests, tmp_module_repository):
        """
        Test load configuration with a malformed file
        """
        tmp_module_repository[4].switch_to_application_config()
        tmp_module_repository[4].get_repository()[["paths", "settings"]] = conf_tests[
            "repository"
        ]["application"]["failed"]
        with pytest.raises(AttributeError):
            tmp_module_repository[4].load()
        tmp_module_repository[4].get_repository()[["paths", "settings"]] = conf_tests[
            "repository"
        ]["application"]["settings"]

    def test_config_with_unfitted_file(self, conf_tests, tmp_module_repository):
        tmp_module_repository[4].switch_to_application_config()
        tmp_module_repository[4].get_repository()[["paths", "config"]] = (
            tmp_module_repository[0][0]
            + "/"
            + conf_tests["repository"]["package"]["config"]
        )
        with pytest.raises(IndexError):
            tmp_module_repository[4].load()

    def test_toggle_repository(self, tmp_module_repository):
        config = tmp_module_repository[4]
        config.switch_to_package_config()
        assert config._current_config == "package"
        config.toggle_config()
        assert config._current_config == "application"


class TestConfigDetails:
    @pytest.mark.parametrize(
        "repository, details, expected",
        [
            (
                "application",
                {
                    "name": "Test App",
                    "summary": "Test Summary",
                    "description": "Test Description",
                    "version": "1.0.0",
                    "content_type": "text/plain",
                    "copyright_holder": "Test Copyright Holder",
                },
                {
                    "name": "Test App",
                    "summary": "Test Summary",
                    "description": "Test Description",
                    "version": "1.0.0",
                    "content_type": "text/plain",
                    "copyright_holder": "Test Copyright Holder",
                },
            ),
            (
                "package",
                {
                    "name": "Test Package",
                    "summary": None,
                    "description": "Test Package Description",
                    "version": None,
                    "content_type": None,
                    "copyright_holder": None,
                },
                {"name": "Test Package", "description": "Test Package Description"},
            ),
            (
                "application",
                {
                    "name": None,
                    "summary": "Only Summary",
                    "description": None,
                    "version": None,
                    "content_type": None,
                    "copyright_holder": None,
                },
                {"summary": "Only Summary"},
            ),
            (
                "package",
                {
                    "name": None,
                    "summary": None,
                    "description": None,
                    "version": "2.0.0",
                    "content_type": "application/json",
                    "copyright_holder": "New Copyright Holder",
                },
                {
                    "version": "2.0.0",
                    "content_type": "application/json",
                    "copyright_holder": "New Copyright Holder",
                },
            ),
        ],
    )
    def test_add_details(self, tmp_module_repository, repository, details, expected):
        """
        Test adding details to the configuration.

        This test verifies that the add_details function correctly updates the details
        of the repository configuration with the provided values.
        """
        config = tmp_module_repository[4]

        # Switch to the appropriate repository
        if repository == "application":
            config.switch_to_application_config()
        elif repository == "package":
            config.switch_to_package_config()

        # Save original values to restore later
        original_values = {}
        for key in details.keys():
            if key in config.get_repository()["details"]:
                original_values[key] = config.get_repository()["details"][key]

        try:
            # Call add_details with the provided parameters
            config.add_details(
                name=details.get("name"),
                summary=details.get("summary"),
                description=details.get("description"),
                version=details.get("version"),
                content_type=details.get("content_type"),
                copyright_holder=details.get("copyright_holder"),
            )

            # Verify that the values were correctly updated
            for key, value in expected.items():
                assert config.get_repository()["details"][key] == value

        finally:
            # Restore original values
            for key, value in original_values.items():
                config.get_repository()["details"][key] = value

    @pytest.mark.parametrize(
        "repository, key, value, valid, exception, error_message",
        [
            ("application", "name", "Updated App Name", True, None, None),
            ("package", "description", "Updated Package Description", True, None, None),
            ("application", "version", "2.0.0", True, None, None),
            ("package", "content_type", "application/json", True, None, None),
            (
                "application",
                "copyright_holder",
                "New Copyright Holder",
                True,
                None,
                None,
            ),
            (
                "package",
                "non_existent_key",
                "Some Value",
                False,
                KeyError,
                "The key non_existent_key is not in the details of the repository.",
            ),
            (
                "application",
                "name",
                123,
                False,
                TypeError,
                "The type of the value for name is not the same as the existing value.",
            ),
            (
                "package",
                "version",
                ["1.0.0"],
                False,
                TypeError,
                "The type of the value for version is not the same as the existing value.",
            ),
        ],
    )
    def test_update_details(
        self,
        tmp_module_repository,
        repository,
        key,
        value,
        valid,
        exception,
        error_message,
    ):
        """
        Test updating details in the configuration.

        This test verifies that the update_details function correctly updates a specific
        detail in the repository configuration, and that it properly handles error cases.
        """
        config = tmp_module_repository[4]

        # Switch to the appropriate repository
        if repository == "application":
            config.switch_to_application_config()
        elif repository == "package":
            config.switch_to_package_config()

        # Save original value to restore later
        original_value = None
        if key in config.get_repository()["details"]:
            original_value = config.get_repository()["details"][key]

        try:
            if valid:
                # Call update_details with the provided parameters
                config.update_details(key, value)

                # Verify that the value was correctly updated
                assert config.get_repository()["details"][key] == value
            else:
                # Verify that the appropriate exception is raised
                with pytest.raises(exception) as excinfo:
                    config.update_details(key, value)

                # Verify the error message if provided
                if error_message:
                    assert error_message in str(excinfo.value)

        finally:
            # Restore original value if it existed
            if original_value is not None and key in config.get_repository()["details"]:
                config.get_repository()["details"][key] = original_value


class TestConfigCleanup:
    def test_clean_domains(self, tmp_module_repository):
        config = tmp_module_repository[4]
        config.switch_to_application_config()
        config.clean_domains()
        assert config.get_repository()["domains"] == {}

    def test_clean_modules(self, tmp_module_repository):
        config = tmp_module_repository[4]
        config.switch_to_application_config()
        config.clean_modules()
        assert config.get_repository()[["paths", "modules"]] == []
        assert config.get_repository()["domains"] == {}
        config.switch_to_package_config()
        assert not config.get_repository()[["paths", "modules"]] == []
        assert not config.get_repository()["domains"] == {}
        config.clean_modules()
        assert config.get_repository()[["paths", "modules"]] == []
        assert config.get_repository()["domains"] == {}
