"""
CLI Module
==========

**License:**
This file is distributed under the terms of the `CeCILL-C Free Software License Agreement
<https://cecill.info/licences/Licence_CeCILL-C_V1-en.html>`_. By using, modifying, or
redistributing this file, you agree to comply with the terms of this license.

**Author(s):**
This module is authored and maintained as part of the i18n-tools package.

Basic command-line interface for i18n-tools (#39): ``validate``, ``info``,
``sync``, ``repl``. Built on ``argparse`` (stdlib) — the four flat
subcommands don't yet justify a third-party CLI framework.

Outside the models, this module reaches the package through two
entry points only: ``loaders.loader`` (``inspect_book_file()``, the one
loaders module allowed outside ``loaders/``, DD-44) and ``core``
(``inspect_corpus()``, ``synchronize()``). ``info`` and the loading
part of ``validate`` go through the ``Book`` model's own public
``load()`` method.

Key Responsibilities:
    - Parse a ``.i18t`` file path into (directory, language, domain,
      format), following the DD-12 repository layout
      (``locales/<lang>/LC_MESSAGES/<domain>.<format>.i18t``).
    - ``validate <path>``: list the findings of one ``.i18t`` file.
    - ``validate --config C --module M --domain D``: list the findings
      of every configured language of a module/domain, then those of
      the corpus they form.
    - ``info``: load a single Book and report its figures.
    - ``sync``: load an application ``Config`` and synchronize its
      repository's on-disk structure.
    - ``repl``: a minimal interactive loop reusing the same command
      functions, no duplicated logic.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import warnings
from collections.abc import Callable, Iterable
from typing import NoReturn, TextIO, cast

from .__static__ import TranslationFileFormat
from ._finding import Finding
from .config import Config
from .core import inspect_corpus, synchronize
from .exceptions import FormatError, I18nToolsWarning
from .loaders.loader import inspect_book_file
from .locale import normalize_language_tag
from .models.book import Book

# Matches "<domain>.<format>.i18t", e.g. "messages.json.i18t" (DD-34).
_FILENAME_PATTERN = re.compile(r"^(?P<domain>.+)\.(?P<fmt>json|yaml)\.i18t$")


class CliError(Exception):
    """Raised for CLI-level errors (bad path shape, bad arguments)."""


def _parse_i18t_path(path: str) -> tuple[str, str, str, TranslationFileFormat]:
    """
    Parse a ``.i18t`` file path into its DD-12 layout components.

    Expects ``.../<lang>/LC_MESSAGES/<domain>.<format>.i18t``.

    :param path: Path to a ``.i18t`` file.
    :type path: str
    :return: ``(directory, language, domain, fmt)``.
    :rtype: tuple[str, str, str, TranslationFileFormat]
    :raises CliError: If ``path`` does not match the expected filename
        or directory shape (e.g. a ``templates/`` file, which carries
        no language and cannot back a ``Book``).
    """
    directory = os.path.dirname(path) or "."
    filename = os.path.basename(path)

    match = _FILENAME_PATTERN.match(filename)
    if not match:
        raise CliError(
            f"'{filename}' does not look like a translation file "
            + "(expected '<domain>.<json|yaml>.i18t')"
        )

    parent_name = os.path.basename(directory)
    if parent_name != "LC_MESSAGES":
        raise CliError(
            f"'{path}' is not under a 'LC_MESSAGES' directory — cannot "
            + "determine its language (templates/ files have no language "
            + "and are not supported by 'validate'/'info')"
        )

    language = os.path.basename(os.path.dirname(directory))
    if not language:
        raise CliError(f"Could not determine the language for '{path}'")

    # _FILENAME_PATTERN only matches the formats of TranslationFileFormat.
    fmt = cast(TranslationFileFormat, match.group("fmt"))
    return directory, language, match.group("domain"), fmt


def _load_book_from_path(path: str) -> Book:
    """
    Build and load a ``Book`` for the ``.i18t`` file at ``path``.

    :param path: Path to a ``.i18t`` file.
    :type path: str
    :return: The loaded ``Book``.
    :rtype: Book
    :raises CliError: If ``path`` cannot be parsed, or if loading fails
        (file missing, integrity check failed).
    """
    directory, language, domain, fmt = _parse_i18t_path(path)
    book = Book(language=language, domain=domain, file_format=fmt)
    try:
        book.load(directory)
    except (FileNotFoundError, FormatError) as e:
        raise CliError(str(e)) from e
    return book


def _has_error(findings: list[Finding]) -> bool:
    """Whether a finding of ``findings`` is an error."""
    return any(finding.severity == "error" for finding in findings)


def _report(header: str, findings: list[Finding]) -> str:
    """
    Render the findings of a validation under a header line.

    Without findings, the report is the header alone. Otherwise the
    header is followed by a summary of the counts per severity, then by
    one line per finding: severity, language (``-`` when the finding
    has none), where, message.

    :param header: First line of the report.
    :type header: str
    :param findings: The findings, in the order to print them.
    :type findings: list[Finding]
    :return: The report.
    :rtype: str
    """
    if not findings:
        return header
    counts = {
        severity: sum(1 for finding in findings if finding.severity == severity)
        for severity in ("error", "warning", "info")
    }
    summary = (
        f"{counts['error']} error(s), {counts['warning']} warning(s), "
        + f"{counts['info']} info"
    )
    lines = [
        f"  {finding.severity:<7}  {finding.language or '-'}  "
        + f"{finding.where}: {finding.message}"
        for finding in findings
    ]
    return "\n".join([f"{header} — {summary}", *lines])


def cmd_validate(path: str) -> str:
    """
    Validate a ``.i18t`` file: list its findings of every severity.

    The file is checked against the language and domain its path
    carries. Without error, the Book is loaded to report its figures;
    the warnings already listed are not issued again.

    :param path: Path to a ``.i18t`` file.
    :type path: str
    :return: The success line, followed by the warnings and information
        findings if any.
    :rtype: str
    :raises CliError: If the path cannot be parsed, the file does not
        exist, or a finding is an error (the message is the report).
    """
    _, language, domain, _ = _parse_i18t_path(path)
    try:
        findings = inspect_book_file(path, normalize_language_tag(language), domain)
    except FileNotFoundError as e:
        raise CliError(str(e)) from e
    if _has_error(findings):
        raise CliError(_report(f"'{path}'", findings))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", I18nToolsWarning)
        book = _load_book_from_path(path)
    count = len(book.messages)
    success = (
        f"OK: '{path}' is valid ({count} message(s), domain='{book.domain}', "
        + f"language='{book.language}')"
    )
    return _report(success, findings)


def cmd_validate_corpus(config_path: str, module: str, domain: str) -> str:
    """
    Validate every configured language of a module/domain, then the
    corpus they form (``core.inspect_corpus()``).

    :param config_path: Path to the application's configuration file.
    :type config_path: str
    :param module: Module identifier, as declared in the configuration.
    :type module: str
    :param domain: Translation domain name.
    :type domain: str
    :return: The success line, followed by the warnings and information
        findings if any.
    :rtype: str
    :raises CliError: If the configuration cannot be found or loaded, or
        a finding is an error (the message is the report).
    """
    try:
        config = Config(config_path)
        config.load()
    except (FileNotFoundError, IndexError, AttributeError) as e:
        raise CliError(str(e)) from e
    findings = inspect_corpus(config.application, module, domain)
    subject = f"module '{module}', domain '{domain}'"
    if _has_error(findings):
        raise CliError(_report(subject, findings))
    return _report(f"OK: {subject} is valid", findings)


def cmd_info(path: str) -> str:
    """
    Display domain, language, and coverage statistics for a ``.i18t`` file.

    :param path: Path to a ``.i18t`` file.
    :type path: str
    :return: A multi-line, human-readable summary.
    :rtype: str
    :raises CliError: If the file cannot be parsed or loaded.
    """
    book = _load_book_from_path(path)
    stats = book.metadata.get("statistics", {})
    lines = [
        f"Domain:       {book.domain}",
        f"Language:     {book.language}",
        f"Format:       {book.file_format}",
        f"Messages:     {len(book.messages)}",
        f"Total words:  {stats.get('total_words', 0)}",
    ]
    return "\n".join(lines)


def cmd_sync(config_path: str) -> str:
    """
    Synchronize the on-disk repository structure for an application config.

    :param config_path: Path to the application's configuration file.
    :type config_path: str
    :return: A short, human-readable success message.
    :rtype: str
    :raises CliError: If the configuration file cannot be found or loaded.
    """
    try:
        config = Config(config_path)
        config.load()
    except (FileNotFoundError, IndexError, AttributeError) as e:
        raise CliError(str(e)) from e

    synchronize(config.application)
    return f"OK: repository synchronized from '{config_path}'"


_REPL_COMMANDS: dict[str, Callable[[str], str]] = {
    "validate": cmd_validate,
    "info": cmd_info,
    "sync": cmd_sync,
}


def cmd_repl(
    input_stream: Iterable[str] | None = None,
    output_stream: TextIO | None = None,
) -> None:
    """
    Run a minimal interactive REPL reusing ``validate``/``info``/``sync``.

    Reads lines of the form ``<command> <argument>`` until ``exit``/
    ``quit`` or end of input. Errors are printed but never stop the loop.

    :param input_stream: Line source; defaults to ``sys.stdin``.
    :param output_stream: Output sink; defaults to ``sys.stdout``.
    """
    lines: Iterable[str] = sys.stdin if input_stream is None else input_stream
    out: TextIO = sys.stdout if output_stream is None else output_stream

    print(
        "i18n-tools REPL — commands: validate <path>, info <path>, sync <config>, exit",
        file=out,
    )
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if line in ("exit", "quit"):
            break

        parts = line.split(maxsplit=1)
        command = parts[0]
        argument = parts[1] if len(parts) > 1 else ""

        handler = _REPL_COMMANDS.get(command)
        if handler is None:
            print(f"Unknown command: '{command}'", file=out)
            continue

        try:
            print(handler(argument), file=out)
        except CliError as e:
            print(f"Error: {e}", file=out)


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level ``argparse`` parser and its 4 subcommands."""
    parser = argparse.ArgumentParser(prog="i18n-tools")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate a .i18t file, or a module/domain across its languages",
    )
    _ = validate_parser.add_argument("path", nargs="?")
    _ = validate_parser.add_argument("--config", help="application configuration")
    _ = validate_parser.add_argument("--module", help="module to validate")
    _ = validate_parser.add_argument("--domain", help="domain to validate")

    info_parser = subparsers.add_parser("info", help="Display info about a .i18t file")
    _ = info_parser.add_argument("path")

    sync_parser = subparsers.add_parser("sync", help="Synchronize a repository")
    _ = sync_parser.add_argument("config")

    _ = subparsers.add_parser("repl", help="Start an interactive REPL")

    return parser


