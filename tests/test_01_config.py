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
    tmp_module_repository[4].get_repository()[['paths', 'settings']] = "i18n-tools.yaml"


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
