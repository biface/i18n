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

This module never imports ``i18n_tools.loaders.*`` directly: ``core.py``
is the only module outside ``loaders/`` allowed to do that (DD-28). The
``validate``/``info`` commands go through the ``Book`` model's own
public ``load()`` method instead; ``sync`` goes through
``core.synchronize()``.

Key Responsibilities:
    - Parse a ``.i18t`` file path into (directory, language, domain,
      format), following the DD-12 repository layout
      (``locales/<lang>/LC_MESSAGES/<domain>.<format>.i18t``).
    - ``validate``/``info``: load a single Book and report success or
      a readable error.
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
from typing import NoReturn

from .config import Config
from .core import synchronize
from .models.corpus import Book

# Matches "<domain>.<format>.i18t", e.g. "messages.json.i18t" (DD-34).
_FILENAME_PATTERN = re.compile(r"^(?P<domain>.+)\.(?P<fmt>json|yaml)\.i18t$")


class CliError(Exception):
    """Raised for CLI-level errors (bad path shape, bad arguments)."""


def _parse_i18t_path(path: str) -> tuple[str, str, str, str]:
    """
    Parse a ``.i18t`` file path into its DD-12 layout components.

    Expects ``.../<lang>/LC_MESSAGES/<domain>.<format>.i18t``.

    :param path: Path to a ``.i18t`` file.
    :type path: str
    :return: ``(directory, language, domain, fmt)``.
    :rtype: tuple[str, str, str, str]
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
            f"(expected '<domain>.<json|yaml>.i18t')"
        )

    parent_name = os.path.basename(directory)
    if parent_name != "LC_MESSAGES":
        raise CliError(
            f"'{path}' is not under a 'LC_MESSAGES' directory — cannot "
            f"determine its language (templates/ files have no language "
            f"and are not supported by 'validate'/'info')"
        )

    language = os.path.basename(os.path.dirname(directory))
    if not language:
        raise CliError(f"Could not determine the language for '{path}'")

    return directory, language, match.group("domain"), match.group("fmt")


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
    book = Book(language=language, domain=domain, format=fmt)
    try:
        book.load(directory)
    except (FileNotFoundError, ValueError) as e:
        raise CliError(str(e)) from e
    return book


def cmd_validate(path: str) -> str:
    """
    Validate a ``.i18t`` file: load it and report success.

    :param path: Path to a ``.i18t`` file.
    :type path: str
    :return: A short, human-readable success message.
    :rtype: str
    :raises CliError: If the file cannot be parsed or loaded.
    """
    book = _load_book_from_path(path)
    count = len(book.messages)
    return f"OK: '{path}' is valid ({count} message(s), domain='{book.domain}', language='{book.language}')"


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
        f"Format:       {book.format}",
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


_REPL_COMMANDS = {
    "validate": lambda arg: cmd_validate(arg),
    "info": lambda arg: cmd_info(arg),
    "sync": lambda arg: cmd_sync(arg),
}


def cmd_repl(input_stream=None, output_stream=None) -> None:
    """
    Run a minimal interactive REPL reusing ``validate``/``info``/``sync``.

    Reads lines of the form ``<command> <argument>`` until ``exit``/
    ``quit`` or end of input. Errors are printed but never stop the loop.

    :param input_stream: Line source; defaults to ``sys.stdin``.
    :param output_stream: Output sink; defaults to ``sys.stdout``.
    """
    input_stream = input_stream if input_stream is not None else sys.stdin
    output_stream = output_stream if output_stream is not None else sys.stdout

    print(
        "i18n-tools REPL — commands: validate <path>, info <path>, sync <config>, exit",
        file=output_stream,
    )
    for raw_line in input_stream:
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
            print(f"Unknown command: '{command}'", file=output_stream)
            continue

        try:
            print(handler(argument), file=output_stream)
        except CliError as e:
            print(f"Error: {e}", file=output_stream)


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level ``argparse`` parser and its 4 subcommands."""
    parser = argparse.ArgumentParser(prog="i18n-tools")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate a .i18t file")
    validate_parser.add_argument("path")

    info_parser = subparsers.add_parser("info", help="Display info about a .i18t file")
    info_parser.add_argument("path")

    sync_parser = subparsers.add_parser("sync", help="Synchronize a repository")
    sync_parser.add_argument("config")

    subparsers.add_parser("repl", help="Start an interactive REPL")

    return parser


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
            print(cmd_validate(args.path))
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
