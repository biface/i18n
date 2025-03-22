import tempfile
import uuid
import yaml
import toml
import json

from pathlib import Path

import pytest
from email_validator import EmailNotValidError

from i18n_tools.config import Config, Repository
from i18n_tools.loaders.repository import load_config, save_config
from i18n_tools.loaders.utils import _load_config_file

def temp_dir_with_locales():
    """
    Fixture that creates a temporary directory and returns it
    :return:
    """
    temp_dir = tempfile.TemporaryDirectory()
    temp_path = Path(temp_dir.name)
    locales_dir = temp_path / "locales"
    locales_dir.mkdir(parents=True, exist_ok=True)

    config_yaml = temp_path / "config.yaml"
    config_toml = temp_path / "config.toml"
    config_err_yaml = temp_path / "config_err.yaml"

    config_yaml.write_text(
        """
        setup:
          paths:
            application:
                base: ''
                modules:
                  - mod1/
                  - mod2/pkg1/
                  - mod2/pkg2/
          languages:
            source: en
            hierarchy:
              fr: ["fr-FR", "fr-BE", "fr-CA"]
              en: ["en-IE", "en-US", "en-GB"]
            fallback: fr
          domains:
            package:
              "i18n_tools":
                - "domain1"
            application:
              "mod1":
                - "domain2"
                - "domain3"
              "mod2/pkg1/":
                - "domain4"
                - "domain5"
              "mod2/pkg2/":
                - "domain6"
                - "domain7"
        details:
            name: "Configuration test file"
            description: "This is a temporary configuration test file"
        authors:
            123e4567-e89b-12d3-a456-426614174000:
                first_name: "John"
                last_name: "Doe"
                email: "john.doe@example.com"
                url: "https://johndoe.com"
                languages:                               
                    - "en-US"
                    - "fr-CA"
        """
    )

    config_err_yaml.write_text(
        """
        setup:
          paths:
            application:
                base: ''
                modules:
                    - mod1/
                    - mod2/pkg1/
                    - mod2/pkg2/
          language:
            source: en
            hierarchy:
              fr: ["fr-FR", "fr-BE", "fr-CA"]
              en: ["en-IE", "en-US", "en-GB"]
            fallback: fr
          domains:
            package:
              "i18n_tools": ["domain1"]
            application:
              "mod1/": ["domain2", "domain3"]
              "mod2/pkg1/": ["domain4", "domain5"]
              "mod2/pkg2/": ["domain6", "domain7"]
        details:
            name: "Configuration test file"
            description: "This is a temporary configuration test file"
        authors:
            123e4567-e89b-12d3-a456-426614174000:
                first_name: "John"
                last_name: "Doe"
                email: "john.doe@example.com"
                url: "https://johndoe.com"
                languages:                               
                    - "en-US"
                    - "fr-CA"
        """
    )

    return list(
        (temp_dir, locales_dir, temp_path, config_yaml, config_toml, config_err_yaml)
    )


temp_data = temp_dir_with_locales()
config = Config(temp_data[3])

def test_config_singleton():
    config_2 = Config()
    assert config == config_2


# Testing config load, content en save


def test_config_with_malformed_file():
    """
    Test load configuration with malformed file
    """
    c_path = config.get(["setup", "paths", "config"])
    print(c_path, "-", temp_data[5])
    config.set(["setup", "paths", "config"], temp_data[5])
    with pytest.raises(AttributeError):
        config.load()
    config.set(["setup", "paths", "config"], temp_data[3])


@pytest.fixture
def config_data():
    return {
        "setup": {
            "paths": {
                "config": "/home/fabricemoutte/Personnel/dev/python/i18n/tests/locales/i18n-tools.json",
                "package": {
                    "locale": "/home/fabricemoutte/Personnel/dev/python/i18n/src/i18n_tools/locales",
                    "base": "/home/fabricemoutte/Personnel/dev/python/i18n/src",
                    "modules": ["i18n_tools"],
                },
                "application": {
                    "base": "",
                    "modules": ["mod-1/", "mod-2/pkg-1/", "mod-2/pkk-2/"],
                },
            },
            "domains": {
                "package": {"i18n_tools": ["api", "classes"]},
                "application": {
                    "mod-1/": ["errors", "information"],
                    "mod-2/pkg-1/": ["usages", "information"],
                    "mod-2/pkg-2/": ["information", "errors"],
                },
            },
            "languages": {
                "source": "en",
                "hierarchy": {
                    "fr": ["fr-FR", "fr-BE", "fr-CA"],
                    "en": ["en-IE", "en-US", "en-GB"],
                },
                "fallback": "fr",
            },
            "translators": {
                "GoogleTranslate": {
                    "details": {
                        "name": "GoogleTranslate",
                        "url": "https://translate.google.com",
                        "status": "free",
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
                }
            },
        },
        "details": {
            "name": "Configuration test file",
            "description": "This is a temporary configuration test file",
        },
        "authors": {
            "123e4567-e89b-12d3-a456-426614174000": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "url": "https://johndoe.com",
                "languages": ["en-US", "fr-CA"],
            }
        },
    }


