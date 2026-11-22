"""
Record of a message: its ``count`` and ``fill_mask``, in format 1.0.0.

The record is the shape and the fill state of the content of a message,
taken at a validation point and stored in the entry metadata. Comparing it
with the record observed on the current content shows the texts lost or
added since. One definition is shared by ``Message``, the converter and
the loaders. The module imports nothing from the package except the
runtime guards and the JSON value aliases, so that every layer may use it.

The functions work on plain mappings, as read from a file;
:class:`ContentCounters` is the view a ``Message`` gives on its record.

Private module: ``ContentCounters`` is exported by ``i18n_tools.models``
and the package.
"""

from __future__ import annotations

import json
import string
from collections.abc import Iterator, Mapping, Sequence
from typing import NamedTuple, cast

from ndict_tools import StrictNestedDictionary

from i18n_tools._checks import is_type
from i18n_tools._json import JSONValue

_FORMATTER = string.Formatter()
_CONVERSIONS = frozenset({"r", "s", "a"})

_COUNT_KEYS = ("declensions", "alternatives", "singulars", "plurals")
_RECORD_KEYS = frozenset({"count", "fill_mask"})
_COUNT_ALL_KEYS = frozenset({*_COUNT_KEYS, "segments", "tokens"})
_SHAPE_KEYS = frozenset({"principal", "alternatives"})


def key_path(*keys: str | int) -> str:
    """
    Write a path as the list of its keys, as ndict-tools reaches a value.

    :param keys: The keys, from the base of the path.
    :type keys: str | int
    :return: For instance ``["metadata", "count", "segments"]``.
    :rtype: str
    """
    return json.dumps(list(keys), ensure_ascii=False)


def is_filled(text: str) -> bool:
    """
    Tell whether a text is filled: neither ``""`` nor whitespace only.

    :param text: The text.
    :type text: str
    :return: True if the text holds a character other than whitespace.
    :rtype: bool
    """
    return text.strip() != ""


class Fields(NamedTuple):
    """
    The replacement fields of a text, as :func:`read_fields` reads them.

    ``names`` are the token names, distinct and sorted; the three other
    lists hold fields as written, in order of appearance: the positional
    fields (``""`` for ``{}``), the tokens with attribute or index access
    (``user.name``, ``items[0]``), and the fields nested in a format
    specification (``w`` in ``{n:{w}}``).
    """

    names: list[str]
    positional: list[str]
    accessed: list[str]
    nested: list[str]


def _parse_fields(text: str, nested: bool = False) -> Iterator[tuple[str, bool]]:
    """
    Yield the replacement fields of a text, in order of appearance.

    The fields of a format specification are yielded after the field
    that holds them (``{n:{w}}`` gives ``n``, then ``w``), as
    ``str.format`` replaces them. A conversion other than ``!r``, ``!s``
    or ``!a``, and a field nested in a nested field, are refused as
    ``str.format`` refuses them.

    :param text: The text, or the format specification of a field.
    :type text: str
    :param nested: True when ``text`` is a format specification.
    :type nested: bool
    :return: Each field name as written, with True when the field is
        nested in a format specification.
    :rtype: Iterator[tuple[str, bool]]
    :raises ValueError: If the text is not a valid format string.
    """
    for _, field, specification, conversion in _FORMATTER.parse(text):
        if field is None:
            continue
        if conversion is not None and conversion not in _CONVERSIONS:
            raise ValueError(
                f"unknown conversion '!{conversion}' in the field '{field}'"
            )
        yield field, nested
        if not specification:
            continue
        inner = _parse_fields(specification, nested=True)
        if not nested:
            yield from inner
            continue
        found = next(inner, None)
        if found is not None:
            raise ValueError(
                f"the field '{found[0]}' is nested in a field that is itself nested"
            )


def read_fields(text: str) -> Fields:
    """
    Read the replacement fields of a text, as ``str.format`` reads them.

    A token is a field with a name; its name is the field name as written,
    without conversion or format specification. A positional field
    (``{}``, ``{0}``) is not a token. The fields of a format specification
    (``{n:{w}}``) are read as well.

    :param text: The text.
    :type text: str
    :return: The token names, then the positional, accessed and nested
        fields (see :class:`Fields`).
    :rtype: Fields
    :raises ValueError: If the text is not a valid format string.
    """
    names: set[str] = set()
    fields = Fields([], [], [], [])
    for field, nested in _parse_fields(text):
        head = field.split(".", 1)[0].split("[", 1)[0]
        if head == "" or head.isdigit():
            fields.positional.append(field)
        else:
            names.add(field)
            if head != field:
                fields.accessed.append(field)
        if nested:
            fields.nested.append(field)
    fields.names.extend(sorted(names))
    return fields


