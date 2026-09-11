"""
Tests for i18n_tools.loaders.settings (DD-41, #119) — the TOML/JSON/YAML
settings-file primitives backing Config/Repository, extracted from
01_loader/test_01_loader.py when loaders/settings.py was split out of
loaders/utils.py. Lives under tests/api/ because TestTomlOperations and
part of TestConfigFileOperations exercise the `.toml` branches, which
require the `api` extra.
"""

import json

import pytest
import toml

from i18n_tools.loaders.settings import (
    _load_config_file,
    _load_toml,
    _save_config_file,
    _save_toml,
)


@pytest.fixture(scope="function")
def toml_test_file(tmp_function_repository):
    toml_file = tmp_function_repository[3][1] / "test.toml"
    with open(toml_file, "w", encoding="utf-8") as f:
        toml.dump({"key": "value"}, f)
    return str(toml_file)


class TestTomlOperations:
    def test_load_toml(self, toml_test_file):
        assert _load_toml(str(toml_test_file)) == {"key": "value"}

    def test_load_toml_raise_exception(self):
        with pytest.raises(FileNotFoundError):
            _load_toml("nonexistent/path")

    def test_save_toml(self, toml_test_file):
        data = {"key": "new value"}
        _save_toml(toml_test_file, data)
        with open(toml_test_file, "r", encoding="utf-8") as f:
            loaded_data = toml.load(f)
        assert loaded_data == data

    def test_save_toml_raises_exception(self):
        with pytest.raises(FileNotFoundError):
            _save_toml("/nonexistent/path", {})


class TestConfigFileOperations:
    @pytest.mark.parametrize(
        "source, valid_s, destination, valid_d",
        [
            ("i18n-tools.json", False, "i18n-tools.json", False),
            ("i18n-tools.yaml", True, "i18n-tools.json", True),
            ("i18n-tools.yaml", True, "i18n-tools.csv", False),
            ("i18n-tools.json", True, "i18n-tools.toml", True),
            ("i18n-tools.txt", False, "i18n-tools.json", True),
            ("i18n-tools.toml", True, "config.toml", True),
        ],
    )
    def test_load_and_save_config(
        self, tmp_module_repository, source, valid_s, destination, valid_d
    ):
        source_file = (
            tmp_module_repository[2][1]
            / "fsm_tools"
            / "locales"
            / "_i18n_tools"
            / source
        )
        destination_file = (
            tmp_module_repository[2][1]
            / "fsm_tools"
            / "locales"
            / "_i18n_tools"
            / destination
        )
        if valid_s:
            data = _load_config_file(source_file)
            if valid_d:
                _save_config_file(destination_file, data)
            else:
                with pytest.raises(Exception):
                    _save_config_file(destination_file, data)
        else:
            with pytest.raises(Exception):
                _load_config_file(source_file)

    def test_load_and_save_config_failed_path(self):
        with pytest.raises(Exception):
            _load_config_file("non-existent-path/i18n-tools.json")
            _save_config_file("non-existent-path/i18n-tools.json", {})

    def test_load_config_file_yml_extension(self, tmp_path):
        """biface/i18n#26 — .yml is accepted by __check_config_extension()
        but _load_config_file()'s if/elif only matched ".yaml", silently
        falling through and returning None. _save_config_file() already
        handled ".yml" correctly; _load_config_file() must match it."""
        config_file = tmp_path / "config.yml"
        config_file.write_text("key: value\n", encoding="utf-8")
        result = _load_config_file(config_file)
        assert result == {"key": "value"}

    def test_load_config_file_malformed_content_raises_specific_error(self, tmp_path):
        """biface/i18n#26 — well-formed extension, malformed content. Before
        this fix, json.JSONDecodeError was caught and masked as a bare
        Exception with a generic message. The specific, actionable
        exception must now surface."""
        config_file = tmp_path / "config.json"
        config_file.write_text("{not valid json", encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            _load_config_file(config_file)
