"""
Test module for cli.cmd_validate / cli.cmd_validate_corpus / cli.cmd_info (#39)
"""

import json
from pathlib import Path

import pytest

from i18n_tools.cli import (
    CliError,
    _dispatch_validate,
    cmd_info,
    cmd_sync,
    cmd_validate,
    cmd_validate_corpus,
)
from i18n_tools.models.book import Book
from i18n_tools.models.message import Message


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


def _rewrite(path, change):
    """Apply ``change`` to the JSON content of the file at ``path``."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    change(data)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestCmdValidateFindings:
    def test_warnings_listed_after_success(self, i18t_file):
        _rewrite(
            i18t_file,
            lambda data: data["greet"]["metadata"].update(colour="red"),
        )
        result = cmd_validate(i18t_file)
        first, *lines = result.splitlines()
        assert first.startswith("OK: ")
        assert first.endswith(" — 0 error(s), 1 warning(s), 0 info")
        assert lines == ["  warning  -  greet: unknown metadata key 'colour' ignored"]

    def test_errors_raise_the_report(self, i18t_file):
        _rewrite(i18t_file, lambda data: data.update(broken="not-a-list"))
        with pytest.raises(CliError) as exc_info:
            cmd_validate(i18t_file)
        first, *lines = str(exc_info.value).splitlines()
        assert first.startswith(f"'{i18t_file}' — 1 error(s)")
        assert "  error    -  broken: malformed messages matrix" in lines

    def test_checked_against_the_path_language(self, i18t_file):
        _rewrite(i18t_file, lambda data: data["metadata"].update(language="en-US"))
        with pytest.raises(CliError, match="1 error"):
            cmd_validate(i18t_file)


class TestDispatchValidate:
    def test_path_and_options_exclusive(self):
        with pytest.raises(CliError, match="not both"):
            _dispatch_validate("a.json.i18t", "c.yaml", None, None)

    def test_options_all_required(self):
        with pytest.raises(CliError, match="missing --module, --domain$"):
            _dispatch_validate(None, "c.yaml", None, None)

    def test_nothing_given(self):
        with pytest.raises(CliError, match="missing --config, --module, --domain$"):
            _dispatch_validate(None, None, None, None)

    def test_path_mode(self, i18t_file):
        assert _dispatch_validate(i18t_file, None, None, None).startswith("OK: ")


def _save_complete(repository_root, lang, matrix):
    """Save one complete message "items" in the messages Book of ``lang``."""
    directory = Path(repository_root, "app", "locales", lang, "LC_MESSAGES")
    book = Book(language=lang, domain="messages")
    book.load(str(directory))
    message = Message.from_matrix("items", matrix, metadata={"language": lang})
    message.mark_complete()
    book.messages["items"] = message
    book.save(str(directory))


class TestCmdValidateCorpus:
    def test_sound_corpus(self, corpus_config_file, isolated_config_singleton):
        config_path, _ = corpus_config_file
        _ = cmd_sync(config_path)
        assert (
            cmd_validate_corpus(config_path, "app", "messages")
            == "OK: module 'app', domain 'messages' is valid"
        )

    def test_corpus_errors_raise_the_report(
        self, corpus_config_file, isolated_config_singleton
    ):
        config_path, root = corpus_config_file
        _ = cmd_sync(config_path)
        _save_complete(root, "en", [["{n} item"]])
        _save_complete(root, "fr-FR", [["{count} article"]])
        with pytest.raises(CliError) as exc_info:
            cmd_validate_corpus(config_path, "app", "messages")
        first, *lines = str(exc_info.value).splitlines()
        assert (
            first
            == "module 'app', domain 'messages' — 1 error(s), 0 warning(s), 0 info"
        )
        assert lines == [
            "  error    -  items: tokens of cell (variant 0, segment 0) differ "
            "across languages: en ['n'], fr-FR ['count']"
        ]

    def test_file_findings_carry_their_language(
        self, corpus_config_file, isolated_config_singleton
    ):
        config_path, root = corpus_config_file
        _ = cmd_sync(config_path)
        path = Path(root, "app", "locales", "fr", "LC_MESSAGES", "messages.json.i18t")
        path.unlink()
        with pytest.raises(CliError) as exc_info:
            cmd_validate_corpus(config_path, "app", "messages")
        assert f"  error    fr  root: file not found: {path}" in str(exc_info.value)

    def test_missing_config(self, tmp_path, isolated_config_singleton):
        with pytest.raises(CliError):
            cmd_validate_corpus(str(tmp_path / "none.yaml"), "app", "messages")
