import os
import json
import tempfile
import uuid
from pathlib import Path

import pytest
import toml
import yaml
from email_validator import EmailNotValidError

from i18n_tools.config import Config, Repository
from i18n_tools.loaders import load_config, save_config
from i18n_tools.loaders.utils import _load_config_file

from conftest import conf_tests, tmp_module_repository

def test_config_singleton(tmp_module_repository):
    config_2 = Config()
    assert config_2 == tmp_module_repository[4]

# Testing config load, content en save

def test_config_with_malformed_file(conf_tests, tmp_module_repository):
    """
    Test load configuration with malformed file
    """
    tmp_module_repository[4].get_repository()[['paths', 'settings']] = conf_tests['repository']['application']['failed']
    with pytest.raises(AttributeError):
        tmp_module_repository[4].load()

@pytest.mark.parametrize(
    "source, destination, valid",
    [("i18n-tools.yaml", "config.toml", True),
     ("config.toml", "i18n-settings.json", True),
     ("i18n-settings.json", "config.text", False),
     ("i18n-settings.json", "i18n-tools.toml", True),
     ("config.toml", "i18n-tools.csv", False),
     ],
)
def test_load_and_save_config_file(tmp_module_repository, source, destination, valid):
    """Test loading configuration files in different formats."""
    tmp_module_repository[4].get_repository()[['paths', 'settings']] = source
    tmp_module_repository[4].load()
    destination_file = tmp_module_repository[4].get_repository()[['paths', 'config']] + "/" + destination
    tmp_module_repository[4].get_repository()[['paths', 'settings']] = destination
    assert not os.path.exists(destination_file)
    if valid:
        tmp_module_repository[4].save()
        assert os.path.exists(destination_file)
    else:
        with pytest.raises(Exception):
            tmp_module_repository[4].save()


def test_load_config_file_not_found(conf_tests, tmp_module_repository):
    """Test loading a configuration file that does not exist."""
    tmp_module_repository[4].get_repository()[['paths', 'config']] = conf_tests['repository']['other']
    with pytest.raises(FileNotFoundError, match="Configuration file not found: test-function/i18n-tools.yaml"):
        tmp_module_repository[4].load()
    tmp_module_repository[4].get_repository()[['paths', 'config']] = conf_tests['repository']['application']['config']


def test_save_config_unknown_directory(conf_tests, tmp_module_repository):
    """Test loading a configuration file that does not exist."""
    tmp_module_repository[4].get_repository()[['paths', 'config']] = conf_tests['repository']['other']
    with pytest.raises(Exception):
        tmp_module_repository[4].save()
    tmp_module_repository[4].get_repository()[['paths', 'config']] = conf_tests['repository']['application']['config']

# Test set and get functions

@pytest.mark.parametrize("path, value, expected, valid", [
    (["details", "name"],
     {"name": "Test"}, "Test", True),
])
def test_config_set_with_key_controls(conf_tests, tmp_module_repository, path, value, expected, valid):
    if valid:
        tmp_module_repository[4].set(path, value)
        assert tmp_module_repository[4].get_repository()[path] == expected
    else:
        with pytest.raises(AttributeError):
            tmp_module_repository[4].set(path, value)

def test_config_set_with_nested_key_update():
    # Test updating a nested key in a NestedDictionary
    config.set(["setup", "paths", "application", "base"], "/new/base/path")
    assert config.get(["setup", "paths", "application", "base"]) == "/new/base/path"

    # Test updating a nested key with an invalid key
    with pytest.raises(KeyError):
        config.set(["setup", "paths", "application", "unknown_key"], "value")


def test_config_set_with_invalid_nested_update():
    # Test invalid nested update with incorrect type
    with pytest.raises(TypeError):
        config.set(["setup"], 12345)  # Should be a string

    # Test invalid nested update with non-existent key
    with pytest.raises(KeyError):
        config.set(["setup", "languages", "unknown_key"], "value")


