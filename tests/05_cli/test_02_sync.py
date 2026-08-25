"""
Test module for cli.cmd_sync (#39)

cli.cmd_sync() constructs a Config, which uses patterns.Singleton: only
one instance exists per Python process (see tests/conftest.py's
"TEST EXECUTION ORDER" note — 01_loader initializes it, 09_config
inherits it). Calling Config(config_path) in-process here would return
whatever Config instance already exists elsewhere in the same pytest
session, silently ignoring config_path. To get a real, isolated
end-to-end check, these tests invoke the CLI in a fresh subprocess
instead of calling cmd_sync() directly.
"""

import os
import subprocess
import sys

import pytest


def _run_cli(*args):
    env = dict(os.environ)
    src_path = os.path.join(os.path.dirname(__file__), "..", "..", "src")
    env["PYTHONPATH"] = os.pathsep.join(
        filter(None, [os.path.abspath(src_path), env.get("PYTHONPATH")])
    )
    return subprocess.run(
        [sys.executable, "-m", "i18n_tools.cli", *args],
        capture_output=True,
        text=True,
        env=env,
    )


class TestCmdSync:
    def test_synchronizes_repository_from_config(self, sync_config_file):
        config_path, repository_root = sync_config_file
        result = _run_cli("sync", config_path)

        assert result.returncode == 0
        assert "OK: repository synchronized" in result.stdout
        assert os.path.isdir(os.path.join(repository_root, "app", "locales", "en"))

    def test_missing_config_file_exits_non_zero(self, tmp_path):
        missing = tmp_path / "does-not-exist.yaml"
        result = _run_cli("sync", str(missing))

        assert result.returncode == 1
        assert "Error:" in result.stderr

    def test_creates_expected_domain_files(self, sync_config_file):
        config_path, repository_root = sync_config_file
        _run_cli("sync", config_path)

        messages_dir = os.path.join(
            repository_root, "app", "locales", "en", "LC_MESSAGES"
        )
        assert os.path.isfile(os.path.join(messages_dir, "messages.json.i18t"))


class TestCmdSyncInProcess:
    """
    Same behaviour as TestCmdSync, exercised in-process (with the Config
    singleton reset and restored) so this module's own coverage report
    credits cmd_sync()'s body — subprocess calls execute it for real but
    are invisible to coverage instrumentation running in the parent.
    """

    def test_returns_success_message(self, sync_config_file, isolated_config_singleton):
        from i18n_tools.cli import cmd_sync

        config_path, repository_root = sync_config_file
        result = cmd_sync(config_path)

        assert result == f"OK: repository synchronized from '{config_path}'"
        assert os.path.isdir(os.path.join(repository_root, "app", "locales", "en"))

    def test_missing_config_raises_cli_error(self, tmp_path, isolated_config_singleton):
        from i18n_tools.cli import CliError, cmd_sync

        missing = tmp_path / "does-not-exist.yaml"
        with pytest.raises(CliError):
            cmd_sync(str(missing))
