"""
Message: one identifier's texts, context and metadata, in one language.

The content of a message is a principal declension and zero or more
variant declensions (:class:`Declension`).
"""

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, Literal, TypedDict, Unpack, cast

from ndict_tools import StrictNestedDictionary

from i18n_tools._checks import ensure_type, is_type
from i18n_tools._compat import override
from i18n_tools._counters import ContentCounters, check_format_string, observe
from i18n_tools._json import JSONInput
from i18n_tools.exceptions import MessageError

if TYPE_CHECKING:
    from i18n_tools.formatter.plurals import PluralRule


class DeclensionFields(TypedDict, total=False):
    """
    Keyword contract for the texts of one declension.

    The same keys describe the principal and every variant. ``plurals``
    accepts a list or a tuple; it is stored as a tuple.
    """

    singular: str
    plurals: list[str] | tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Declension:
    """
    One singular text and zero or more plural texts.

    The principal of a message and each of its variants are declensions.
    Segment 0 is the singular, segments 1 to n are the plurals: a singular
    with three plurals has four segments. An empty string marks an absent
    text.

    A declension is immutable: a message changes its content by replacing
    whole declensions, so that every change goes through the methods of
    :class:`Message`.

    :param singular: Text of segment 0.
    :type singular: str
    :param plurals: Texts of segments 1 to n, in order.
    :type plurals: tuple[str, ...]
    :raises TypeError: If a text is not a string, or ``plurals`` is not a
        tuple.
    """

    singular: str = ""
    plurals: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        ensure_type(
            self.singular,
            str,
            f"Declension singular must be a string, got {type(self.singular)}",
        )
        ensure_type(
            self.plurals,
            tuple,
            f"Declension plurals must be a tuple, got {type(self.plurals)}",
        )
        for text in self.plurals:
            ensure_type(
                text, str, f"Declension plural must be a string, got {type(text)}"
            )

    @property
    def segments(self) -> tuple[str, ...]:
        """
        All texts of the declension, singular first.

        :return: ``(singular, *plurals)``.
        :rtype: tuple[str, ...]
        """
        return (self.singular, *self.plurals)

    @classmethod
    def from_segments(cls, segments: list[str] | tuple[str, ...]) -> "Declension":
        """
        Build a declension from its texts, singular first.

        :param segments: ``[singular, *plurals]``; must not be empty.
        :type segments: list[str] | tuple[str, ...]
        :return: The declension.
        :rtype: Declension
        :raises ValueError: If ``segments`` is empty.
        :raises TypeError: If ``segments`` is neither a list nor a tuple, or
            a text is not a string.
        """
        ensure_type(
            segments,
            (list, tuple),
            f"Declension segments must be a list or a tuple, got {type(segments)}",
        )
        if len(segments) == 0:
            raise ValueError("A declension has at least one segment (the singular)")
        return cls(segments[0], tuple(segments[1:]))


class LocationEntry(TypedDict):
    """
    A place in source code that uses a message, as the entry stores it.

    ``declension`` and ``segment`` locate the text the source code asks
    for: ``declension=0`` is the principal, ``segment=0`` the singular. A
    coordinate left to None is not fixed at that place.
    """

    file: str
    line: int
    declension: int | None
    segment: int | None


_LOCATION_KEYS = frozenset(LocationEntry.__annotations__)


def _ensure_coordinate(value: object, name: str) -> None:
    """Check an optional location coordinate: None or an int >= 0."""
    if value is None:
        return
    if is_type(value, bool) or not is_type(value, int):
        raise TypeError(f"Location {name} must be an int or None, got {type(value)}")
    if cast(int, value) < 0:
        raise ValueError(f"Location {name} must be >= 0, got {value}")


def _checked_location(value: object) -> LocationEntry:
    """
    Check a location and return it as a new mapping.

    :raises TypeError: If it is not a mapping with the four keys, or a
        field has the wrong type.
    :raises ValueError: If ``file`` is empty, ``line`` is below 1 or a
        coordinate is negative.
    """
    if not is_type(value, Mapping) or frozenset(
        cast("Mapping[str, object]", value)
    ) != (_LOCATION_KEYS):
        raise TypeError(
            "A location is a mapping with the keys file, line, declension and "
            + f"segment, got {value!r}"
        )
    item = cast("Mapping[str, object]", value)
    file = item["file"]
    line = item["line"]
    ensure_type(file, str, f"Location file must be a string, got {type(file)}")
    if file == "":
        raise ValueError("Location file must not be empty")
    if is_type(line, bool) or not is_type(line, int):
        raise TypeError(f"Location line must be an int, got {type(line)}")
    if cast(int, line) < 1:
        raise ValueError(f"Location line must be >= 1, got {line}")
    _ensure_coordinate(item["declension"], "declension")
    _ensure_coordinate(item["segment"], "segment")
    return {
        "file": cast(str, file),
        "line": cast(int, line),
        "declension": cast("int | None", item["declension"]),
        "segment": cast("int | None", item["segment"]),
    }


def _checked_texts(value: object, name: str) -> list[str]:
    """Check a list of strings (flags or comments) and return a new list."""
    if not is_type(value, (list, tuple)) or not all(
        is_type(item, str) for item in cast("Sequence[object]", value)
    ):
        raise TypeError(f"Message {name} must be a list of str, got {value!r}")
    return list(cast("Sequence[str]", value))


def _checked_flags(value: object) -> list[str]:
    """Check flags: non-empty strings, each at most once."""
    flags = _checked_texts(value, "flags")
    for flag in flags:
        if flag == "":
            raise ValueError("A flag must not be empty")
    repeated = sorted({flag for flag in flags if flags.count(flag) > 1})
    if repeated:
        raise ValueError(f"Flag(s) given more than once: {', '.join(repeated)}")
    return flags


def _checked_identifier(value: object) -> str:
    """Check an identifier: a str, or an int converted with str()."""
    if is_type(value, bool) or not is_type(value, (str, int)):
        raise TypeError(
            f"Message identifier must be a str or an int, got {type(value)}"
        )
    identifier = str(value)
    if identifier == "":
        raise ValueError("Message identifier must not be empty")
    return identifier