def test_config_unknown_file():
    config.setup[["paths", "config"]] = "o18n-tools.yaml"
    with pytest.raises(FileNotFoundError):
        config.load()
    config.set(["setup", "paths", "config"], temp_data[3])


@pytest.mark.parametrize(
    "args, expected_exception",
    [
        (("", {}), ValueError),
        (((1, 2), {}), ValueError),
        (([], "Path must be specified"), ValueError),
        (({"key": 1}, {}), ValueError),
        (("unknown", {}), KeyError),
        (("details", "string"), TypeError),
    ],
)
def test_config_set_errors(args, expected_exception):
    with pytest.raises(expected_exception):
        config.set(*args)


def test_config_set_errors_special():
    with pytest.raises(TypeError):
        config.set("details", "string")
        config.set(["details", "name"], ["A test for life"])


def test_config_set_with_type_check():
    # Test type compatibility check for direct attribute update
    with pytest.raises(TypeError):
        config.set("details", "This should be a dictionary")


def test_config_application_repository(tmp_path):
    application_path = tmp_path / "repository"
    application_path.mkdir(parents=True, exist_ok=True)
    config.set_application_repository(
        str(application_path), config.get(["setup", "paths", "application", "modules"])
    )
    assert config.get(["setup", "paths", "application", "base"]) == str(
        application_path
    )
    assert config.get(["setup", "paths", "application", "locale"]) == str(
        application_path / "locales"
    )


def test_config_application_repository_failure(tmp_path):
    application_path = tmp_path / "unknown"
    with pytest.raises(FileNotFoundError):
        config.set_application_repository(str(application_path))
    assert config.get(["setup", "paths", "application", "base"]) != str(
        application_path
    )
    assert config.get(["setup", "paths", "application", "locale"]) != str(
        application_path / "locales"
    )


def test_config_update_application_repository(tmp_path):
    application_path = tmp_path / "repository"
    modules = config.get(["setup", "paths", "application", "modules"])
    application_path.mkdir(parents=True, exist_ok=True)
    config.update_application_repository(str(application_path))
    assert config.get(["setup", "paths", "application", "base"]) == str(
        application_path
    )
    assert config.get(["setup", "paths", "application", "locale"]) == str(
        application_path / "locales"
    )
    config.update_application_repository(modules=["mod3"])
    assert config.get(["setup", "paths", "application", "modules"]) == ["mod3"]
    config.update_application_repository(modules=modules)


def test_config_update_application_repository_failure(tmp_path):
    application_path = tmp_path / "unknown"
    with pytest.raises(ValueError):
        config.update_application_repository(str(application_path))
    assert config.get(["setup", "paths", "application", "base"]) != str(
        application_path
    )
    assert config.get(["setup", "paths", "application", "locale"]) != str(
        application_path / "locales"
    )
    assert config.get(["setup", "paths", "application", "modules"]) == [
        "mod1/",
        "mod2/pkg1/",
        "mod2/pkg2/",
    ]


# Testing authors


def test_add_author():
    config.add_author("Albert", "Dupont", "albert.dupont@local.net", "", ["en", "fr"])
    assert (
        config.get_author("123e4567-e89b-12d3-a456-426614174000")["email"]
        == "john.doe@example.com"
    )


def test_add_author_email_already_exists():
    with pytest.raises(KeyError):
        config.add_author(
            "Albert", "Dupond", "albert.dupont@local.net", "", ["en", "fr"]
        )


def test_add_author_email_error():
    with pytest.raises(EmailNotValidError):
        config.add_author("Albert", "Durand", "albert@host", "", ["en", "fr"])


def test_get_author_by_email():
    assert (
        config.get_author("albert.dupont@local.net")["email"]
        == "albert.dupont@local.net"
    )


def test_get_autor_error_false_uuid():
    with pytest.raises(KeyError):
        config.get_author(str(uuid.uuid4()))


def test_get_autor_email_error():
    with pytest.raises(ValueError):
        config.get_author("albert@host")


