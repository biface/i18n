"""
Publish Module
==============

Implements ``publish()`` (DD-27): selects a cell ``(segment, variant)``
from a ``Message``'s matrix, falling back through up to four steps when
a cell is absent (an empty string is the DD-02 semantic marker for "no
content here", not intentional empty content), then substitutes
``{token}`` placeholders.

This module reads the cells of ``Message.matrix`` rather than going
through ``Message.format()``, which selects a single cell and does not
apply this fallback.

Key Responsibilities:
    - Take the segment as given, or resolve it from a count through the
      ``Message``'s ``PluralRule``.
    - Refuse an address outside the matrix (``PluralIndexError``,
      ``VariantIndexError``).
    - Apply the DD-27 four-step column fallback to select a cell.
    - Substitute tokens and surface formatting errors as
      ``FormatterError``.
"""

from __future__ import annotations

from .._cells import resolve_cell
from .._checks import ensure_type, is_type
from ..exceptions import FormatterError, PluralIndexError, VariantIndexError
from ..models import Message


def _ensure_int(value: object, name: str, optional: bool = False) -> None:
    """Raise TypeError unless ``value`` is an int (or None if optional)."""
    if optional and value is None:
        return
    if is_type(value, bool) or not is_type(value, int):
        expected = "an int or None" if optional else "an int"
        raise TypeError(f"publish() {name} must be {expected}, got {type(value)}")


def publish(
    message: Message,
    variant: int = 0,
    segment: int | None = None,
    n: int | None = None,
    **tokens: object,
) -> str:
    """
    Format a message: select the cell ``(segment, variant)``, apply the
    DD-27 four-step column fallback, then substitute the tokens.

    The segment is either given, or resolved from ``n`` by
    ``message.plural_rule`` (DD-40); without both, it is 0 (the
    singular). ``segment`` and ``n`` exclude each other. Ports with sum
    types model this choice as one argument (singular, segment or count).

    :param message: The ``Message`` to format.
    :type message: Message
    :param variant: The declension to use, 0 for the principal.
    :type variant: int
    :param segment: The segment to use, 0 for the singular.
    :type segment: int | None
    :param n: Count resolved to a segment by ``message.plural_rule``.
        Ignored if the message has no plural rule.
    :type n: int | None
    :param tokens: Values substituted into the text via
        ``str.format_map``.
    :return: The formatted message.
    :rtype: str
    :raises TypeError: If ``message`` is not a Message, or ``variant``,
        ``segment`` or ``n`` is not an int.
    :raises ValueError: If both ``segment`` and ``n`` are given.
    :raises PluralIndexError: If the segment, given or resolved, is not a
        row of the matrix.
    :raises VariantIndexError: If ``variant`` is not a column of the
        matrix.
    :raises FormatterError: If a token has no value or the text is
        malformed.
    """
    ensure_type(
        message, Message, f"publish() message must be a Message, got {type(message)}"
    )
    _ensure_int(variant, "variant")
    _ensure_int(segment, "segment", optional=True)
    _ensure_int(n, "n", optional=True)
    if segment is not None and n is not None:
        raise ValueError("publish() takes segment or n, not both")

    row = 0
    if segment is not None:
        row = segment
    elif n is not None and message.plural_rule is not None:
        row = message.plural_rule(n)

    matrix = message.matrix
    if not 0 <= row < len(matrix):
        raise PluralIndexError(message.id, row, len(matrix))
    if not 0 <= variant < len(matrix[0]):
        raise VariantIndexError(message.id, variant, len(matrix[0]))

    text = resolve_cell(matrix, row, variant)
    try:
        return text.format_map(tokens)
    except KeyError as e:
        missing = str(e).strip("'")
        raise FormatterError(
            f"Missing token '{missing}' for message '{message.id}'"
        ) from e
    except Exception as e:
        raise FormatterError(f"Error formatting message '{message.id}': {e}") from e
