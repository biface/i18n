import pytest
import tempfile
from pathlib import Path
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

    config_yaml.write_text("""
        paths:
          application:
            - app/locales
        languages:
          source: en
          fallback: fr
        domains:
          package: [domain1]
          application: [domain2, domain3]
        """)

    return  list((temp_dir, locales_dir, temp_path, config_yaml, config_toml))

temp_data = temp_dir_with_locales()
config = Config(temp_data[3])

def test_config_singleton():
    config_2 = Config()
    assert config == config_2

def test_config_with_temp_file():
    """
    Test Config loading from a temporary file.
    """
    # Use the temporary file for Config initialization
    config.load()
    assert config.setup[['languages','source']] == "en"
    assert config.setup[['languages', 'fallback']] == "fr"
    assert config.setup[['domains','package']] == ["domain1"]
    assert config.setup[['domains', 'application']] == ["domain2", "domain3"]


def test_config_save_with_temp_file(tmp_path):
    """
    Test saving configuration to a temporary file.
    """
    save_path = temp_data[2] / "output-config.toml"
    # Initialize Config and modify values
    config.setup[['paths','config']] = str(save_path)
    config.setup[['languages']].update({"source": "fr-FR", "fallback": "es"})
    config.setup[['languages','application']] = ["test/locales"]
    config.setup[['domains', 'application']] = ["domainX", "domainY"]
    # Save the configuration
    config.save()
    assert Path(config.setup[['paths','config']]).exists()
    config.load()
    # Verify the saved content
    assert config.setup[['languages','source']] == "fr-FR"
    assert config.setup[['languages','fallback']]  == "es"
    assert config.setup[['languages','application']] == ["test/locales"]
    assert config.setup[['domains','application']] == ["domainX", "domainY"]