@pytest.fixture
def temp_config_files(tmp_path, config_data):

    yaml_path = tmp_path / "config.yaml"
    with open(yaml_path, "w") as yaml_file:
        yaml.safe_dump(config_data, yaml_file)

    toml_path = tmp_path / "config.toml"
    with open(toml_path, "w") as toml_file:
        toml.dump(config_data, toml_file)

    json_path = tmp_path / "config.json"
    with open(json_path, "w") as json_file:
        json.dump(config_data, json_file)

    return [(yaml_path, "yaml"), (toml_path, "toml"), (json_path, "json")]


@pytest.mark.parametrize(
    "config_path, config_format",
    [("config.yaml", "yaml"), ("config.toml", "toml"), ("config.json", "json")],
)
def test_load_config_file(temp_config_files, config_path, config_format):
    """Test loading configuration files in different formats."""
    # Find the correct path based on the config_format
    config_file_path = next(
        (path for path, fmt in temp_config_files if fmt == config_format), None
    )

    if config_file_path is None:
        pytest.fail(f"Configuration file for format '{config_format}' not found.")

    # Load the configuration file
    config_data = _load_config_file(config_file_path)

    # Assert the loaded data matches the expected data
    assert config_data["setup"]["paths"]["package"]["modules"] == ["i18n_tools"]


@pytest.fixture
def setup_temp_dir(tmp_path, config_data):
    # Create temporary directories and configuration files

    # Create root directory
    root_dir = tmp_path / "root"
    root_dir.mkdir()

    # Create locales directory
    locales_dir = tmp_path / "locales"
    locales_dir.mkdir()

    # Create configuration files in root directory
    root_yaml = root_dir / "i18n-tools.yaml"
    with open(root_yaml, "w") as yaml_file:
        yaml.safe_dump(config_data, yaml_file)

    root_toml = root_dir / "i18n-tools.toml"
    with open(root_toml, "w") as toml_file:
        toml.dump(config_data, toml_file)

    root_json = root_dir / "i18n-tools.json"
    with open(root_json, "w") as json_file:
        json.dump(config_data, json_file)

    # Create configuration files in locales directory
    locales_yaml = locales_dir / "i18n-tools.yaml"
    with open(locales_yaml, "w") as yaml_file:
        yaml.safe_dump(config_data, yaml_file)

    return tmp_path


def test_load_config_from_root(setup_temp_dir, monkeypatch, config_data):
    """Test loading configuration from the root directory."""
    temp_dir = setup_temp_dir
    root_dir = temp_dir / "root"

    # Mock the current working directory to be the temporary root directory
    monkeypatch.chdir(root_dir)

    loaded_data = load_config()
    assert loaded_data == config_data


def test_load_config_from_locales(setup_temp_dir, monkeypatch, config_data):
    """Test loading configuration from the locales directory."""
    temp_dir = setup_temp_dir
    locales_dir = temp_dir / "locales"

    # Mock the current working directory to be the temporary locales directory
    monkeypatch.chdir(locales_dir)

    loaded_data = load_config()
    assert loaded_data == config_data


def test_load_config_not_found(setup_temp_dir, monkeypatch):
    """Test loading configuration when no config file is found."""
    temp_dir = setup_temp_dir
    empty_dir = temp_dir / "empty"
    empty_dir.mkdir()

    # Mock the current working directory to be an empty directory
    monkeypatch.chdir(empty_dir)

    with pytest.raises(FileNotFoundError, match="No configuration file found"):
        load_config()


def test_load_config_file_unsupported_format(tmp_path):
    """Test loading an unsupported configuration file format."""
    unsupported_path = tmp_path / "config.txt"
    unsupported_path.write_text("key=value")

    with pytest.raises(Exception):
        _load_config_file(unsupported_path)


def test_load_config_file_not_found(tmp_path):
    """Test loading a configuration file that does not exist."""
    non_existent_path = tmp_path / "non_existent.yaml"

    with pytest.raises(Exception, match="Error loading configuration file"):
        _load_config_file(non_existent_path)


def test_load_config_file_invalid_yaml(tmp_path):
    """Test loading an invalid YAML configuration file."""
    invalid_yaml_path = tmp_path / "invalid.yaml"
    invalid_yaml_path.write_text("key: value\ninvalid_yaml")

    with pytest.raises(Exception, match="Error loading configuration file"):
        _load_config_file(invalid_yaml_path)


