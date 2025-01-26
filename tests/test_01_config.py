import tempfile
import uuid

from pathlib import Path

import pytest
from email_validator import EmailNotValidError

from i18n_tools.config import Config


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
            package: ["domain1"]
            application: [
                ["mod1", ["domain2", "domain3"]],
                ["mod2/pkg1", ["domain4", "domain5"]],
                ["mod2/pkg2", ["domain6", "domain7"]],
                ]
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
            package: ["domain1"]
            application: [
                ["mod1", ["domain2", "domain3"]],
                ["mod2/pkg1", ["domain4", "domain5"]],
                ["mod2/pkg2", ["domain6", "domain7"]],
                ]
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


def test_config_with_temp_file():
    """
    Test Config loading from a temporary file.
    """
    # Use the temporary file for Config initialization
    config.load()
    assert config.get(["setup", "languages", "source"]) == "en"
    assert config.setup[["languages", "fallback"]] == "fr"
    assert config.setup[["domains", "package"]] == ["domain1"]
    assert config.setup[["domains", "application"]] == [
        ["mod1", ["domain2", "domain3"]],
        ["mod2/pkg1", ["domain4", "domain5"]],
        ["mod2/pkg2", ["domain6", "domain7"]],
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
    save_path = temp_data[2] / "output-config.toml"
    # Initialize Config and modify values
    config.setup[["paths", "config"]] = str(save_path)
    config.setup[["languages"]].update({"source": "fr-FR", "fallback": "es"})
    config.setup[["languages", "application"]] = ["test/locales"]
    config.setup[["domains", "application"]] = ["domainX", "domainY"]
    # Save the configuration
    config.save()
    assert Path(config.setup[["paths", "config"]]).exists()
    config.load()
    # Verify the saved content
    assert config.setup[["languages", "source"]] == "fr-FR"
    assert config.setup[["languages", "fallback"]] == "es"
    assert config.setup[["languages", "application"]] == ["test/locales"]
    assert config.setup[["domains", "application"]] == ["domainX", "domainY"]
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
    domains = config.setup[["domains", "application"]]
    assert any(entry[0] == module and domain in entry[1] for entry in domains)


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
    assert any(
        entry[0] == module and domain in entry[1]
        for entry in config.setup[["domains", "application"]]
    )
    config.remove_domain(module, domain)
    assert not any(
        entry[0] == module and domain in entry[1]
        for entry in config.setup[["domains", "application"]]
    )


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