def check_format_string(text: str) -> str | None:
    """
    Tell why a text is not a valid format string, if it is not.

    :param text: The text.
    :type text: str
    :return: The error of ``str.format`` parsing, or None if the text is
        valid.
    :rtype: str | None
    """
    try:
        _ = read_fields(text)
    except ValueError as e:
        return str(e)
    return None


def _tokens(text: str) -> list[str]:
    """Token names of a text; none for a text that does not parse."""
    try:
        return read_fields(text).names
    except ValueError:
        return []


def observe(
    principal: Sequence[str], alternatives: Sequence[Sequence[str]]
) -> dict[str, JSONValue]:
    """
    Compute the record of a content, as a writer writes it.

    :param principal: The texts of the principal.
    :type principal: Sequence[str]
    :param alternatives: The texts of each alternative.
    :type alternatives: Sequence[Sequence[str]]
    :return: ``{"count": {...}, "fill_mask": {...}}``.
    :rtype: dict[str, JSONValue]
    """
    lengths = [len(alternative) for alternative in alternatives]
    count: dict[str, JSONValue] = {
        "declensions": 1 + len(alternatives),
        "alternatives": len(alternatives),
        "singulars": 1 + len(alternatives),
        "plurals": (len(principal) - 1) + sum(length - 1 for length in lengths),
        "segments": {"principal": len(principal), "alternatives": list(lengths)},
        "tokens": {
            "principal": [list(_tokens(text)) for text in principal],
            "alternatives": [
                [list(_tokens(text)) for text in alternative]
                for alternative in alternatives
            ],
        },
    }
    fill_mask: dict[str, JSONValue] = {
        "principal": [is_filled(text) for text in principal],
        "alternatives": [
            [is_filled(text) for text in alternative] for alternative in alternatives
        ],
    }
    return {"count": count, "fill_mask": fill_mask}


def entry_statistics(
    principal: Sequence[str], alternatives: Sequence[Sequence[str]]
) -> dict[str, JSONValue]:
    """
    Compute the ``statistics`` of an entry from its texts.

    :param principal: The texts of the principal.
    :type principal: Sequence[str]
    :param alternatives: The texts of each alternative.
    :type alternatives: Sequence[Sequence[str]]
    :return: ``words`` (``len(text.split())``) and ``characters``
        (``len(text)``), over every text, tokens counted as written.
    :rtype: dict[str, JSONValue]
    """
    texts = [
        *principal,
        *(text for alternative in alternatives for text in alternative),
    ]
    return {
        "words": sum(len(text.split()) for text in texts),
        "characters": sum(len(text) for text in texts),
    }


def _is_int(value: object, minimum: int) -> bool:
    """Tell whether ``value`` is an int (not a bool) of at least ``minimum``."""
    return (
        is_type(value, int) and not is_type(value, bool) and cast(int, value) >= minimum
    )


def _unknown(
    node: Mapping[str, object], known: frozenset[str], *path: str
) -> list[str]:
    """One defect per key of ``node`` that is not in ``known``."""
    return [
        f"unknown key '{key}' in {key_path(*path)}" for key in node if key not in known
    ]


def _check_shape(
    node: object,
    lengths: tuple[int, list[int]] | None,
    leaf: str,
    check: type,
    *path: str,
) -> list[str]:
    """
    Check that ``node`` has the shape of the content given by ``lengths``.

    ``leaf`` names the type of a value at an address, ``check`` is it.
    """
    if not is_type(node, Mapping):
        return [f"{key_path(*path)} is not a mapping"]
    mapping = cast("Mapping[str, object]", node)
    defects = _unknown(mapping, _SHAPE_KEYS, *path)
    for key in ("principal", "alternatives"):
        if key not in mapping:
            defects.append(f"{key_path(*path, key)} is missing")
    if defects:
        return defects
    principal = mapping["principal"]
    alternatives = mapping["alternatives"]
    if not is_type(principal, list) or not all(
        is_type(value, check) for value in cast("list[object]", principal)
    ):
        defects.append(f"{key_path(*path, 'principal')} is not a list of {leaf}")
    if not is_type(alternatives, list) or not all(
        is_type(alternative, list)
        and all(is_type(value, check) for value in cast("list[object]", alternative))
        for alternative in cast("list[object]", alternatives)
    ):
        defects.append(
            f"{key_path(*path, 'alternatives')} is not a list of lists of {leaf}"
        )
    if defects or lengths is None:
        return defects
    expected_principal, expected_alternatives = lengths
    shape = (
        len(cast("list[object]", principal)),
        [
            len(cast("list[object]", item))
            for item in cast("list[object]", alternatives)
        ],
    )
    if shape != (expected_principal, expected_alternatives):
        defects.append(
            f"{key_path(*path)} does not have the shape given by "
            + key_path("metadata", "count", "segments")
        )
    return defects


