"""
Test module for cli.build_parser / cli.main (#39)
"""

from unittest import mock

import pytest

from i18n_tools.cli import build_parser, main


class TestBuildParser:
    def test_validate_subcommand(self):
        args = build_parser().parse_args(["validate", "some/path.json.i18t"])
        assert args.command == "validate"
        assert args.path == "some/path.json.i18t"

    def test_info_subcommand(self):
        args = build_parser().parse_args(["info", "some/path.json.i18t"])
        assert args.command == "info"
        assert args.path == "some/path.json.i18t"

    def test_sync_subcommand(self):
        args = build_parser().parse_args(["sync", "config.yaml"])
        assert args.command == "sync"
        assert args.config == "config.yaml"

    def test_repl_subcommand(self):
        args = build_parser().parse_args(["repl"])
        assert args.command == "repl"

    def test_no_subcommand_is_an_error(self):
        with pytest.raises(SystemExit):
            build_parser().parse_args([])

    def test_unknown_subcommand_is_an_error(self):
        with pytest.raises(SystemExit):
            build_parser().parse_args(["bogus"])


class TestMainExitCodes:
    def test_validate_success_exits_0(self, i18t_file, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main(["validate", i18t_file])
        assert exc_info.value.code == 0
        assert "OK:" in capsys.readouterr().out

    def test_validate_failure_exits_1(self, tmp_path, capsys):
        bad_path = str(tmp_path / "messages.txt")
        with pytest.raises(SystemExit) as exc_info:
            main(["validate", bad_path])
        assert exc_info.value.code == 1
        assert "Error:" in capsys.readouterr().err

    def test_info_success_exits_0(self, i18t_file, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main(["info", i18t_file])
        assert exc_info.value.code == 0
        assert "Domain:" in capsys.readouterr().out

    def test_sync_dispatch_exits_0(self, sync_config_file, isolated_config_singleton):
        config_path, _ = sync_config_file
        with pytest.raises(SystemExit) as exc_info:
            main(["sync", config_path])
        assert exc_info.value.code == 0

    def test_repl_dispatch_calls_cmd_repl(self):
        with mock.patch("i18n_tools.cli.cmd_repl") as mocked_repl:
            with pytest.raises(SystemExit) as exc_info:
                main(["repl"])
        mocked_repl.assert_called_once_with()
        assert exc_info.value.code == 0
