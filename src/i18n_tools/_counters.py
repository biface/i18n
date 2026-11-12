"""
Content counters of a message: number of declensions, number of
segments and fill mask.

One definition shared by ``Message``, the converter and the loaders. The
module imports nothing from the package except the runtime guards and the
JSON value aliases, so that every layer may use it.

Private module: ``ContentCounters`` is exported by ``i18n_tools.models``
and the package.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast

from i18n_tools._checks import ensure_type, is_type
from i18n_tools._json import JSONInput


def _ensure_count(value: int, name: str) -> None:
    """Check a counter: an int (not a bool) of at least 1."""
    if is_type(value, bool) or not is_type(value, int):
        raise TypeError(f"ContentCounters {name} must be an int, got {type(value)}")
    if value < 1:
        raise ValueError(f"ContentCounters {name} must be >= 1, got {value}")


@dataclass(frozen=True, slots=True)
class ContentCounters:
    """
    Structure and fill state of the content of a message.

    :param declensions: Number of declensions, principal included (the
        length of the singular row of the matrix).
    :type declensions: int
    :param segments: Number of rows of the matrix: the largest segment
        count over the declensions.
    :type segments: int
    :param filled: Fill mask in matrix orientation: ``filled[segment][variant]``
        is True when that text is not empty. A cell that only exists
        through padding is False.
    :type filled: tuple[tuple[bool, ...], ...]
    :raises TypeError: If a field has the wrong type.
    :raises ValueError: If a counter is below 1, or the mask is not a
        ``segments`` x ``declensions`` rectangle.
    """

    declensions: int
    segments: int
    filled: tuple[tuple[bool, ...], ...]

    def __post_init__(self) -> None:
        _ensure_count(self.declensions, "declensions")
        _ensure_count(self.segments, "segments")
        ensure_type(
            self.filled,
            tuple,
            f"ContentCounters filled must be a tuple, got {type(self.filled)}",
        )
        if len(self.filled) != self.segments:
            raise ValueError(
                f"ContentCounters filled has {len(self.filled)} rows, "
                + f"expected {self.segments}"
            )
        for row in self.filled:
            ensure_type(
                row,
                tuple,
                f"ContentCounters filled row must be a tuple, got {type(row)}",
            )
            if len(row) != self.declensions:
                raise ValueError(
                    f"ContentCounters filled row has {len(row)} cells, "
                    + f"expected {self.declensions}"
                )
            for cell in row:
                ensure_type(
                    cell,
                    bool,
                    f"ContentCounters filled cell must be a bool, got {type(cell)}",
                )


def count_content(matrix: list[list[str]]) -> ContentCounters:
    """
    Compute the counters of a message matrix.

    :param matrix: A non-empty rectangle of texts, one row per segment
        and one column per declension, as ``Message.matrix`` returns it.
    :type matrix: list[list[str]]
    :return: The counters.
    :rtype: ContentCounters
    :raises ValueError: If ``matrix`` is empty or its first row is empty.
    """
    if len(matrix) == 0 or len(matrix[0]) == 0:
        raise ValueError("A message matrix has at least one cell")
    return ContentCounters(
        declensions=len(matrix[0]),
        segments=len(matrix),
        filled=tuple(tuple(text != "" for text in row) for row in matrix),
    )


def counters_to_entry(counters: ContentCounters) -> dict[str, JSONInput]:
    """
    The counters as ``.i18t`` entry metadata.

    :param counters: The counters to write.
    :type counters: ContentCounters
    :return: ``singular_count``, ``segment_count`` and ``fill_mask`` (a
        list of lists of booleans, matrix orientation).
    :rtype: dict[str, JSONInput]
    """
    return {
        "singular_count": counters.declensions,
        "segment_count": counters.segments,
        "fill_mask": [list(row) for row in counters.filled],
    }


def counters_from_entry(metadata: Mapping[str, object]) -> ContentCounters | None:
    """
    Read the counters of ``.i18t`` entry metadata.

    :param metadata: The entry metadata.
    :type metadata: Mapping[str, object]
    :return: The counters, or None if one of the keys is missing or a
        value is malformed.
    :rtype: ContentCounters | None
    """
    declensions = metadata.get("singular_count")
    segments = metadata.get("segment_count")
    mask = metadata.get("fill_mask")
    if (
        not isinstance(declensions, int)
        or not isinstance(segments, int)
        or not isinstance(mask, list)
    ):
        return None
    rows: list[tuple[bool, ...]] = []
    for row in cast(list[object], mask):
        if not isinstance(row, list):
            return None
        cells = cast(list[object], row)
        if not all(isinstance(cell, bool) for cell in cells):
            return None
        rows.append(tuple(cell is True for cell in cells))
    try:
        return ContentCounters(declensions, segments, tuple(rows))
    except (TypeError, ValueError):
        return None


def describe_differences(
    recorded: ContentCounters, observed: ContentCounters
) -> list[str]:
    """
    List how the observed counters differ from the recorded ones.

    Cells are named ``(variant, segment)``, the addressing of a message;
    a cell outside one of the masks counts as not filled there.

    :param recorded: The counters taken at the last validation point.
    :type recorded: ContentCounters
    :param observed: The counters computed from the current content.
    :type observed: ContentCounters
    :return: One line per difference; empty if the counters are equal.
    :rtype: list[str]
    """
    lines: list[str] = []
    if recorded.declensions != observed.declensions:
        lines.append(
            f"declensions: recorded {recorded.declensions}, "
            + f"observed {observed.declensions}"
        )
    if recorded.segments != observed.segments:
        lines.append(
            f"segments: recorded {recorded.segments}, observed {observed.segments}"
        )
    for segment in range(max(recorded.segments, observed.segments)):
        for variant in range(max(recorded.declensions, observed.declensions)):
            was = _cell(recorded, segment, variant)
            now = _cell(observed, segment, variant)
            if was and not now:
                lines.append(f"text ({variant}, {segment}) lost")
            elif now and not was:
                lines.append(f"text ({variant}, {segment}) added")
    return lines


def _cell(counters: ContentCounters, segment: int, variant: int) -> bool:
    """Fill state of a cell; False outside the mask."""
    if segment < counters.segments and variant < counters.declensions:
        return counters.filled[segment][variant]
    return False