def _is_token_list(value: object) -> bool:
    if not is_type(value, list):
        return False
    names = cast("list[object]", value)
    if not all(is_type(name, str) for name in names):
        return False
    return names == sorted(set(cast("list[str]", names)))


def record_defects(record: Mapping[str, object]) -> list[str]:
    """
    List why a record is not well formed.

    The record is a mapping with ``count`` and ``fill_mask``. Every
    defect is described with its path from the entry, in the order of the
    conditions of the format: types and keys, then the five conditions of
    a well-formed record.

    :param record: ``{"count": ..., "fill_mask": ...}``, as read.
    :type record: Mapping[str, object]
    :return: The defects; empty if the record is well formed.
    :rtype: list[str]
    """
    base = ("metadata", "count")
    count = record.get("count")
    if not is_type(count, Mapping):
        return [f"{key_path(*base)} is not a mapping"]
    node = cast("Mapping[str, object]", count)
    defects = _unknown(node, _COUNT_ALL_KEYS, *base)
    for key in (*_COUNT_KEYS, "segments", "tokens"):
        if key not in node:
            defects.append(f"{key_path(*base, key)} is missing")
    for key, minimum in zip(_COUNT_KEYS, (1, 0, 1, 0)):
        if key in node and not _is_int(node[key], minimum):
            defects.append(f"{key_path(*base, key)} is not an integer >= {minimum}")
    segments = node.get("segments")
    lengths: tuple[int, list[int]] | None = None
    if "segments" in node:
        if not is_type(segments, Mapping):
            defects.append(f"{key_path(*base, 'segments')} is not a mapping")
        else:
            seg = cast("Mapping[str, object]", segments)
            seg_defects = _unknown(seg, _SHAPE_KEYS, *base, "segments")
            principal = seg.get("principal")
            alternatives = seg.get("alternatives")
            if not _is_int(principal, 1):
                seg_defects.append(
                    f"{key_path(*base, 'segments', 'principal')} is not an integer >= 1"
                )
            if not is_type(alternatives, list) or not all(
                _is_int(value, 1) for value in cast("list[object]", alternatives)
            ):
                seg_defects.append(
                    f"{key_path(*base, 'segments', 'alternatives')} is not a list "
                    + "of integers >= 1"
                )
            defects.extend(seg_defects)
            if not seg_defects:
                lengths = (
                    cast(int, principal),
                    list(cast("list[int]", alternatives)),
                )
    if "tokens" in node:
        tokens = node["tokens"]
        if not is_type(tokens, Mapping):
            defects.append(f"{key_path(*base, 'tokens')} is not a mapping")
        else:
            defects.extend(_check_tokens(cast("Mapping[str, object]", tokens), lengths))
    if "fill_mask" not in record:
        defects.append(f"{key_path('metadata', 'fill_mask')} is missing")
    else:
        defects.extend(
            _check_shape(
                record["fill_mask"], lengths, "booleans", bool, "metadata", "fill_mask"
            )
        )
    if defects or lengths is None:
        return defects
    return _well_formed(node, lengths)