class MessageOptions(TypedDict, total=False):
    """
    Keyword contract of :class:`Message`: the texts beyond the principal
    singular and the metadata of the entry, all optional.

    ``alternatives`` holds the texts of each alternative, singular first.
    ``status``, ``count`` and ``fill_mask`` are not options: they are set
    by :meth:`Message.mark_complete`, :meth:`Message.reopen` and
    :meth:`Message.record`.
    """

    plurals: list[str] | tuple[str, ...]
    alternatives: list[list[str]] | tuple[tuple[str, ...], ...]
    context: str
    locations: list[LocationEntry]
    flags: list[str]
    user_comments: list[str]
    auto_comments: list[str]
    rules: Mapping[str, JSONInput]


_MESSAGE_OPTIONS = MessageOptions.__optional_keys__
_METADATA_OPTIONS = _MESSAGE_OPTIONS - {"plurals", "alternatives"}

# Keys of the entry metadata changed only by the methods named here.
_GUARDED_KEYS: dict[str, str] = {
    "status": "mark_complete(), reopen()",
    "count": "mark_complete(), record()",
    "fill_mask": "mark_complete(), record()",
}
# Keys of the entry metadata with a property setter, and their default.
_SETTABLE_DEFAULTS: dict[str, object] = {
    "context": "",
    "locations": [],
    "flags": [],
    "user_comments": [],
    "auto_comments": [],
    "rules": {},
}

_DECLENSION_FIELDS = frozenset({"singular", "plurals"})
_DIRECTIONS = frozenset({"natural", "reverse"})
_STATUSES = frozenset({"draft", "complete"})

MessageStatus = Literal["draft", "complete"]
"""Completion status of a message."""


def _ensure_int(value: object, name: str) -> None:
    """Raise TypeError unless ``value`` is an int (a bool is refused)."""
    if is_type(value, bool) or not is_type(value, int):
        raise TypeError(f"{name} must be an int, got {type(value)}")


def _apply_fields(base: Declension, fields: DeclensionFields) -> Declension:
    """
    Return ``base`` with the texts given in ``fields`` replaced.

    :param base: The declension to start from.
    :type base: Declension
    :param fields: ``singular`` and/or ``plurals``.
    :type fields: DeclensionFields
    :return: A new declension.
    :rtype: Declension
    :raises TypeError: If a key is unknown, ``plurals`` is neither a list
        nor a tuple, or a text is not a string.
    """
    unknown = sorted(set(fields) - _DECLENSION_FIELDS)
    if unknown:
        raise TypeError(f"Unknown declension field(s): {', '.join(unknown)}")
    singular = fields.get("singular", base.singular)
    plurals = fields.get("plurals", base.plurals)
    ensure_type(
        plurals,
        (list, tuple),
        f"Declension plurals must be a list or a tuple, got {type(plurals)}",
    )
    return Declension(singular, tuple(plurals))


def _check_format(declension: int, texts: Sequence[str]) -> None:
    """Refuse a text that is not a valid format string."""
    for segment, text in enumerate(texts):
        error = check_format_string(text)
        if error is not None:
            raise ValueError(
                f"text ({declension}, {segment}) is not a valid format string: {error}"
            )


def extract_tokens(text: str) -> list[str]:
    """
    List the tokens of a text, in order of appearance.

    A token is a placeholder variable written ``{name}``.

    :param text: The text to read.
    :type text: str
    :return: The token names, repeated if a token appears several times.
    :rtype: list[str]
    """
    return re.findall(r"\{([^{}]+)\}", text)