def _dispatch_validate(
    path: str | None, config: str | None, module: str | None, domain: str | None
) -> str:
    """
    Run ``validate`` in the mode its arguments select: a path, or the
    three options ``--config``, ``--module`` and ``--domain`` together.

    :raises CliError: If both modes or neither are given, or an option of
        the corpus mode is missing.
    """
    options = {"--config": config, "--module": module, "--domain": domain}
    given = [name for name, value in options.items() if value is not None]
    if path is not None:
        if given:
            raise CliError(
                "validate takes a path or --config/--module/--domain, not both"
            )
        return cmd_validate(path)
    if config is None or module is None or domain is None:
        missing = [name for name, value in options.items() if value is None]
        raise CliError(
            "validate needs a path, or --config, --module and --domain; missing "
            + ", ".join(missing)
        )
    return cmd_validate_corpus(config, module, domain)


def main(argv: list[str] | None = None) -> NoReturn:
    """
    CLI entry point (``[project.scripts]``).

    :param argv: Argument list, defaults to ``sys.argv[1:]``.
    :type argv: list[str] | None
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "validate":
            print(_dispatch_validate(args.path, args.config, args.module, args.domain))
        elif args.command == "info":
            print(cmd_info(args.path))
        elif args.command == "sync":
            print(cmd_sync(args.config))
        elif args.command == "repl":
            cmd_repl()
    except CliError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
