"""
Test module for cli.cmd_repl (#39)
"""

import io

from i18n_tools.cli import cmd_repl


def _run_repl(commands: list[str]) -> str:
    input_stream = io.StringIO("\n".join(commands) + "\n")
    output_stream = io.StringIO()
    cmd_repl(input_stream=input_stream, output_stream=output_stream)
    return output_stream.getvalue()


class TestReplBasics:
    def test_prints_banner(self):
        output = _run_repl(["exit"])
        assert "i18n-tools REPL" in output

    def test_exit_stops_the_loop(self):
        output = _run_repl(["exit", "validate /should/not/run"])
        assert "should/not/run" not in output

    def test_quit_is_also_accepted(self):
        output = _run_repl(["quit"])
        assert "i18n-tools REPL" in output

    def test_blank_lines_are_ignored(self):
        output = _run_repl(["", "  ", "exit"])
        assert "Unknown command" not in output

    def test_unknown_command_reports_error_and_continues(self):
        output = _run_repl(["bogus arg", "exit"])
        assert "Unknown command: 'bogus'" in output

    def test_end_of_input_stops_the_loop_without_exit(self):
        # No "exit" line at all — the generator simply runs dry.
        output = _run_repl(["  "])
        assert "i18n-tools REPL" in output


class TestReplDelegatesToCommands:
    def test_validate_command_via_repl(self, i18t_file):
        output = _run_repl([f"validate {i18t_file}", "exit"])
        assert "OK:" in output

    def test_validate_error_is_reported_without_crashing(self, tmp_path):
        bad_path = str(tmp_path / "messages.txt")
        output = _run_repl([f"validate {bad_path}", "exit"])
        assert "Error:" in output

    def test_info_command_via_repl(self, i18t_file):
        output = _run_repl([f"info {i18t_file}", "exit"])
        assert "Domain:" in output