def test_remove_author():
    assert config.remove_author("albert.dupont@local.net") == True
    config.add_author("Albert", "Dupont", "albert.dupont@local.net", "", ["en", "fr"])
    id = config._email_index["albert.dupont@local.net"]
    assert config.remove_author(id) == True


@pytest.mark.parametrize(
    "author, flag",
    [
        ("lbert.dupont@local.net", False),
        ("albert.dupont@local.net", False),
        (str(uuid.uuid4()), False),
    ],
)
def test_remove_author_unsuccessful(author, flag):
    assert config.remove_author(author) == flag


def test_remove_author_error():
    with pytest.raises(ValueError):
        config.remove_author("albert@host")


# Testing modules and domains


@pytest.mark.parametrize(
    "module_path",
    [
        "mod1/",
        "mod2/pkg1/",
        "mod2/pkg2/",
    ],
)
def test_existing_modules(module_path):
    assert module_path in config.setup[["paths", "application", "modules"]]


@pytest.mark.parametrize(
    "module_path",
    [
        "package-alpha/module-1",
        "package-alpha/module-2",
        "package-beta/module-a",
        "package-beta/module-b",
        "package-beta/module-c",
        "package-delta/module-1",
        "package-delta/module-2/sub-21",
        "package-delta/module-2/sub-22",
        "package-delta/module-2/sub-23",
    ],
)
def test_add_module(module_path):
    """
    Test adding modules to the manager.
    """
    config.add_module(module_path)
    assert module_path in config.setup[["paths", "application", "modules"]]


@pytest.mark.parametrize(
    "module_path",
    [
        "package-alpha/module-1",
        "package-alpha/module-2",
        "package-beta/module-a",
        "package-delta/module-1",
        "package-delta/module-2/sub-21",
    ],
)
def test_remove_module(module_path):
    """
    Test removing modules from the manager.
    """
    assert module_path in config.setup[["paths", "application", "modules"]]
    config.remove_module(module_path)
    assert module_path not in config.setup[["paths", "application", "modules"]]
    config.add_module(module_path)


@pytest.mark.parametrize(
    "module, domain",
    [
        ("package-alpha/module-1", "messages"),
        ("package-alpha/module-2", "errors"),
        ("package-beta/module-a", "notifications"),
        ("package-delta/module-1", "logs"),
        ("package-delta/module-2/sub-21", "configurations"),
        ("package-delta/module-2/sub-21", "informations"),
        ("package-delta/module-2/sub-21", "usages"),
        ("package-delta/module-2/sub-22", "usages"),
    ],
)
def test_add_domain(module, domain):
    """
    Test adding domains to a module.
    """
    config.add_domain(module, domain)
    assert domain in config.get(["setup", "domains", "application"])[module]


@pytest.mark.parametrize(
    "module, domain",
    [
        ("package-alpha/module-1", "messages"),
        ("package-alpha/module-2", "errors"),
        ("package-beta/module-a", "notifications"),
    ],
)
def test_remove_domain(module, domain):
    """
    Test removing domains from a module.
    """
    assert domain in config.get(["setup", "domains", "application"])[module]
    config.remove_domain(module, domain)
    assert not domain in config.get(["setup", "domains", "application"])[module]


@pytest.mark.parametrize(
    "module", ["package-delta/module-2/sub-21", "package-delta/module-2/sub-22"]
)
def test_clean_domains_for_module(module):
    """
    Test cleaning domains for a specific module.
    """
    config.clean_domains(module=module)
    domains = config.setup[["domains", "application"]]
    assert not any(entry[0] == module for entry in domains)


def test_clean_all_domains():
    config.clean_domains()
    assert not config.setup[["domains", "application"]]


def test_clean_modules():
    config.add_domain("package-alpha/module-1", "informations")
    config.clean_modules()
    assert not config.setup[["domains", "application"]]
    assert not config.setup[["paths", "application", "modules"]]


# Testing exceptions in modules and domains


