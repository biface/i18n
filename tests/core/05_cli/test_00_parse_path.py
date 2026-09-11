"""
Test module for cli._parse_i18t_path (DD-12 layout parsing, #39)
"""

import pytest

from i18n_tools.cli import CliError, _parse_i18t_path


class TestParseValidPath:
    def test_extracts_directory_language_domain_format(self, tmp_path):
        path = tmp_path / "fr-FR" / "LC_MESSAGES" / "messages.json.i18t"
        path.parent.mkdir(parents=True)
        path.write_text("{}")

        directory, language, domain, fmt = _parse_i18t_path(str(path))

        assert directory == str(path.parent)
        assert language == "fr-FR"
        assert domain == "messages"
        assert fmt == "json"

    def test_accepts_yaml_format(self, tmp_path):
        path = tmp_path / "en" / "LC_MESSAGES" / "ui.yaml.i18t"
        _, _, domain, fmt = _parse_i18t_path(str(path))
        assert domain == "ui"
        assert fmt == "yaml"

    def test_domain_with_dots_is_preserved(self, tmp_path):
        path = tmp_path / "en" / "LC_MESSAGES" / "ui.errors.json.i18t"
        _, _, domain, _ = _parse_i18t_path(str(path))
        assert domain == "ui.errors"


class TestParseInvalidPath:
    def test_missing_i18t_extension_raises(self, tmp_path):
        path = tmp_path / "en" / "LC_MESSAGES" / "messages.json"
        with pytest.raises(CliError, match="does not look like a translation file"):
            _parse_i18t_path(str(path))

    def test_missing_format_segment_raises(self, tmp_path):
        path = tmp_path / "en" / "LC_MESSAGES" / "messages.i18t"
        with pytest.raises(CliError, match="does not look like a translation file"):
            _parse_i18t_path(str(path))

    def test_unrecognized_format_raises(self, tmp_path):
        path = tmp_path / "en" / "LC_MESSAGES" / "messages.xml.i18t"
        with pytest.raises(CliError, match="does not look like a translation file"):
            _parse_i18t_path(str(path))

    def test_not_under_lc_messages_raises(self, tmp_path):
        path = tmp_path / "en" / "messages.json.i18t"
        with pytest.raises(CliError, match="LC_MESSAGES"):
            _parse_i18t_path(str(path))

    def test_no_language_directory_raises(self):
        # "LC_MESSAGES/messages.json.i18t" with no language segment above it.
        with pytest.raises(CliError, match="Could not determine the language"):
            _parse_i18t_path("LC_MESSAGES/messages.json.i18t")

    def test_templates_path_raises(self, template_i18t_file):
        with pytest.raises(CliError, match="templates/ files have no language"):
            _parse_i18t_path(template_i18t_file)
