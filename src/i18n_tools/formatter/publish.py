"""
Publish Module
==============

Implements ``publish()`` (DD-27): selects a cell from a ``Message``'s
plural/alternative matrix, falling back through up to four steps when a
cell is absent (an empty string is the DD-02 semantic marker for "no
content here", not intentional empty content), then substitutes
``{variable}`` placeholders.

This module reads ``Message``'s raw attributes (``default``,
``options``, ``default_plurals``, ``options_plurals``) directly rather
than going through ``Message.format()``: the latter implements a
different, narrower fallback and is left untouched (DD-27) as the
existing, tested, single-cell selection API.

Key Responsibilities:
    - Resolve a plural row index automatically from a ``PluralRule``,
      when the ``Message`` has one and a count is given.
    - Apply the DD-27 four-step column fallback to select a cell.
    - Substitute variables and surface formatting errors as
      ``FormatterError``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..exceptions import FormatterError, PluralIndexError

if TYPE_CHECKING:
    from ..models import Message


def _get_cell(message: "Message", plural_index: int, alternative: int) -> str:
    """
    Raw accessor for ``messages[plural_index][alternative]``.

    :return: The cell's text, or ``""`` if absent — the DD-02 semantic
        marker for "no content here".
    :rtype: str
    """
    if plural_index == 0:
        if alternative == 0:
            return message.default
        return message.options.get(alternative, "")

    if alternative == 0:
        return message.default_plurals.get(plural_index, "")

    return message.options_plurals.get(alternative, {}).get(plural_index, "")


def _resolve_cell(message: "Message", plural_index: int, alternative: int) -> str:
    """
    Apply the DD-27 four-step column fallback:

        1. ``messages[plural_index][alternative]``
        2. -> ``messages[plural_index][0]``
        3. -> ``messages[0][alternative]``
        4. -> ``messages[0][0]`` (guaranteed non-empty by convention)
    """
    text = _get_cell(message, plural_index, alternative)
    if text:
        return text

    if plural_index != 0:
        text = _get_cell(message, plural_index, 0)
        if text:
            return text

    if alternative != 0:
        text = _get_cell(message, 0, alternative)
        if text:
            return text

    return message.default


def _plural_row_exists(message: "Message", plural_index: int) -> bool:
    """
    Whether ``plural_index`` is a row that exists on ``message``.

    Row 0 (singular) always exists. Row existence for plural rows is
    determined from ``default_plurals``: per DD-02, all columns of a
    given entry share the same row set, so ``default_plurals`` alone
    defines which plural rows the entry has.
    """
    return plural_index == 0 or plural_index in message.default_plurals


def publish(message: "Message", alternative: int = 0, n: int | None = None, **kwargs) -> str:
    """
    Format a message: resolve the cell to use (DD-27 four-step column
    fallback, with automatic plural-row resolution via DD-40's
    ``PluralRule`` when applicable), then substitute variables.

    :param message: The ``Message`` to format.
    :type message: Message
    :param alternative: The alternative (column) index to use. Defaults
        to 0 (the main text).
    :type alternative: int
    :param n: Count driving automatic plural-row resolution via
        ``message.plural_rule``. Ignored if ``message.plural_rule`` is
        ``None``.
    :type n: int | None
    :param kwargs: Variables substituted into the resolved text via
        ``str.format_map``.
    :return: The formatted message.
    :rtype: str
    :raises PluralIndexError: If ``message.plural_rule`` resolves a
        plural row index that does not exist on ``message``.
    :raises FormatterError: If variable substitution fails (a required
        variable is missing, or the resolved text is malformed).
    """
    plural_index = 0
    if message.plural_rule is not None and n is not None:
        plural_index = message.plural_rule(n)
        if not _plural_row_exists(message, plural_index):
            raise PluralIndexError(
                f"PluralRule resolved plural row {plural_index} for n={n}, "
                f"which does not exist on message '{message.id}'"
            )

    text = _resolve_cell(message, plural_index, alternative)

    try:
        return text.format_map(kwargs)
    except KeyError as e:
        missing_var = str(e).strip("'")
        raise FormatterError(
            f"Missing variable '{missing_var}' for message '{message.id}'"
        ) from e
    except Exception as e:
        raise FormatterError(
            f"Error formatting message '{message.id}': {e}"
        ) from e
