"""
Message: one identifier's texts, context and metadata, in one language.

The content of a message is a principal declension and zero or more
variant declensions (:class:`Declension`).
"""

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar, Literal, TypedDict, Unpack

from ndict_tools import StrictNestedDictionary

from i18n_tools.__static__ import __version__ as i18n_tools_version
from i18n_tools._checks import ensure_type, is_type
from i18n_tools._compat import override
from i18n_tools._counters import ContentCounters, count_content
from i18n_tools.exceptions import MessageError
from i18n_tools.locale import normalize_language_tag

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


def _ensure_coordinate(value: int | None, name: str) -> None:
    """Check an optional location coordinate: None or an int >= 0."""
    if value is None:
        return
    if is_type(value, bool) or not is_type(value, int):
        raise TypeError(f"Location {name} must be an int or None, got {type(value)}")
    if value < 0:
        raise ValueError(f"Location {name} must be >= 0, got {value}")


@dataclass(frozen=True, slots=True)
class Location:
    """
    A place in source code that uses a message.

    ``variant`` and ``segment`` locate the text the source code asks for,
    with the addressing of the message: ``variant=0`` is the principal,
    ``segment=0`` is the singular. A coordinate left to None is not fixed
    at that call site; a location with no coordinate refers to the whole
    message.

    :param file: Path of the source file.
    :type file: str
    :param line: Line number in that file, starting at 1.
    :type line: int
    :param variant: Declension used at that call site, if fixed.
    :type variant: int | None
    :param segment: Segment used at that call site, if fixed.
    :type segment: int | None
    :raises TypeError: If a field has the wrong type.
    :raises ValueError: If ``file`` is empty, ``line`` is below 1 or a
        coordinate is negative.
    """

    file: str
    line: int
    variant: int | None = None
    segment: int | None = None

    def __post_init__(self) -> None:
        ensure_type(
            self.file, str, f"Location file must be a string, got {type(self.file)}"
        )
        if self.file == "":
            raise ValueError("Location file must not be empty")
        if is_type(self.line, bool) or not is_type(self.line, int):
            raise TypeError(f"Location line must be an int, got {type(self.line)}")
        if self.line < 1:
            raise ValueError(f"Location line must be >= 1, got {self.line}")
        _ensure_coordinate(self.variant, "variant")
        _ensure_coordinate(self.segment, "segment")


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


