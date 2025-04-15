import json
import os
import tempfile
import uuid
from pathlib import Path

import pytest
import toml
import yaml
from conftest import conf_tests, tmp_module_repository
from email_validator import EmailNotValidError

from i18n_tools.classes import Singleton
from i18n_tools.config import Config, Repository
from i18n_tools.loaders import load_config, save_config
from i18n_tools.loaders.utils import _load_config_file


# Modifying Singleton to verify initials paraméters


def test_config_failed_path(tmp_module_repository):
    True_singleton = Singleton._instances
    Singleton._instances = {}
    with pytest.raises(FileNotFoundError):
        config = Config(tmp_module_repository[3][0] + "/" + "config.toml")
    Singleton._instances = True_singleton


def test_config_init(tmp_module_repository):
    True_singleton = Singleton._instances
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
    Singleton._instances = True_singleton


def test_config_singleton(tmp_module_repository):
    config_2 = Config()
    assert config_2 == tmp_module_repository[4]


# Testing config load, content en save


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
def test_load_and_save_config_file(tmp_module_repository, source, destination, valid):
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
    tmp_module_repository[4].get_repository()[["paths", "settings"]] = "i18n-tools.yaml"


def test_load_config_file_not_found(conf_tests, tmp_module_repository):
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


def test_save_config_unknown_directory(conf_tests, tmp_module_repository):
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


# Test set and get functions


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
def test_set_config(conf_tests, tmp_function_repository, path, value, exp_value, valid, exp_except):
    config = tmp_function_repository[4]
    if valid:
        config.set(path, value)
        assert config.get(path) == exp_value
    else:
        with pytest.raises(exp_except):
            config.set(path, value)


@pytest.mark.parametrize("switch, valid, module, extension, expected_name, exception", [
    ("application", True, "discotheque", "json", "discotheque", None),
    ("package", True, "i18n_tools", "yaml", "fsm-tools", None),
    ("application", False, "discotheque", "csv", "discotheque", ValueError),
    ("application", False, "discotheque", "yaml", "discotheque", FileNotFoundError),
    ("package", False, "i18n-tools", "json", "", IOError),
])
def test_set_config_repository(conf_tests, tmp_function_repository, switch, valid, module, extension, expected_name,
                               exception):
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


def test_set_config_repository_failed_directory(conf_tests, tmp_function_repository):
    config = Config()
    with pytest.raises(FileNotFoundError):
        config.switch_to_application_config()
        config.set_repository(
            tmp_function_repository[2][0] + "/discotheque/locales/_i18n_tools/i18n-tools.json",
            "json",
            "discotheque"
        )



# malformed files and paths


def test_config_with_malformed_file(conf_tests, tmp_module_repository):
    """
    Test load configuration with malformed file
    """
    tmp_module_repository[4].get_repository()[["paths", "settings"]] = conf_tests[
        "repository"
    ]["application"]["failed"]
    with pytest.raises(AttributeError):
        tmp_module_repository[4].load()
    tmp_module_repository[4].get_repository()[["paths", "settings"]] = conf_tests[
        "repository"
    ]["application"]["settings"]


def test_config_with_unfitted_file(conf_tests, tmp_module_repository):
    tmp_module_repository[4].get_repository()[["paths", "config"]] = (
            tmp_module_repository[0][0]
            + "/"
            + conf_tests["repository"]["package"]["config"]
    )
    with pytest.raises(IndexError):
        tmp_module_repository[4].load()