def _check_tokens(
    tokens: Mapping[str, object], lengths: tuple[int, list[int]] | None
) -> list[str]:
    """Check ``count.tokens``: the shape of the content, sorted distinct names."""
    path = ("metadata", "count", "tokens")
    defects = _unknown(tokens, _SHAPE_KEYS, *path)
    for key in ("principal", "alternatives"):
        if key not in tokens:
            defects.append(f"{key_path(*path, key)} is missing")
    if defects:
        return defects
    principal = tokens["principal"]
    alternatives = tokens["alternatives"]
    if not is_type(principal, list):
        return [f"{key_path(*path, 'principal')} is not a list"]
    if not is_type(alternatives, list) or not all(
        is_type(item, list) for item in cast("list[object]", alternatives)
    ):
        return [f"{key_path(*path, 'alternatives')} is not a list of lists"]
    for index, names in enumerate(cast("list[object]", principal)):
        if not _is_token_list(names):
            defects.append(
                f"{key_path(*path, 'principal', index)} is not a sorted list of "
                + "distinct names"
            )
    for k, alternative in enumerate(cast("list[list[object]]", alternatives)):
        for index, names in enumerate(alternative):
            if not _is_token_list(names):
                defects.append(
                    f"{key_path(*path, 'alternatives', k, index)} is not a sorted "
                    + "list of distinct names"
                )
    if defects or lengths is None:
        return defects
    shape = (
        len(cast("list[object]", principal)),
        [len(item) for item in cast("list[list[object]]", alternatives)],
    )
    if shape != lengths:
        defects.append(
            f"{key_path(*path)} does not have the shape given by "
            + key_path("metadata", "count", "segments")
        )
    return defects


def _well_formed(
    count: Mapping[str, object], lengths: tuple[int, list[int]]
) -> list[str]:
    """The conditions 1 to 4 of a well-formed record, on checked types."""
    base = ("metadata", "count")
    declensions = cast(int, count["declensions"])
    alternatives = cast(int, count["alternatives"])
    singulars = cast(int, count["singulars"])
    plurals = cast(int, count["plurals"])
    principal, per_alternative = lengths
    defects: list[str] = []
    if not singulars == declensions == 1 + alternatives:
        defects.append(
            f"{key_path(*base, 'singulars')} is {singulars}, "
            + f"{key_path(*base, 'declensions')} is {declensions}, "
            + f"1 + {key_path(*base, 'alternatives')} is {1 + alternatives}"
        )
    if len(per_alternative) != alternatives:
        defects.append(
            f"{key_path(*base, 'segments', 'alternatives')} has "
            + f"{len(per_alternative)} values, {key_path(*base, 'alternatives')} "
            + f"is {alternatives}"
        )
    for index, length in enumerate(per_alternative):
        if length != principal:
            defects.append(
                f"{key_path(*base, 'segments', 'alternatives', index)} is {length}, "
                + f"{key_path(*base, 'segments', 'principal')} is {principal}"
            )
    expected = (principal - 1) + sum(per_alternative) - len(per_alternative)
    if plurals != expected:
        defects.append(
            f"{key_path(*base, 'plurals')} is {plurals}, "
            + f"{key_path(*base, 'segments')} give {expected}"
        )
    return defects


def _declension_lists(node: Mapping[str, object]) -> list[list[object]]:
    """``[principal, *alternatives]`` of a node in the shape of the content."""
    principal = cast("list[object]", node["principal"])
    alternatives = cast("list[list[object]]", node["alternatives"])
    return [list(principal), *(list(item) for item in alternatives)]


def record_differences(
    recorded: Mapping[str, object], observed: Mapping[str, object]
) -> list[str]:
    """
    Describe how a well-formed record differs from the observed one.

    The number of declensions is compared first; if it differs, nothing
    else is. Then, declension by declension, the number of segments; at
    equal number, each text lost or added (from the fill masks), then the
    token names of each text.

    :param recorded: The record of the entry, well formed.
    :type recorded: Mapping[str, object]
    :param observed: The record computed from the content.
    :type observed: Mapping[str, object]
    :return: One line per difference; empty if the records are equal.
    :rtype: list[str]
    """
    rec_count = cast("Mapping[str, object]", recorded["count"])
    obs_count = cast("Mapping[str, object]", observed["count"])
    if rec_count["declensions"] != obs_count["declensions"]:
        return [
            f"declensions: recorded {rec_count['declensions']}, "
            + f"observed {obs_count['declensions']}"
        ]
    rec_masks = _declension_lists(cast("Mapping[str, object]", recorded["fill_mask"]))
    obs_masks = _declension_lists(cast("Mapping[str, object]", observed["fill_mask"]))
    rec_tokens = _declension_lists(cast("Mapping[str, object]", rec_count["tokens"]))
    obs_tokens = _declension_lists(cast("Mapping[str, object]", obs_count["tokens"]))
    lines: list[str] = []
    for declension, (rec_mask, obs_mask) in enumerate(zip(rec_masks, obs_masks)):
        if len(rec_mask) != len(obs_mask):
            lines.append(
                f"segments of declension {declension}: recorded {len(rec_mask)}, "
                + f"observed {len(obs_mask)}"
            )
            continue
        for segment, (was, now) in enumerate(zip(rec_mask, obs_mask)):
            if was and not now:
                lines.append(f"text ({declension}, {segment}) lost")
            elif now and not was:
                lines.append(f"text ({declension}, {segment}) added")
        for segment, (was, now) in enumerate(
            zip(rec_tokens[declension], obs_tokens[declension])
        ):
            if was != now:
                lines.append(
                    f"tokens of text ({declension}, {segment}): "
                    + f"recorded {_names(was)}, observed {_names(now)}"
                )
    return lines