def _build_empty_metadata() -> StrictNestedDictionary:
    return StrictNestedDictionary(
        {
            "version": i18n_tools_version,
            "language": "",
            "locations": [],
            "flags": ["python-format"],
            "user_comments": [],
            "auto_comments": [],
        },
        default_setup={"indent": 2},
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
    One identifier's texts, context and metadata, in one language.

    The content of a message is a principal declension and zero or more
    variant declensions. A text is addressed by ``(variant, segment)``:
    ``variant=0`` is the principal, ``variant=1`` the first variant;
    ``segment=0`` is the singular, ``segment=1`` the first plural.

    The principal always exists as a structure: an absent principal is a
    declension whose singular is ``""``. ``""`` marks an absent text
    anywhere in the content.

    Declensions may have different numbers of segments while a message is
    edited. :attr:`matrix` pads the shorter ones with ``""``.

    A message is ``"draft"`` or ``"complete"``. :meth:`mark_complete`
    records the content counters and locks the texts and the structure;
    :meth:`reopen` makes the message a draft again; :meth:`record` records
    the counters of a draft (a draft save). Context, locations,
    flags, comments and other metadata stay editable in both states.

    :ivar id: Language-neutral identifier of the message.
    :ivar context: Disambiguation context, kept for other formats.
    :ivar metadata: Version, language, locations, flags and comments.
    :ivar plural_rule: Rule resolving a count to a segment, or None.
    """

    id: str
    context: str
    metadata: StrictNestedDictionary
    plural_rule: "PluralRule | None"
    _principal: Declension
    _variants: list[Declension]
    _status: MessageStatus
    _recorded: ContentCounters | None

    # A message is mutable and compares by content: it is not hashable.
    __hash__: ClassVar[None] = None  # pyright: ignore[reportIncompatibleMethodOverride]

    def __init__(
        self,
        id: str,
        principal: Declension | None = None,
        variants: list[Declension] | tuple[Declension, ...] | None = None,
        context: str = "",
        metadata: dict[str, object] | None = None,
        status: MessageStatus = "draft",
        recorded: ContentCounters | None = None,
    ) -> None:
        """
        Create a message.

        ``status`` and ``recorded`` restore a message read from a file:
        a ``"complete"`` message built this way is not checked as
        :meth:`mark_complete` would check it.

        :param id: Identifier of the message.
        :type id: str
        :param principal: The principal declension; None gives an absent
            principal, ``Declension()``.
        :type principal: Declension | None
        :param variants: The variant declensions, in order.
        :type variants: list[Declension] | tuple[Declension, ...] | None
        :param context: Context of the message.
        :type context: str
        :param metadata: Metadata values, as accepted by
            :meth:`add_metadata`.
        :type metadata: dict[str, object] | None
        :param status: ``"draft"`` or ``"complete"``.
        :type status: MessageStatus
        :param recorded: Counters taken at the last validation point.
        :type recorded: ContentCounters | None
        :raises TypeError: If an argument has the wrong type.
        :raises ValueError: If ``status`` is neither value.
        :raises KeyError: If ``metadata`` holds an unknown key.
        """
        ensure_type(id, str, f"Message id must be a string, got {type(id)}")
        ensure_type(
            principal,
            (Declension, type(None)),
            f"Message principal must be a Declension or None, got {type(principal)}",
        )
        ensure_type(
            variants,
            (list, tuple, type(None)),
            f"Message variants must be a list, a tuple or None, got {type(variants)}",
        )
        for variant in variants or ():
            ensure_type(
                variant,
                Declension,
                f"Message variant must be a Declension, got {type(variant)}",
            )
        ensure_type(
            context, str, f"Message context must be a string, got {type(context)}"
        )
        ensure_type(
            metadata,
            (dict, type(None)),
            f"Message metadata must be a dict or None, got {type(metadata)}",
        )
        if not is_type(status, str) or str(status) not in _STATUSES:
            raise ValueError(
                f"Message status must be 'draft' or 'complete', got {status!r}"
            )
        ensure_type(
            recorded,
            (ContentCounters, type(None)),
            "Message recorded must be ContentCounters or None, "
            + f"got {type(recorded)}",
        )
        self.id = id
        self._principal = principal if principal is not None else Declension()
        self._variants = list(variants) if variants is not None else []
        self.context = context
        self.metadata = _build_empty_metadata()
        self.plural_rule = None
        self._status = status
        self._recorded = recorded
        if metadata is not None:
            self.add_metadata(**metadata)

    @classmethod
    def from_matrix(
        cls,
        id: str,
        matrix: list[list[str]],
        context: str = "",
        metadata: dict[str, object] | None = None,
        status: MessageStatus = "draft",
        recorded: ContentCounters | None = None,
    ) -> "Message":
        """
        Build a message from its matrix.

        The matrix has the orientation of the ``.i18t`` format: one row per
        segment (row 0 holds the singulars), one column per declension
        (column 0 is the principal). Each column becomes a declension with
        all its cells, empty strings included, so that
        ``Message.from_matrix(id, m).matrix == m``.

        :param id: Identifier of the message.
        :type id: str
        :param matrix: Rows of texts; at least one row, all rows of the
            same non-zero length.
        :type matrix: list[list[str]]
        :param context: Context of the message.
        :type context: str
        :param metadata: Metadata of the message, as accepted by the
            constructor.
        :type metadata: dict[str, object] | None
        :param status: Status of the message, as accepted by the
            constructor.
        :type status: MessageStatus
        :param recorded: Recorded counters, as accepted by the constructor.
        :type recorded: ContentCounters | None
        :return: The message.
        :rtype: Message
        :raises TypeError: If ``id`` or ``context`` is not a string,
            ``matrix`` or one of its rows is not a list, or a cell is not a
            string.
        :raises ValueError: If ``matrix`` is empty or not rectangular.
        """
        ensure_type(id, str, f"Message id must be a string, got {type(id)}")
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
        declensions = [
            Declension(matrix[0][column], tuple(row[column] for row in matrix[1:]))
            for column in range(columns)
        ]
        return cls(
            id=id,
            principal=declensions[0],
            variants=declensions[1:],
            context=context,
            metadata=metadata,
            status=status,
            recorded=recorded,
        )

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

    # --- Completion status and counters --------------------------------------

    @property
    def status(self) -> MessageStatus:
        """
        Completion status: ``"draft"`` or ``"complete"``.

        :return: The status.
        :rtype: MessageStatus
        """
        return self._status

    @property
    def observed(self) -> ContentCounters:
        """
        Counters computed from the current content.

        :return: The counters, new on each access.
        :rtype: ContentCounters
        """
        return count_content(self.matrix)

    @property
    def recorded(self) -> ContentCounters | None:
        """
        Counters taken at the last validation point, or read from a file.

        :return: The counters, or None if the message was never validated.
        :rtype: ContentCounters | None
        """
        return self._recorded

    @property
    def has_divergence(self) -> bool:
        """
        Whether the content no longer matches the recorded counters.

        A ``"complete"`` message without recorded counters cannot be
        verified and diverges. A draft without recorded counters does not.

        :return: True if the message diverges.
        :rtype: bool
        """
        if self._recorded is None:
            return self._status == "complete"
        return self._recorded != self.observed

    def mark_complete(self) -> None:
        """
        Declare the content final: record its counters and lock it.

        :raises MessageError: If the message is already complete, its
            principal singular is empty, or its declensions do not all
            have the same number of segments. The status is unchanged.
        """
        if self._status == "complete":
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
        self._recorded = self.observed
        self._status = "complete"

    def record(self) -> None:
        """
        Record the counters of a draft, as they are now.

        Saving a draft is a validation point: ``Book.save()`` calls this
        method for each draft once the file is written. The counters of a
        complete message are recorded by :meth:`mark_complete` only.

        :raises MessageError: If the message is complete.
        """
        if self._status == "complete":
            raise MessageError(
                f"Message '{self.id}' is complete: its counters are recorded "
                + "by mark_complete()"
            )
        self._recorded = self.observed

    def reopen(self) -> None:
        """
        Make a complete message a draft again; the recorded counters are kept.

        :raises MessageError: If the message is already a draft.
        """
        if self._status == "draft":
            raise MessageError(f"Message '{self.id}' is already a draft")
        self._status = "draft"

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
        self._principal = self._updated(self._principal, fields, "principal")

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
        self._variants[variant - 1] = self._updated(
            self._variants[variant - 1], fields, f"variant {variant}"
        )

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
        Strict equality: same identifier, content, context, metadata,
        status and recorded counters.

        :param other: The object to compare with.
        :type other: object
        :return: True if ``other`` is an equal Message.
        :rtype: bool
        """
        if not isinstance(other, Message):
            return False
        return (
            self.id == other.id
            and self._principal == other._principal
            and self._variants == other._variants
            and self.context == other.context
            and self.metadata.to_dict() == other.metadata.to_dict()
            and self._status == other._status
            and self._recorded == other._recorded
        )

    def isomorph(self, other: object) -> bool:
        """
        Whether ``other`` is a Message with the same matrix.

        Identifier, context and metadata are ignored.

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
        if self._status == "complete":
            raise MessageError(
                f"Message '{self.id}' is complete: reopen() it before changing "
                + "its texts or structure"
            )

    def _declensions(self) -> list[Declension]:
        """Return ``[principal, *variants]``, in a new list."""
        return [self._principal, *self._variants]

    def _set_declension(self, variant: int, declension: Declension) -> None:
        """Store ``declension`` at index ``variant`` (0 is the principal)."""
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

    def get_metadata(self, key: list[str] | str | None = None) -> dict[str, Any] | Any:
        """
        Get metadata from the message.

        Args:
            key (list[str] or str, optional): The specific metadata key to retrieve.
                If None, returns all metadata. Defaults to None.

        Returns:
            dict[str, Any] | Any: The requested metadata. If key is None, returns the entire
                metadata dictionary. If key is provided, returns the value for that key.

        Raises:
            KeyError: If the specified key doesn't exist in the metadata.
        """
        if key is None:
            return self.metadata

        if (isinstance(key, str) and key in self.metadata) or (
            isinstance(key, list) and key in self.metadata.paths()
        ):
            return self.metadata[key]

        raise KeyError(f"Metadata '{key}' is not a key or path")

    @property
    def locations(self) -> tuple[Location, ...]:
        """
        The places in source code that use the message, in insertion order.

        :return: The locations.
        :rtype: tuple[Location, ...]
        """
        return tuple(self.metadata["locations"])

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
        location = Location(file, line, variant, segment)
        if location not in self.locations:
            self.metadata["locations"].append(location)

    def add_language(self, lang: str) -> None:
        """
        Set the language of the message.

        Args:
            lang (str): An IETF language tag.
        """
        self.metadata["language"] = normalize_language_tag(lang)

    def add_comment(self, mode: Literal["auto", "user"], comment: str) -> None:
        """
        Add an author's comment to the message.

        Args:
            mode (Literal["auto", "user"], optional): The mode of the comment. Defaults to "auto".
            comment (str): The author's comment to add.
        """
        if len(comment) == 0:
            raise ValueError("Unable to add empty comment")
        key = mode + "_comments"
        self.metadata[key].append(comment)

    def add_metadata(self, *args: tuple[list[str], Any], **kwargs: object) -> None:
        """
        Set metadata for the message.

        Args:
            args (tuple[list[str], Any]): The list of keys and value to pass to the metadata.
            kwargs (dict[str, Any]): The kwargs parameters to pass to the metadata.

        Raises:
            ValueError: If key_or_dict is malformed and value is None.
        """

        if args:
            for path, value in args:
                if (
                    is_type(path, str) and self.metadata.paths().__contains__([path])
                ) or (is_type(path, list) and self.metadata.paths().__contains__(path)):
                    self.metadata[path] = value
                else:
                    raise KeyError(
                        f"The path '{path}' is not a present key in the metadata dictionary"
                    )
        if kwargs:
            for key, value in kwargs.items():

                if isinstance(value, set):
                    raise TypeError(
                        f"{type(value)} type of {value} is not compatible metadata"
                    )

                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        path = [key, sub_key]
                        if not self.metadata.paths().__contains__(path):
                            raise KeyError(
                                f"The path '{path}' is not a present key in the metadata dictionary"
                            )
                        else:
                            self.metadata[path] = sub_value
                elif is_type(key, str) and self.metadata.is_key(key):
                    self.metadata[key] = value
                else:
                    raise KeyError(
                        f"The key '{key}' is not a present key in the metadata dictionary"
                    )

    def update_metadata(self, *args: tuple[list[str], Any], **kwargs: object) -> None:
        """
        Update the message's metadata with new values.

        Args:
            args (Tuple[list[str], Any): is a list of (paths, value) pairs is a StrictNestedDictionary
            kwargs :
        """

        if args:
            for path, value in args:
                if (
                    is_type(path, str) and self.metadata.paths().__contains__([path])
                ) or (is_type(path, list) and self.metadata.paths().__contains__(path)):
                    if self.metadata[path] == value:
                        raise ValueError(
                            f"The value ({value}) is already stored in the path '{path}'"
                        )
                    else:
                        self.metadata[path] = value
                else:
                    raise KeyError(
                        f"The path '{path}' is not a present key in the metadata dictionary"
                    )
        if kwargs:
            for key, value in kwargs.items():
                if isinstance(value, set):
                    raise TypeError(
                        f"{type(value)} of {value} is not compatible metadata"
                    )

                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        path = [key, sub_key]
                        if not self.metadata.paths().__contains__(path):
                            raise KeyError(
                                f"The path '{path}' is not a present key in the metadata dictionary"
                            )
                        elif self.metadata[path] == sub_value:
                            raise ValueError(
                                f"The value ({sub_value}) is already stored in the path '{path}'"
                            )
                        else:
                            self.metadata[path] = sub_value
                elif is_type(key, str) and self.metadata.is_key(key):
                    if self.metadata[key] == value:
                        raise ValueError(
                            f"The value ({value}) is already stored in the path '[{key}]'"
                        )
                    else:
                        self.metadata[key] = value
                else:
                    raise KeyError(
                        f"The key '{key}' is not a present key in the metadata dictionary"
                    )

    def remove_metadata(self, key: str | list[str] | None = None) -> None:
        """
        Delete metadata from the message.

        Args:
            key (str | None, optional): The specific metadata key to delete.
                If None, clears all metadata.

        Raises:
            KeyError: If the specified key doesn't exist in the metadata.
        """

        ref_meta = _build_empty_metadata()

        if key is None:
            self.metadata = ref_meta
        elif isinstance(key, list) and key not in self.metadata.paths():
            raise KeyError(
                f"path '{key}' is not a present key in the metadata dictionary"
            )
        elif isinstance(key, str) and key not in self.metadata.keys():
            raise KeyError(f"Metadata key '{key}' not found")
        else:
            self.metadata[key] = ref_meta[key]