@pytest.mark.parametrize(
    "module_path", ["package-alpha/module-1", "package-beta/module-a"]
)
def test_add_existing_module_raises_exception(module_path):
    """
    Test adding an already existing module raises an exception.
    """
    config.add_module(module_path)
    with pytest.raises(ValueError):
        config.add_module(module_path)
    config.remove_module(module_path)


@pytest.mark.parametrize(
    "module_path", ["package-alpha/module-1", "package-beta/module-a"]
)
def test_remove_nonexistent_module_raises_exception(module_path):
    """
    Test removing a nonexistent module raises an exception.
    """
    assert not config.remove_module(module_path)


@pytest.mark.parametrize(
    "module, domain",
    [
        ("package-alpha/module-1", "messages"),
        ("package-beta/module-a", "notifications"),
    ],
)
def test_add_domain_to_nonexistent_module_raises_exception(module, domain):
    """
    Test adding a domain to a nonexistent module raises an exception.
    """
    with pytest.raises(ValueError):
        config.add_domain(module, domain)


@pytest.mark.parametrize(
    "module, domain",
    [
        ("package-alpha/module-1", "messages"),
        ("package-beta/module-a", "notifications"),
    ],
)
def test_add_existing_domain_raises_exception(module, domain):
    """
    Test adding an already existing domain raises an exception.
    """
    config.add_module(module)
    config.add_domain(module, domain)  # Add domain first
    with pytest.raises(ValueError):
        config.add_domain(module, domain)


@pytest.mark.parametrize(
    "module, domain",
    [
        ("package-alpha/module-1", "messages"),
        ("package-beta/module-a", "notifications"),
    ],
)
def test_remove_nonexistent_domain_raises_exception(module, domain):
    """
    Test removing a nonexistent domain raises an exception.
    """
    config.clean_domains(module)  # Ensure module exists
    assert not config.remove_domain(module, domain)


@pytest.mark.parametrize(
    "package, path, assertion",
    [
        (True, ["base", "modules"], ["i18n_tools"]),
        (False, ["modules", "mod-1/"], ["errors", "information"]),
        (True, ["languages", "source"], "en"),
        (False, ["languages", "source"], "en"),
        (False, ["languages", "hierarchy", "fr"], ["fr-FR", "fr-BE", "fr-CA"]),
        (
            True,
            ["authors", "123e4567-e89b-12d3-a456-426614174000", "email"],
            "john.doe@example.com",
        ),
    ],
)
def test_config_repository(tmp_path, config_data, package, path, assertion):
    config_file_path = tmp_path / "repository_config.json"
    save_config(config_file_path, config_data)
    config.setup[["paths", "config"]] = config_file_path
    config.load()
    repository = config.repository(package)
    assert repository[path] == assertion


@pytest.fixture
def mock_config():
    config = Config()
    config.set(["setup", "paths", "application", "modules"], ["module1", "module2"])
    config.set(["details", "name"], "Test Project")
    return config


def test_repository_initialization(mock_config):
    repository = Repository.from_config(mock_config, package=True)
    assert repository.directory == mock_config.setup["paths"]["package"]
    assert repository.domains == mock_config.setup["domains"]["package"]
    assert repository.languages == mock_config.setup["languages"]
    assert repository.authors == mock_config.authors
    assert repository.details == mock_config.details


def test_repository_from_config_application(mock_config):
    repository = Repository.from_config(mock_config, package=False)
    assert repository.directory == mock_config.setup["paths"]["application"]
    assert repository.domains == mock_config.setup["domains"]["application"]


def test_repository_application_repr(mock_config):
    repository = Repository.from_config(mock_config, package=False)
    assert "Test Project" in repr(repository)
    assert "module1" in repr(repository)
    assert "en" in repr(repository)
    assert "fr" in repr(repository)


def test_repository_package_repr(mock_config):
    repository = Repository.from_config(mock_config, package=True)
    assert "Test Project" in repr(repository)
    assert "i18n_tools" in repr(repository)
    assert "en" in repr(repository)
    assert "fr" in repr(repository)