def _names(value: object) -> str:
    """Write a list of token names as ``[a, b]``."""
    return "[" + ", ".join(str(name) for name in cast("list[object]", value)) + "]"


class ContentCounters(StrictNestedDictionary):
    """
    The record of a message: its ``count`` and its ``fill_mask``.

    A view on the two keys of the entry metadata, with the paths of the
    file: ``counters[["count", "segments", "principal"]]``. Built on the
    nodes of a message, it holds them, not copies: a change of the message
    metadata is seen through it. Two records are equal when their content
    and their settings are equal.

    The constructor takes the record, or nothing: ndict-tools copies an
    object by building an empty one and filling its keys.

    :param record: A mapping with ``count`` and ``fill_mask``, or None for
        an empty record.
    :type record: Mapping[str, object] | None
    :param default_setup: Settings of the nested dictionary, passed on
        unchanged.
    :type default_setup: Mapping[str, object] | None
    :raises TypeError: If ``record`` is not a mapping with ``count`` and
        ``fill_mask``.
    """

    def __init__(
        self,
        record: Mapping[str, object] | None = None,
        *,
        default_setup: Mapping[str, object] | None = None,
    ) -> None:
        if record is None:
            super().__init__(default_setup=default_setup)
            return
        if not is_type(record, Mapping) or not _RECORD_KEYS <= set(record):
            raise TypeError(
                "ContentCounters needs the count and fill_mask mappings, "
                + f"got {type(record)}"
            )
        super().__init__(
            {"count": record["count"], "fill_mask": record["fill_mask"]},
            default_setup=default_setup,
        )

    @property
    def declensions(self) -> int:
        """
        Number of declensions, the principal included.

        :return: ``self[["count", "declensions"]]``.
        :rtype: int
        """
        return cast(int, self[["count", "declensions"]])

    @property
    def alternatives(self) -> int:
        """
        Number of alternatives.

        :return: ``self[["count", "alternatives"]]``.
        :rtype: int
        """
        return cast(int, self[["count", "alternatives"]])

    @property
    def singulars(self) -> int:
        """
        Number of singulars, one per declension.

        :return: ``self[["count", "singulars"]]``.
        :rtype: int
        """
        return cast(int, self[["count", "singulars"]])

    @property
    def plurals(self) -> int:
        """
        Number of plural segments over every declension.

        :return: ``self[["count", "plurals"]]``.
        :rtype: int
        """
        return cast(int, self[["count", "plurals"]])

    @property
    def segments(self) -> StrictNestedDictionary:
        """
        Number of segments of the principal and of each alternative.

        :return: ``self[["count", "segments"]]``.
        :rtype: StrictNestedDictionary
        """
        return cast(StrictNestedDictionary, self[["count", "segments"]])

    @property
    def tokens(self) -> StrictNestedDictionary:
        """
        Token names of each text, in the shape of the content.

        :return: ``self[["count", "tokens"]]``.
        :rtype: StrictNestedDictionary
        """
        return cast(StrictNestedDictionary, self[["count", "tokens"]])

    @property
    def fill_mask(self) -> StrictNestedDictionary:
        """
        Fill state of each text, in the shape of the content.

        :return: ``self["fill_mask"]``.
        :rtype: StrictNestedDictionary
        """
        return cast(StrictNestedDictionary, self["fill_mask"])

    def defects(self) -> list[str]:
        """
        List why the record is not well formed.

        :return: The defects; empty if the record is well formed.
        :rtype: list[str]
        """
        return record_defects(cast("Mapping[str, object]", self.to_dict()))

    def differences(self, other: "ContentCounters") -> list[str]:
        """
        Describe how ``other`` differs from this record.

        Both records must be well formed.

        :param other: The record to compare with, the observed one.
        :type other: ContentCounters
        :return: One line per difference; empty if the records are equal.
        :rtype: list[str]
        """
        return record_differences(
            cast("Mapping[str, object]", self.to_dict()),
            cast("Mapping[str, object]", other.to_dict()),
        )