class Message:
    """
    One identifier's texts and metadata, in one language.

    The content of a message is a principal declension and zero or more
    variant declensions. A text is addressed by ``(variant, segment)``:
    ``variant=0`` is the principal, ``variant=1`` the first variant;
    ``segment=0`` is the singular, ``segment=1`` the first plural.

    The principal always exists as a structure: an absent principal is a
    declension whose singular is ``""``. ``""`` marks an absent text
    anywhere in the content.

    Declensions may have different numbers of segments while a message is
    edited. :attr:`matrix` pads the shorter ones with ``""``.

    :attr:`metadata` holds the keys of the entry metadata of a ``.i18t``
    file: ``id``, ``context``, ``locations``, ``flags``,
    ``user_comments``, ``auto_comments``, ``status``, ``rules``, and
    ``count`` and ``fill_mask`` once a record is taken. The properties of
    the same names read these keys.

    A message is ``"draft"`` or ``"complete"``. :meth:`mark_complete`
    records the content and locks the texts and the structure;
    :meth:`reopen` makes the message a draft again; :meth:`record` records
    the content of a draft (a draft save). Context, locations, flags,
    comments and rules stay editable in both states.

    :ivar metadata: The entry metadata.
    :ivar plural_rule: Rule resolving a count to a segment, or None.
    """

    metadata: StrictNestedDictionary
    plural_rule: "PluralRule | None"
    _principal: Declension
    _variants: list[Declension]

    # A message is mutable and compares by content: it is not hashable.
    __hash__: ClassVar[None] = None  # pyright: ignore[reportIncompatibleMethodOverride]

    def __init__(
        self,
        id: str | int,
        singular: str = "",
        **options: Unpack[MessageOptions],
    ) -> None:
        """
        Create a draft message.

        :param id: Identifier of the message: a string, or an int
            converted with ``str()``.
        :type id: str | int
        :param singular: The principal singular; ``""`` gives an absent
            principal, to be filled later.
        :type singular: str
        :param options: ``plurals`` of the principal, ``alternatives``
            (the texts of each, singular first), and the metadata
            ``context``, ``locations``, ``flags``, ``user_comments``,
            ``auto_comments`` and ``rules``.
        :type options: MessageOptions
        :raises TypeError: If an option is unknown, is ``status``,
            ``count`` or ``fill_mask``, or a value has the wrong type.
        :raises ValueError: If the identifier is empty, a text is not a
            valid format string, or a flag or a location is refused.
        """
        guarded = sorted(set(options) & set(_GUARDED_KEYS))
        if guarded:
            key = guarded[0]
            raise TypeError(
                f"'{key}' is not a Message option: it is set by {_GUARDED_KEYS[key]}"
            )
        unknown = sorted(set(options) - _MESSAGE_OPTIONS)
        if unknown:
            raise TypeError(f"Unknown Message option(s): {', '.join(unknown)}")
        identifier = _checked_identifier(id)
        ensure_type(
            singular, str, f"Message singular must be a string, got {type(singular)}"
        )
        plurals = options.get("plurals", ())
        ensure_type(
            plurals,
            (list, tuple),
            f"Message plurals must be a list or a tuple, got {type(plurals)}",
        )
        alternatives = options.get("alternatives", ())
        ensure_type(
            alternatives,
            (list, tuple),
            "Message alternatives must be a list or a tuple, "
            + f"got {type(alternatives)}",
        )
        self._principal = Declension(singular, tuple(plurals))
        self._variants = [
            Declension.from_segments(alternative) for alternative in alternatives
        ]
        for index, declension in enumerate(self._declensions()):
            _check_format(index, declension.segments)
        self.metadata = StrictNestedDictionary(
            {"id": identifier}, default_setup={"indent": 2}
        )
        self.plural_rule = None
        self.context = options.get("context", "")
        self.locations = options.get("locations", [])
        self.flags = options.get("flags", [])
        self.user_comments = options.get("user_comments", [])
        self.auto_comments = options.get("auto_comments", [])
        self.metadata["status"] = "draft"
        self.rules = options.get("rules", {})

    @classmethod
    def from_matrix(
        cls,
        id: str | int,
        matrix: list[list[str]],
        **options: Unpack[MessageOptions],
    ) -> "Message":
        """
        Build a draft message from its matrix.

        The matrix has the orientation of the format of 0.10.0: one row per
        segment (row 0 holds the singulars), one column per declension
        (column 0 is the principal). Each column becomes a declension with
        all its cells, empty strings included, so that
        ``Message.from_matrix(id, m).matrix == m``.

        :param id: Identifier of the message, as accepted by the
            constructor.
        :type id: str | int
        :param matrix: Rows of texts; at least one row, all rows of the
            same non-zero length.
        :type matrix: list[list[str]]
        :param options: The metadata options of the constructor; the texts
            come from the matrix.
        :type options: MessageOptions
        :return: The message.
        :rtype: Message
        :raises TypeError: If ``matrix`` or one of its rows is not a list, a
            cell is not a string, or an option is refused.
        :raises ValueError: If ``matrix`` is empty or not rectangular.
        """
        unknown = sorted(set(options) - _METADATA_OPTIONS - set(_GUARDED_KEYS))
        if unknown:
            raise TypeError(f"Unknown Message option(s): {', '.join(unknown)}")
        ensure_type(matrix, list, f"Message matrix must be a list, got {type(matrix)}")
        if len(matrix) == 0:
            raise ValueError("A message matrix has at least one row (the singulars)")
        for row in matrix:
            ensure_type(
                row, list, f"Message matrix row must be a list, got {type(row)}"
            )
            for cell in row:
                ensure_type(
                    cell, str, f"Message matrix cell must be a string, got {type(cell)}"
                )
        columns = len(matrix[0])
        if columns == 0 or any(len(row) != columns for row in matrix):
            raise ValueError(
                "A message matrix is a non-empty rectangle: every row has the "
                + "same number of cells, at least one"
            )
        declensions = [[row[column] for row in matrix] for column in range(columns)]
        texts: MessageOptions = {
            **options,
            "plurals": declensions[0][1:],
            "alternatives": declensions[1:],
        }
        return cls(id, declensions[0][0], **texts)

    @property
    def id(self) -> str:
        """
        Identifier of the message: ``metadata["id"]``.

        The Book that holds the message is the master of its key: it writes
        its key here when it renames the message, and writes its key as the
        ``id`` of the entry on save.

        :return: The identifier.
        :rtype: str
        """
        return cast(str, self.metadata["id"])

    @id.setter
    def id(self, value: str) -> None:
        self.metadata["id"] = _checked_identifier(value)

    def get_id(self) -> str:
        """
        Get the identifier of the message.

        :return: The identifier.
        :rtype: str
        """
        return self.id

    # --- Reading the content -------------------------------------------------

    @property
    def principal(self) -> Declension:
        """
        The principal declension (variant 0).

        :return: The principal; its singular is ``""`` when it is absent.
        :rtype: Declension
        """
        return self._principal

    @property
    def variants(self) -> tuple[Declension, ...]:
        """
        The variant declensions, variant 1 first.

        :return: The variants.
        :rtype: tuple[Declension, ...]
        """
        return tuple(self._variants)

    @property
    def matrix(self) -> list[list[str]]:
        """
        The texts of the message as a matrix.

        One row per segment (row 0 holds the singulars), one column per
        declension (column 0 is the principal), as in the ``.i18t``
        format. The matrix is a rectangle: a declension with fewer plurals
        than another is padded with empty strings. The lists are new on
        each access.

        :return: The matrix of texts.
        :rtype: list[list[str]]
        """
        declensions = self._declensions()
        rows = max(len(declension.segments) for declension in declensions)
        return [
            [
                (
                    declension.segments[segment]
                    if segment < len(declension.segments)
                    else ""
                )
                for declension in declensions
            ]
            for segment in range(rows)
        ]

    @property
    def has_variants(self) -> bool:
        """
        Whether the message has at least one variant.

        :return: True if there is a variant, empty or not.
        :rtype: bool
        """
        return len(self._variants) > 0

    @property
    def has_plurals(self) -> bool:
        """
        Whether a declension of the message has a plural segment.

        The test is structural: a plural segment counts even if its text is
        empty.

        :return: True if the matrix has more than one row.
        :rtype: bool
        """
        return any(len(declension.plurals) > 0 for declension in self._declensions())

    def get_variant(self, variant: int) -> Declension:
        """
        Get a variant declension.

        :param variant: Index of the variant, 1 for the first one.
        :type variant: int
        :return: The variant.
        :rtype: Declension
        :raises TypeError: If ``variant`` is not an int.
        :raises IndexError: If ``variant`` is 0 (the principal) or out of
            range.
        """
        self._check_variant_index(variant)
        return self._variants[variant - 1]

    def get_segment(self, segment: int, variant: int = 0) -> str:
        """
        Get one text of the message, read from the matrix.

        :param segment: Segment of the text, 0 for the singular.
        :type segment: int
        :param variant: Declension of the text, 0 for the principal.
        :type variant: int
        :return: The text; ``""`` for an absent text or a padding cell.
        :rtype: str
        :raises TypeError: If an index is not an int.
        :raises IndexError: If an index is outside the matrix.
        """
        self._check_cell(segment, variant)
        segments = self._declensions()[variant].segments
        return segments[segment] if segment < len(segments) else ""

    # --- Completion status and record --------------------------------------

    @property
    def status(self) -> MessageStatus:
        """
        Completion status, ``metadata["status"]``: ``"draft"`` or
        ``"complete"``.

        :return: The status.
        :rtype: MessageStatus
        """
        return cast(MessageStatus, self.metadata["status"])

    def _padded(self) -> list[list[str]]:
        """The texts of each declension, padded to the same number of segments."""
        matrix = self.matrix
        return [[row[column] for row in matrix] for column in range(len(matrix[0]))]

    def _observed_record(self) -> dict[str, object]:
        """The record of the current content, as plain values."""
        declensions = self._padded()
        return cast("dict[str, object]", observe(declensions[0], declensions[1:]))

    @property
    def observed(self) -> ContentCounters:
        """
        The record of the current content: its ``count`` and ``fill_mask``.

        Declensions with fewer segments than another are counted padded
        with ``""``, as they are written.

        :return: The record, new on each access, with the settings of
            :attr:`metadata`.
        :rtype: ContentCounters
        """
        return ContentCounters(
            self._observed_record(), default_setup=dict(self.metadata.default_setup)
        )

    @property
    def recorded(self) -> ContentCounters | None:
        """
        The record taken at the last validation point, or read from a file.

        A view on ``metadata["count"]`` and ``metadata["fill_mask"]``: it
        holds the stored nodes, not copies.

        :return: The record, or None if the message has none.
        :rtype: ContentCounters | None
        """
        if "count" not in self.metadata or "fill_mask" not in self.metadata:
            return None
        return ContentCounters(
            {"count": self.metadata["count"], "fill_mask": self.metadata["fill_mask"]},
            default_setup=dict(self.metadata.default_setup),
        )

    @property
    def has_divergence(self) -> bool:
        """
        Whether the content no longer matches the record.

        A ``"complete"`` message without a record cannot be verified and
        diverges. A draft without a record does not.

        :return: True if the message diverges.
        :rtype: bool
        """
        recorded = self.recorded
        if recorded is None:
            return self.status == "complete"
        return recorded != self.observed

    def _take_record(self) -> None:
        """Store the record of the current content in the metadata."""
        record = self._observed_record()
        for key in ("count", "fill_mask"):
            self.metadata[key] = StrictNestedDictionary(
                cast("dict[str, object]", record[key]),
                default_setup=dict(self.metadata.default_setup),
            )

    def mark_complete(self) -> None:
        """
        Declare the content final: record it and lock it.

        :raises MessageError: If the message is already complete, its
            principal singular is empty, or its declensions do not all
            have the same number of segments. The status is unchanged.
        """
        if self.status == "complete":
            raise MessageError(f"Message '{self.id}' is already complete")
        if self._principal.singular == "":
            raise MessageError(
                f"Message '{self.id}' cannot be complete: the principal singular "
                + "is empty"
            )
        lengths = {len(declension.segments) for declension in self._declensions()}
        if len(lengths) > 1:
            raise MessageError(
                f"Message '{self.id}' cannot be complete: its declensions have "
                + f"different segment counts {sorted(lengths)}"
            )
        self._take_record()
        self.metadata["status"] = "complete"

    def record(self) -> None:
        """
        Record the content of a draft, as it is now.

        Saving a draft is a validation point: ``Book.save()`` calls this
        method for each draft once the file is written. The record of a
        complete message is taken by :meth:`mark_complete` only.

        :raises MessageError: If the message is complete.
        """
        if self.status == "complete":
            raise MessageError(
                f"Message '{self.id}' is complete: its counters are recorded "
                + "by mark_complete()"
            )
        self._take_record()

    def reopen(self) -> None:
        """
        Make a complete message a draft again; the record is kept.

        :raises MessageError: If the message is already a draft.
        """
        if self.status == "draft":
            raise MessageError(f"Message '{self.id}' is already a draft")
        self.metadata["status"] = "draft"

    # --- Changing the principal ----------------------------------------------

    def add_principal(self, **fields: Unpack[DeclensionFields]) -> None:
        """
        Give the message its principal.

        The principal must be absent (empty singular). Plurals not given
        keep their current segments.

        :param fields: ``singular`` (required, not empty) and ``plurals``.
        :type fields: DeclensionFields
        :raises ValueError: If the principal is present, or ``singular`` is
            missing or empty.
        :raises TypeError: If a field is unknown or has the wrong type.
        :raises MessageError: If the message is complete.
        """
        self._ensure_draft()
        if self._principal.singular != "":
            raise ValueError(
                f"Message '{self.id}' already has a principal: use update_principal()"
            )
        principal = _apply_fields(self._principal, fields)
        if principal.singular == "":
            raise ValueError("A principal needs a non-empty singular")
        _check_format(0, principal.segments)
        self._principal = principal

    def update_principal(self, **fields: Unpack[DeclensionFields]) -> None:
        """
        Replace texts of the principal.

        :param fields: ``singular`` (not empty) and/or ``plurals``.
        :type fields: DeclensionFields
        :raises ValueError: If no field is given or ``singular`` is empty.
        :raises TypeError: If a field is unknown or has the wrong type.
        :raises MessageError: If the message is complete.
        """
        self._ensure_draft()
        principal = self._updated(self._principal, fields, "principal")
        _check_format(0, principal.segments)
        self._principal = principal

    def remove_principal(self) -> None:
        """
        Empty every text of the principal, keeping its number of segments.

        :raises MessageError: If the message is complete.
        """
        self._ensure_draft()
        self._principal = Declension("", tuple("" for _ in self._principal.plurals))

    # --- Changing the variants -----------------------------------------------

    def add_variant(self, **fields: Unpack[DeclensionFields]) -> int:
        """
        Append a variant.

        The variant keeps the segments it is given: it is not padded to the
        segment count of the other declensions.

        :param fields: ``singular`` (required, not empty) and ``plurals``.
        :type fields: DeclensionFields
        :return: The index of the new variant.
        :rtype: int
        :raises ValueError: If ``singular`` is missing or empty.
        :raises TypeError: If a field is unknown or has the wrong type.
        :raises MessageError: If the message is complete.
        """
        self._ensure_draft()
        variant = _apply_fields(Declension(), fields)
        if variant.singular == "":
            raise ValueError("A variant needs a non-empty singular")
        _check_format(len(self._variants) + 1, variant.segments)
        self._variants.append(variant)
        return len(self._variants)

    def update_variant(self, variant: int, **fields: Unpack[DeclensionFields]) -> None:
        """
        Replace texts of a variant.

        :param variant: Index of the variant, 1 for the first one.
        :type variant: int
        :param fields: ``singular`` (not empty) and/or ``plurals``.
        :type fields: DeclensionFields
        :raises IndexError: If ``variant`` is 0 or out of range.
        :raises ValueError: If no field is given or ``singular`` is empty.
        :raises TypeError: If ``variant`` is not an int, or a field is
            unknown or has the wrong type.
        :raises MessageError: If the message is complete.
        """
        self._ensure_draft()
        self._check_variant_index(variant)
        updated = self._updated(
            self._variants[variant - 1], fields, f"variant {variant}"
        )
        _check_format(variant, updated.segments)
        self._variants[variant - 1] = updated

    def remove_variant(self, variant: int) -> None:
        """
        Remove a variant; the following variants move down by one.

        :param variant: Index of the variant, 1 for the first one.
        :type variant: int
        :raises IndexError: If ``variant`` is 0 or out of range.
        :raises TypeError: If ``variant`` is not an int.
        :raises MessageError: If the message is complete.
        """
        self._ensure_draft()
        self._check_variant_index(variant)
        del self._variants[variant - 1]

    # --- Changing segments ---------------------------------------------------

    def add_segment(self, text: str, segment: int, variant: int = 0) -> None:
        """
        Insert a plural row at ``segment`` in every declension.

        ``text`` goes to declension ``variant``, the others get ``""``.
        The rows from ``segment`` on move down by one. A declension that
        does not reach ``segment`` is left as it is, unless it receives the
        text.

        :param text: Text of the new segment in declension ``variant``.
        :type text: str
        :param segment: Position of the new row, from 1 to the current
            number of rows.
        :type segment: int
        :param variant: Declension receiving the text, 0 for the principal.
        :type variant: int
        :raises ValueError: If ``segment`` is 0 (the singular row).
        :raises IndexError: If ``segment`` or ``variant`` is out of range.
        :raises TypeError: If an argument has the wrong type.
        :raises MessageError: If the message is complete.
        """
        self._ensure_draft()
        ensure_type(text, str, f"Segment text must be a string, got {type(text)}")
        _ensure_int(segment, "segment")
        self._check_variant(variant)
        if segment == 0:
            raise ValueError("Segment 0 is the singular: add_segment() inserts plurals")
        rows = len(self.matrix)
        if segment < 0 or segment > rows:
            raise IndexError(f"Segment {segment} is out of range 1..{rows}")
        _check_format(variant, [""] * segment + [text])
        declensions = self._declensions()
        for index, declension in enumerate(declensions):
            segments = list(declension.segments)
            if len(segments) >= segment:
                segments.insert(segment, text if index == variant else "")
            elif index == variant:
                segments.extend("" for _ in range(segment - len(segments)))
                segments.append(text)
            else:
                continue
            self._set_declension(index, Declension.from_segments(segments))

    def update_segment(self, text: str, segment: int, variant: int = 0) -> None:
        """
        Replace one text of the message.

        :param text: The new text; ``""`` marks an absent text, refused for
            the principal singular.
        :type text: str
        :param segment: Segment of the text, 0 for the singular.
        :type segment: int
        :param variant: Declension of the text, 0 for the principal.
        :type variant: int
        :raises ValueError: If ``text`` is empty for ``(0, 0)``.
        :raises IndexError: If an index is outside the matrix.
        :raises TypeError: If an argument has the wrong type.
        :raises MessageError: If the message is complete.
        """
        self._ensure_draft()
        ensure_type(text, str, f"Segment text must be a string, got {type(text)}")
        self._check_cell(segment, variant)
        if segment == 0 and variant == 0 and text == "":
            raise ValueError(
                "The principal singular cannot be emptied: use remove_principal()"
            )
        _check_format(variant, [""] * segment + [text])
        segments = list(self._declensions()[variant].segments)
        segments.extend("" for _ in range(segment + 1 - len(segments)))
        segments[segment] = text
        self._set_declension(variant, Declension.from_segments(segments))

    def remove_segment(self, segment: int) -> None:
        """
        Remove the plural row ``segment`` from every declension.

        :param segment: Row to remove, 1 for the first plural.
        :type segment: int
        :raises ValueError: If ``segment`` is 0 (the singular row).
        :raises IndexError: If ``segment`` is out of range.
        :raises TypeError: If ``segment`` is not an int.
        :raises MessageError: If the message is complete.
        """
        self._ensure_draft()
        _ensure_int(segment, "segment")
        if segment == 0:
            raise ValueError("Segment 0 is the singular and cannot be removed")
        rows = len(self.matrix)
        if segment < 0 or segment >= rows:
            raise IndexError(f"Segment {segment} is out of range 1..{rows - 1}")
        for index, declension in enumerate(self._declensions()):
            if len(declension.segments) > segment:
                segments = list(declension.segments)
                del segments[segment]
                self._set_declension(index, Declension.from_segments(segments))

    # --- Reordering declensions ----------------------------------------------

    def switch(self, source: int, destination: int) -> None:
        """
        Exchange two declensions; 0 is the principal.

        :param source: Index of the first declension.
        :type source: int
        :param destination: Index of the second declension.
        :type destination: int
        :raises IndexError: If the indices are equal or out of range.
        :raises TypeError: If an index is not an int.
        :raises MessageError: If the message is complete.
        """
        self._ensure_draft()
        self._check_variant(source)
        self._check_variant(destination)
        if source == destination:
            raise IndexError(
                f"source ({source}) and destination ({destination}) must be different"
            )
        declensions = self._declensions()
        self._set_declension(source, declensions[destination])
        self._set_declension(destination, declensions[source])

    def toggle(self, direction: Literal["natural", "reverse"] = "natural") -> None:
        """
        Rotate the declensions by one position.

        ``"natural"`` moves 0 to 1, 1 to 2, ..., n to 0; ``"reverse"``
        moves 1 to 0, 2 to 1, ..., 0 to n. Nothing changes without variants.

        :param direction: ``"natural"`` or ``"reverse"``.
        :type direction: Literal["natural", "reverse"]
        :raises ValueError: If ``direction`` is neither value.
        :raises MessageError: If the message is complete.
        """
        self._ensure_draft()
        if not is_type(direction, str) or str(direction) not in _DIRECTIONS:
            raise ValueError("direction must be either 'natural' or 'reverse'")
        declensions = self._declensions()
        if direction == "natural":
            rotated = [declensions[-1], *declensions[:-1]]
        else:
            rotated = [*declensions[1:], declensions[0]]
        self._principal = rotated[0]
        self._variants = rotated[1:]

    # --- Tokens --------------------------------------------------------------

    def format(self, variant: int = 0, segment: int = 0, **tokens: object) -> str:
        """
        Substitute the tokens of one text.

        The text is the exact cell ``(variant, segment)``; an absent text
        gives ``""``. There is no fallback to another cell: the column
        fallback belongs to ``formatter.publish()``.

        :param variant: Declension of the text, 0 for the principal.
        :type variant: int
        :param segment: Segment of the text, 0 for the singular.
        :type segment: int
        :param tokens: Values of the tokens.
        :type tokens: object
        :return: The formatted text.
        :rtype: str
        :raises IndexError: If an index is outside the matrix.
        :raises KeyError: If a token of the text has no value.
        :raises ValueError: If the text cannot be formatted.
        """
        text = self.get_segment(segment, variant)
        try:
            return text.format(**tokens)
        except KeyError as e:
            missing = str(e).strip("'")
            raise KeyError(f"Missing token '{missing}' for message '{self.id}'") from e
        except Exception as e:
            raise ValueError(f"Error formatting message '{self.id}': {e}") from e

    def get_tokens(self, variant: int = 0) -> list[list[str]]:
        """
        List the tokens of each segment of one declension.

        :param variant: Declension to read, 0 for the principal.
        :type variant: int
        :return: One list of token names per segment of the declension.
        :rtype: list[list[str]]
        :raises IndexError: If ``variant`` is out of range.
        :raises TypeError: If ``variant`` is not an int.
        """
        self._check_variant(variant)
        return [extract_tokens(text) for text in self._declensions()[variant].segments]

    # --- Comparisons ---------------------------------------------------------

    @property
    def texts(self) -> frozenset[str]:
        """
        The non-empty texts of the message, wherever they are.

        :return: The set of texts.
        :rtype: frozenset[str]
        """
        return frozenset(
            text
            for declension in self._declensions()
            for text in declension.segments
            if text
        )

    def equal(self, other: object) -> bool:
        """
        Strict equality: same content and same metadata, the identifier,
        the status and the record included.

        :param other: The object to compare with.
        :type other: object
        :return: True if ``other`` is an equal Message.
        :rtype: bool
        """
        if not isinstance(other, Message):
            return False
        return (
            self._principal == other._principal
            and self._variants == other._variants
            and self.metadata.to_dict() == other.metadata.to_dict()
        )

    def isomorph(self, other: object) -> bool:
        """
        Whether ``other`` is a Message with the same matrix.

        Metadata, the identifier included, is ignored.

        :param other: The object to compare with.
        :type other: object
        :return: True if both matrices are equal.
        :rtype: bool
        """
        return isinstance(other, Message) and self.matrix == other.matrix

    def similar(self, other: object) -> bool:
        """
        Whether ``other`` is a Message with the same non-empty texts.

        Where a text is stored (principal or variant, which segment) is
        ignored, as are the identifier, context and metadata.

        :param other: The object to compare with.
        :type other: object
        :return: True if both sets of texts are equal.
        :rtype: bool
        """
        return isinstance(other, Message) and self.texts == other.texts

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Message):
            return NotImplemented
        return self.equal(other)

    @override
    def __str__(self) -> str:
        """
        The principal singular.

        :return: The principal singular.
        :rtype: str
        """
        return self._principal.singular

    @override
    def __repr__(self) -> str:
        return (
            f"Message(id={self.id!r}, principal={self._principal!r}, "
            + f"variants={self._variants!r})"
        )

    # --- Internal helpers ----------------------------------------------------

    def _ensure_draft(self) -> None:
        """Refuse a change of texts or structure on a complete message."""
        if self.status == "complete":
            raise MessageError(
                f"Message '{self.id}' is complete: reopen() it before changing "
                + "its texts or structure"
            )

    def _declensions(self) -> list[Declension]:
        """Return ``[principal, *variants]``, in a new list."""
        return [self._principal, *self._variants]

    def _set_declension(self, variant: int, declension: Declension) -> None:
        """Store ``declension`` at index ``variant`` (0 is the principal)."""
        _check_format(variant, declension.segments)
        if variant == 0:
            self._principal = declension
        else:
            self._variants[variant - 1] = declension

    def _check_variant(self, variant: int) -> None:
        """Check a declension index, 0 (principal) included."""
        _ensure_int(variant, "variant")
        if variant < 0 or variant > len(self._variants):
            raise IndexError(
                f"Variant {variant} is out of range 0..{len(self._variants)}"
            )

    def _check_variant_index(self, variant: int) -> None:
        """Check a variant index: from 1 to the number of variants."""
        _ensure_int(variant, "variant")
        if variant == 0:
            raise IndexError("Variant 0 is the principal: use the principal methods")
        if variant < 0 or variant > len(self._variants):
            raise IndexError(
                f"Variant {variant} is out of range 1..{len(self._variants)}"
            )

    def _check_cell(self, segment: int, variant: int) -> None:
        """Check that ``(variant, segment)`` is inside the matrix."""
        _ensure_int(segment, "segment")
        self._check_variant(variant)
        rows = len(self.matrix)
        if segment < 0 or segment >= rows:
            raise IndexError(f"Segment {segment} is out of range 0..{rows - 1}")

    def _updated(
        self, declension: Declension, fields: DeclensionFields, name: str
    ) -> Declension:
        """Apply ``fields`` to ``declension`` for an update_* method."""
        if not fields:
            raise ValueError(f"No field given to update the {name}")
        updated = _apply_fields(declension, fields)
        if "singular" in fields and updated.singular == "":
            raise ValueError(f"The singular of the {name} cannot be empty")
        return updated

    # --- Metadata ------------------------------------------------------------

    @property
    def context(self) -> str:
        """
        Context that distinguishes messages with the same text,
        ``metadata["context"]``.

        :return: The context; ``""`` when there is none.
        :rtype: str
        """
        return cast(str, self.metadata["context"])

    @context.setter
    def context(self, value: str) -> None:
        if not is_type(value, str):
            raise TypeError(f"Message context must be a str, got {type(value)}")
        self.metadata["context"] = value

    @property
    def rules(self) -> Mapping[str, JSONInput]:
        """
        Plural rules of the message, ``metadata["rules"]``; they override
        those of the Book key by key.

        :return: The stored rules, a ``StrictNestedDictionary``; empty when
            there is none.
        :rtype: Mapping[str, JSONInput]
        """
        return cast("Mapping[str, JSONInput]", self.metadata["rules"])

    @rules.setter
    def rules(self, value: Mapping[str, JSONInput]) -> None:
        if not is_type(value, Mapping):
            raise TypeError(f"Message rules must be a mapping, got {type(value)}")
        self.metadata["rules"] = StrictNestedDictionary(
            dict(value), default_setup=dict(self.metadata.default_setup)
        )

    @property
    def locations(self) -> list[LocationEntry]:
        """
        The places in source code that use the message, in insertion
        order: ``metadata["locations"]``.

        :return: The stored list of locations.
        :rtype: list[LocationEntry]
        """
        return cast("list[LocationEntry]", self.metadata["locations"])

    @locations.setter
    def locations(self, value: list[LocationEntry]) -> None:
        if not is_type(value, (list, tuple)):
            raise TypeError(f"Message locations must be a list, got {type(value)}")
        self.metadata["locations"] = [
            _checked_location(item) for item in cast("Sequence[object]", value)
        ]

    @property
    def flags(self) -> list[str]:
        """
        Flags of the message (``python-format``…), ``metadata["flags"]``.

        :return: The stored list of flags.
        :rtype: list[str]
        """
        return cast("list[str]", self.metadata["flags"])

    @flags.setter
    def flags(self, value: list[str]) -> None:
        self.metadata["flags"] = _checked_flags(value)

    @property
    def user_comments(self) -> list[str]:
        """
        Comments written by translators, ``metadata["user_comments"]``.

        :return: The stored list of comments.
        :rtype: list[str]
        """
        return cast("list[str]", self.metadata["user_comments"])

    @user_comments.setter
    def user_comments(self, value: list[str]) -> None:
        self.metadata["user_comments"] = _checked_texts(value, "user_comments")

    @property
    def auto_comments(self) -> list[str]:
        """
        Comments extracted from source code, ``metadata["auto_comments"]``.

        :return: The stored list of comments.
        :rtype: list[str]
        """
        return cast("list[str]", self.metadata["auto_comments"])

    @auto_comments.setter
    def auto_comments(self, value: list[str]) -> None:
        self.metadata["auto_comments"] = _checked_texts(value, "auto_comments")

    def get_metadata(self, key: list[str] | str | None = None) -> object:
        """
        Get metadata from the message.

        :param key: A key or a path of the metadata; None for the whole
            metadata.
        :type key: list[str] | str | None
        :return: The value stored there.
        :rtype: object
        :raises KeyError: If the key or the path does not exist.
        """
        if key is None:
            return self.metadata

        if (isinstance(key, str) and key in self.metadata) or (
            isinstance(key, list) and key in self.metadata.paths()
        ):
            return self.metadata[key]

        raise KeyError(f"Metadata '{key}' is not a key or path")

    def add_location(
        self,
        file: str,
        line: int,
        variant: int | None = None,
        segment: int | None = None,
    ) -> None:
        """
        Add a place in source code that uses the message.

        ``variant`` and ``segment`` locate the text used at that place; None
        leaves the coordinate open. They are not checked against the
        content: source code may refer to a text not written yet. A
        location already present is not added twice. Locations stay
        editable on a complete message.

        :param file: Path of the source file.
        :type file: str
        :param line: Line number in that file, starting at 1.
        :type line: int
        :param variant: Declension used there, if fixed.
        :type variant: int | None
        :param segment: Segment used there, if fixed.
        :type segment: int | None
        :raises TypeError: If an argument has the wrong type.
        :raises ValueError: If ``file`` is empty, ``line`` is below 1 or a
            coordinate is negative.
        """
        location = _checked_location(
            {"file": file, "line": line, "declension": variant, "segment": segment}
        )
        if location not in self.locations:
            self.locations.append(location)

    def remove_location(self, index: int) -> None:
        """
        Remove a location by its position in :attr:`locations`.

        :param index: Position of the location, from 0.
        :type index: int
        :raises TypeError: If ``index`` is not an int.
        :raises IndexError: If there is no location at ``index``.
        """
        _ensure_int(index, "index")
        if index < 0 or index >= len(self.locations):
            raise IndexError(
                f"Location {index} is out of range 0..{len(self.locations) - 1}"
            )
        del self.locations[index]

    def add_flag(self, flag: str) -> None:
        """
        Add a flag; a flag already present is not added twice.

        :param flag: The flag, a non-empty string.
        :type flag: str
        :raises TypeError: If ``flag`` is not a string.
        :raises ValueError: If ``flag`` is empty.
        """
        _ = _checked_flags([flag])
        if flag not in self.flags:
            self.flags.append(flag)

    def remove_flag(self, flag: str) -> None:
        """
        Remove a flag.

        :param flag: The flag.
        :type flag: str
        :raises ValueError: If the message does not carry ``flag``.
        """
        if flag not in self.flags:
            raise ValueError(f"Message '{self.id}' has no flag '{flag}'")
        self.flags.remove(flag)

    def add_comment(self, mode: Literal["auto", "user"], comment: str) -> None:
        """
        Add a comment to the message.

        :param mode: ``"auto"`` for a comment extracted from source code,
            ``"user"`` for a comment written by a translator.
        :type mode: Literal["auto", "user"]
        :param comment: The comment, not empty.
        :type comment: str
        :raises ValueError: If ``comment`` is empty.
        """
        if len(comment) == 0:
            raise ValueError("Unable to add empty comment")
        key = mode + "_comments"
        cast("list[str]", self.metadata[key]).append(comment)

    def remove_comment(self, mode: Literal["auto", "user"], comment: str) -> None:
        """
        Remove a comment from the message.

        :param mode: ``"auto"`` or ``"user"``, as for :meth:`add_comment`.
        :type mode: Literal["auto", "user"]
        :param comment: The comment.
        :type comment: str
        :raises ValueError: If the message does not hold ``comment``.
        """
        comments = cast("list[str]", self.metadata[mode + "_comments"])
        if comment not in comments:
            raise ValueError(f"Message '{self.id}' has no {mode} comment {comment!r}")
        comments.remove(comment)

    def _set_metadata(
        self, method: str, path: str | list[str], value: object, check: bool
    ) -> None:
        """
        Write one metadata value for the generic mutators.

        A key changed only by a dedicated method is refused; a key with a
        property setter goes through it; inside ``rules`` any path is
        written, the content of ``rules`` being open.
        """
        keys: list[str] = (
            [cast(str, path)] if is_type(path, str) else list(cast("list[str]", path))
        )
        if len(keys) == 0 or not is_type(keys[0], str):
            raise KeyError(f"The path '{path}' is not a present key in the metadata")
        head = keys[0]
        if head in _GUARDED_KEYS:
            raise ValueError(
                f"metadata key '{head}' is not changed by {method}(): use "
                + _GUARDED_KEYS[head]
            )
        if head not in _SETTABLE_DEFAULTS and head != "id":
            raise KeyError(
                f"The key '{head}' is not a present key in the metadata dictionary"
            )
        if len(keys) > 1 and head != "rules":
            raise KeyError(f"The path '{path}' is not a present key in the metadata")
        if check:
            current = self.metadata[keys] if keys in self.metadata.paths() else None
            if current == value:
                raise ValueError(
                    f"The value ({value}) is already stored in the path '{path}'"
                )
        if len(keys) > 1:
            self.metadata[keys] = value
        else:
            setattr(self, head, value)

    def add_metadata(self, *args: tuple[list[str], object], **kwargs: object) -> None:
        """
        Set metadata values, by path or by key.

        ``status``, ``count`` and ``fill_mask`` are refused: they are
        changed by :meth:`mark_complete`, :meth:`reopen` and
        :meth:`record`. The other keys go through the checks of their
        property; a path inside ``rules`` is written as it is.

        :param args: ``(path, value)`` pairs.
        :type args: tuple[list[str], object]
        :param kwargs: ``key=value`` pairs.
        :type kwargs: object
        :raises KeyError: If a key or a path is not one of the metadata.
        :raises ValueError: If a key is changed by a dedicated method, or a
            value is refused by its property.
        :raises TypeError: If a value has the wrong type.
        """
        for path, value in args:
            self._set_metadata("add_metadata", path, value, check=False)
        for key, value in kwargs.items():
            self._set_metadata("add_metadata", key, value, check=False)

    def update_metadata(
        self, *args: tuple[list[str], object], **kwargs: object
    ) -> None:
        """
        Replace metadata values, by path or by key.

        As :meth:`add_metadata`; a value equal to the stored one is
        refused.

        :param args: ``(path, value)`` pairs.
        :type args: tuple[list[str], object]
        :param kwargs: ``key=value`` pairs.
        :type kwargs: object
        :raises KeyError: If a key or a path is not one of the metadata.
        :raises ValueError: If a key is changed by a dedicated method, a
            value is already stored, or a value is refused by its property.
        :raises TypeError: If a value has the wrong type.
        """
        for path, value in args:
            self._set_metadata("update_metadata", path, value, check=True)
        for key, value in kwargs.items():
            self._set_metadata("update_metadata", key, value, check=True)

    def remove_metadata(self, key: str | list[str] | None = None) -> None:
        """
        Reset metadata to its default value.

        :param key: A key or a path inside ``rules``; None resets
            ``context``, ``locations``, ``flags``, the comments and
            ``rules``. The identifier, the status and the record are never
            reset.
        :type key: str | list[str] | None
        :raises KeyError: If the key or the path does not exist.
        :raises ValueError: If the key is the identifier, or a key changed
            by a dedicated method.
        """
        if key is None:
            for name, default in _SETTABLE_DEFAULTS.items():
                setattr(self, name, type(default)())
            return
        keys: list[str] = (
            [cast(str, key)] if is_type(key, str) else list(cast("list[str]", key))
        )
        head = keys[0] if keys else ""
        if head in _GUARDED_KEYS or head == "id":
            raise ValueError(
                f"metadata key '{head}' is not changed by remove_metadata(): use "
                + _GUARDED_KEYS.get(head, "the id property")
            )
        if keys not in self.metadata.paths():
            raise KeyError(
                f"path '{key}' is not a present key in the metadata dictionary"
            )
        if len(keys) > 1:
            del self.metadata[keys]
        else:
            setattr(self, head, type(_SETTABLE_DEFAULTS[head])())
