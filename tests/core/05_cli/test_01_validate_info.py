"""
Test module for cli.cmd_validate / cli.cmd_info (#39)
"""

import pytest

from i18n_tools.cli import CliError, cmd_info, cmd_validate


class TestCmdValidate:
    def test_valid_file_reports_success(self, i18t_file):
        result = cmd_validate(i18t_file)
        assert result.startswith("OK:")
        assert "1 message(s)" in result
        assert "domain='messages'" in result
        assert "language='fr-FR'" in result

    def test_missing_file_raises_cli_error(self, tmp_path):
        path = tmp_path / "fr-FR" / "LC_MESSAGES" / "messages.json.i18t"
        with pytest.raises(CliError):
            cmd_validate(str(path))

    def test_bad_path_shape_raises_cli_error(self, tmp_path):
        path = tmp_path / "messages.txt"
        with pytest.raises(CliError, match="does not look like a translation file"):
            cmd_validate(str(path))


class TestCmdInfo:
    def test_reports_domain_language_format_and_counts(self, i18t_file):
        result = cmd_info(i18t_file)
        assert "Domain:       messages" in result
        assert "Language:     fr-FR" in result
        assert "Format:       json" in result
        assert "Messages:     1" in result
        assert "Total words:" in result

    def test_missing_file_raises_cli_error(self, tmp_path):
        path = tmp_path / "fr-FR" / "LC_MESSAGES" / "messages.json.i18t"
        with pytest.raises(CliError):
            cmd_info(str(path))