@pytest.mark.parametrize(
    "config_path, config_format",
    [
        ("i18n-tools.yaml", "yaml"),
        ("i18n-tools.json", "json"),
        ("i18n-tools.toml", "toml"),
    ],
)
def test_save_config_file(tmp_path, config_path, config_format, config_data):
    """Test saving configuration files in different formats."""
    config_file_path = tmp_path / config_path
    save_config(config_file_path, config_data)

    # Load the saved configuration file
    loaded_data = _load_config_file(config_file_path)

    # Assert the loaded data matches the expected config_data
    assert loaded_data == config_data


def test_save_config_unsupported_format(tmp_path, config_data):
    """Test saving configuration with an unsupported file format."""
    unsupported_path = tmp_path / "config.txt"

    with pytest.raises(ValueError, match="Unsupported file format"):
        save_config(unsupported_path, config_data)


def test_save_config_unknown_directory(config_data):
    with pytest.raises(Exception):
        save_config("/tmp/unknown/test.json", config_data)


def test_config_with_temp_file():
    """
    Test Config loading from a temporary file.
    """
    # Use the temporary file for Config initialization
    config.load()
    assert config.get(["setup", "languages", "source"]) == "en"
    assert config.setup[["languages", "fallback"]] == "fr"
    assert config.setup[["domains", "package", "i18n_tools"]] == ["domain1"]
    assert config.setup[["domains", "application", "mod1"]] == ["domain2", "domain3"]
    assert config.setup[["domains", "application", "mod2/pkg1/"]] == [
        "domain4",
        "domain5",
    ]
    assert config.setup[["domains", "application", "mod2/pkg2/"]] == [
        "domain6",
        "domain7",
    ]
    assert config.get(["details", "name"]) == "Configuration test file"
    assert (
        config.get(["authors", "123e4567-e89b-12d3-a456-426614174000", "first_name"])
        == "John"
    )
    with pytest.raises(KeyError):
        config.get(["detail", "name"])


def test_config_save_with_temp_file(tmp_path):
    """
    Test saving configuration to a temporary file.
    """
    save_path = temp_data[2] / "output-config.yaml"
    # Initialize Config and modify values
    config.setup[["paths", "config"]] = str(save_path)
    config.setup[["languages"]].update({"source": "fr-FR", "fallback": "es"})
    config.setup[["languages", "application"]] = ["test/locales"]
    # Save the configuration
    config.save()
    assert Path(config.setup[["paths", "config"]]).exists()
    config.load()
    # Verify the saved content
    assert config.setup[["languages", "source"]] == "fr-FR"
    assert config.setup[["languages", "fallback"]] == "es"
    assert config.setup[["languages", "application"]] == ["test/locales"]
    config.set(["setup", "paths", "config"], "")
    with pytest.raises(ValueError):
        config.save()


# Test set and get functions


def test_config_set_with_key_controls():
    config.set(
        "details",
        {"name": "A configuration for life", "description": "This or nothing"},
    )
    assert config.get(["details", "name"]) == "A configuration for life"
    assert config.get(["details", "description"]) == "This or nothing"
    with pytest.raises(KeyError):
        config.set(
            "details",
            {"name": "A configuration for life", "descriptions": "This or nothing"},
        )


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
    config.set_application_repository(str(application_path), config.get(["setup", "paths", "application", "modules"]))
    assert config.get(["setup", "paths", "application", "base"]) == str(application_path)
    assert config.get(["setup", "paths", "application", "locale"]) == str (application_path / "locales")

def test_config_application_repository_failure(tmp_path):
    application_path = tmp_path / "unknown"
    with pytest.raises(FileNotFoundError):
        config.set_application_repository(str(application_path))
    assert config.get(["setup", "paths", "application", "base"]) != str(application_path)
    assert config.get(["setup", "paths", "application", "locale"]) != str(application_path / "locales")

def test_config_update_application_repository(tmp_path):
    application_path = tmp_path / "repository"
    modules = config.get(["setup", "paths", "application", "modules"])
    application_path.mkdir(parents=True, exist_ok=True)
    config.update_application_repository(str(application_path))
    assert config.get(["setup", "paths", "application", "base"]) == str(application_path)
    assert config.get(["setup", "paths", "application", "locale"]) == str(application_path / "locales")
    config.update_application_repository(modules=["mod3"])
    assert config.get(["setup", "paths", "application", "modules"]) == ["mod3"]
    config.update_application_repository(modules=modules)

def test_config_update_application_repository_failure(tmp_path):
    application_path = tmp_path / "unknown"
    with pytest.raises(ValueError):
        config.update_application_repository(str(application_path))
    assert config.get(["setup", "paths", "application", "base"]) != str(application_path)
    assert config.get(["setup", "paths", "application", "locale"]) != str(application_path / "locales")
    assert config.get(["setup", "paths", "application", "modules"]) == ["mod1/", "mod2/pkg1/", "mod2/pkg2/"]

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
