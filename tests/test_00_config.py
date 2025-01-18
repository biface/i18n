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
              - app/locales
          languages:
            source: en
            hierarchy:
              fr: ["fr-FR", "fr-BE", "fr-CA"]
              en: ["en-IE", "en-US", "en-GB"]
            fallback: fr
          domains:
            package: [domain1]
            application: [domain2, domain3]
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
              - app/locales
          language:
            source: en
            hierarchy:
              fr: ["fr-FR", "fr-BE", "fr-CA"]
              en: ["en-IE", "en-US", "en-GB"]
            fallback: fr
          domains:
            package: [domain1]
            application: [domain2, domain3]
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

    return list((temp_dir, locales_dir, temp_path, config_yaml, config_toml, config_err_yaml))


temp_data = temp_dir_with_locales()
config = Config(temp_data[3])


def test_config_singleton():
    config_2 = Config()
    assert config == config_2


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
    assert config.setup[["domains", "application"]] == ["domain2", "domain3"]
    assert config.get(["details", "name"]) == "Configuration test file"
    assert config.get(["authors", "123e4567-e89b-12d3-a456-426614174000", "first_name"]) == "John"
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


def test_config_set_with_key_controls():
    config.set("details", {"name": "A configuration for life", "description": "This or nothing"})
    assert config.get(["details", "name"]) == "A configuration for life"
    assert config.get(["details", "description"]) == "This or nothing"
    with pytest.raises(KeyError):
        config.set("details", {"name": "A configuration for life", "descriptions": "This or nothing"})


def test_config_unknown_file():
    config.setup[["paths", "config"]] = "o18n-tools.yaml"
    with pytest.raises(FileNotFoundError):
        config.load()
    config.set(["setup", "paths", "config"], temp_data[3])


@pytest.mark.parametrize("args, expected_exception",
    [
        (("", {}), ValueError),
        (((1,2), {}), ValueError),
        (([], "Path must be specified"), ValueError),
        (({'key':1}, {}), ValueError),
        (("unknown", {}), KeyError),
        (("details", "string"), TypeError),
    ])
def test_config_set_errors(args, expected_exception):
    with pytest.raises(expected_exception):
        config.set(*args)

def test_config_set_errors_special():
    with pytest.raises(TypeError):
        config.set("details", "string")
        config.set(["details", "name"], ["A test for life"])


def test_add_author():
    config.add_author("Albert",
                      "Dupont",
                      "albert.dupont@local.net",
                      "",
                      ["en", "fr"])
    assert config.get_author("123e4567-e89b-12d3-a456-426614174000")["email"] == "john.doe@example.com"

def test_add_author_email_already_exists():
    with pytest.raises(KeyError):
        config.add_author("Albert",
                          "Dupond",
                          "albert.dupont@local.net",
                          "",
                          ["en", "fr"])

def test_add_author_email_error():
    with pytest.raises(EmailNotValidError):
        config.add_author("Albert",
                          "Durand",
                          "albert@host",
                          "",
                          ["en", "fr"])

def test_get_author_by_email():
    assert config.get_author("albert.dupont@local.net")["email"] == "albert.dupont@local.net"

def test_get_autor_error_false_uuid():
    with pytest.raises(KeyError):
        config.get_author(str(uuid.uuid4()))

def test_get_autor_email_error():
    with pytest.raises(ValueError):
        config.get_author("albert@host")

def test_remove_author():
    assert config.remove_author("albert.dupont@local.net") == True
    config.add_author("Albert",
                      "Dupont",
                      "albert.dupont@local.net",
                      "",
                      ["en", "fr"])
    id = config._email_index["albert.dupont@local.net"]
    assert config.remove_author(id) == True

@pytest.mark.parametrize("author, flag", [
    ("lbert.dupont@local.net", False),
    ("albert.dupont@local.net", False),
    (str(uuid.uuid4()), False),
])
def test_remove_author_unsuccessful(author, flag):
    assert config.remove_author(author) == flag

def test_remove_author_error():
    with pytest.raises(ValueError):
        config.remove_author("albert@host")
