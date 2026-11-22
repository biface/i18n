"""
This module handles the manipulation of files within the repository using utils.py. It calculates paths, controls file names and access, and retrieves data contained in translation files.

Key Responsibilities:
    - Manipulate files within the repository.
    - Calculate paths, control file names and access.
    - Retrieve data from translation files.

"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Literal, TypedDict, TypeGuard, cast

from babel import __version__ as babel_version
from babel.core import Locale
from ndict_tools import StrictNestedDictionary
from yaml import YAMLError

if TYPE_CHECKING:
    # Only used in fetch_template()/fetch_catalog()'s return-type
    # annotations — never instantiated here (create_template() imports
    # it locally itself, DD-41 #120: this whole PO/MO path is dead in
    # production, build_repository()/verify_repository() have zero
    # callers).
    import tarfile

    from babel.messages.catalog import Catalog

from ..__static__ import (
    I18N_TOOLS_CONFIG,
    I18N_TOOLS_LOCALE,
    I18N_TOOLS_MESSAGES,
    I18N_TOOLS_TEMPLATE,
    I18N_TOOLS_TRANSLATION_FILE_EXT,
    TranslationFileFormat,
)
from ..__static__ import __version__ as i18n_tools_version
from .._counters import (
    is_filled,
    key_path,
    observe,
    read_fields,
    record_defects,
    record_differences,
)
from .._finding import Finding
from .._json import JSONInput, JSONValue
from ..exceptions import FormatError
from ..locale import get_all_languages, is_valid_language_tag, normalize_language_tag
from . import _settings, _utils


def normalize_module_identifier(path: str) -> str:
    """Public API to normalize a module identifier from a filesystem path or identifier.

    Delegates to the internal loaders._utils helper so other layers (CLI, config)
    can prepare a proper module string before interacting with models.
    """
    return _utils.normalize_module_identifier(path)


def _check_matrix(matrix: object) -> TypeGuard[list[list[object]]]:
    """
    Check the messages matrix of one translation entry.

    The matrix is a non-empty list of lists, with at least one non-empty
    row, and every row has the same length.

    :param matrix: The candidate matrix.
    :type matrix: object
    :return: True if the matrix is well-formed, False otherwise.
    :rtype: bool
    """
    if not isinstance(matrix, list):
        return False
    lengths: set[int] = set()
    for row in matrix:
        if not isinstance(row, list):
            return False
        lengths.add(len(row))
    return len(lengths) == 1 and lengths != {0}


def check_json_integrity(data: Mapping[str, JSONInput]) -> bool:
    """
    Check the integrity of translation data.

    Every entry other than the reserved ``.i18n_tools`` and ``metadata``
    keys takes one of two forms:

    - ``{"messages": matrix, "metadata": {...}}``, the native ``.i18t``
      entry; ``metadata`` is optional and must be a dictionary;
    - a bare ``matrix``, the legacy flat form, still readable.

    In both forms the matrix must pass the checks of ``_check_matrix()``.

    :param data: The translation data.
    :type data: dict
    :return: True if the data is valid, False otherwise.
    :rtype: bool
    """

    for key, value in data.items():
        if key in (".i18n_tools", "metadata"):
            continue
        if isinstance(value, dict):
            if "messages" not in value:
                return False
            if not isinstance(value.get("metadata", {}), dict):
                return False
            matrix: object = value["messages"]
        else:
            matrix = value
        if not _check_matrix(matrix):
            return False
    return True


# -----------------------------------------------------------------------------
# Reading a Book file, format 1.0.0
# -----------------------------------------------------------------------------

ROOT = "root"
"""``where`` value of a finding about the root of the file."""

RESERVED_KEYS = (".pyi18t_tools", ".i18n_tools")
"""Root keys that a reader ignores and a writer never writes."""

FORMAT_VERSION = "1.0.0"
"""Version of the format a writer of this package writes."""

DEFAULT_VERSION = "0.0.1"
"""Version of a new Book, and of a file without ``version``."""

GETTEXT_KEYS = (
    "project_id_version",
    "report_msgid_bugs_to",
    "pot_creation_date",
    "po_revision_date",
    "last_translator",
    "language_team",
    "header_comment",
)
"""Keys of the ``gettext`` mapping of the root metadata, in written order."""

BOOK_COUNT_KEYS = (
    "messages",
    "draft",
    "complete",
    "declensions",
    "alternatives",
    "singulars",
    "plurals",
    "segments",
    "filled",
    "empty",
)
"""Keys of the root ``count``, in written order."""

_SEMVER = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")
_KNOWN_MAJORS = frozenset({1})
_ROOT_METADATA_KEYS = frozenset(
    {
        "format_version",
        "version",
        "language",
        "domain",
        "gettext",
        "rules",
        "count",
        "statistics",
    }
)
_BOOK_STATISTICS_INTS = (
    "words",
    "characters",
    "messages_with_alternatives",
    "messages_with_plurals",
    "messages_with_rules",
    "locations",
)
_BOOK_STATISTICS_KEYS = frozenset({*_BOOK_STATISTICS_INTS, "flags", "tokens"})
_ENTRY_KEYS = frozenset({"messages", "metadata"})
_CONTENT_KEYS = frozenset({"principal", "alternatives"})
_ENTRY_METADATA_KEYS = frozenset(
    {
        "id",
        "context",
        "locations",
        "flags",
        "user_comments",
        "auto_comments",
        "status",
        "rules",
        "count",
        "fill_mask",
        "statistics",
    }
)
_ENTRY_STATISTICS_KEYS = frozenset({"words", "characters"})
_LOCATION_KEYS = frozenset({"file", "line", "declension", "segment"})
_COMMENT_KEYS = ("user_comments", "auto_comments")


class BookData(TypedDict):
    """
    Content of a Book file as read, in format 1.0.0.

    ``metadata`` holds ``format_version``, ``version``, ``language``,
    ``domain``, ``gettext`` (its seven keys) and ``rules``, absent values
    replaced as the format says. ``entries`` maps each identifier to its
    entry: ``messages`` (``principal``, ``alternatives``) and ``metadata``
    (``id``, ``context``, ``locations``, ``flags``, ``user_comments``,
    ``auto_comments``, ``status``, ``rules``, and ``count`` and
    ``fill_mask`` when the entry has a record). The root ``count`` and
    ``statistics`` and the entry ``statistics`` are not kept: a writer
    computes them.
    """

    metadata: dict[str, JSONValue]
    entries: dict[str, dict[str, JSONValue]]


class _Entry(TypedDict):
    """An entry read, with what the checks after every entry need."""

    data: dict[str, JSONValue]
    complete: bool
    broken: list[str]
    record: dict[str, JSONValue]


def _is_int(value: object, minimum: int) -> bool:
    """Tell whether ``value`` is an int (not a bool) of at least ``minimum``."""
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


def _is_text_list(value: object) -> bool:
    """Tell whether ``value`` is a list of strings."""
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


Severity = Literal["error", "warning", "info"]


class _Findings:
    """The findings of one read, in the order they are found."""

    def __init__(self) -> None:
        self.items: list[Finding] = []

    def add(self, severity: Severity, where: str, message: str) -> None:
        self.items.append(Finding(severity, where, message))

    def unknown(
        self, node: Mapping[str, object], known: frozenset[str], where: str, *path: str
    ) -> None:
        """One error per key of ``node`` that the format does not define."""
        place = key_path(*path) if path else "the entry"
        for key in node:
            if key not in known:
                self.add("error", where, f"unknown key '{key}' in {place}")


def _read_root(
    root: object, language: str | None, domain: str | None, found: _Findings
) -> dict[str, JSONValue] | None:
    """Check the root metadata and return it as read, or None on an error."""
    if not isinstance(root, dict):
        found.add("error", ROOT, f"{key_path('metadata')} is not a mapping")
        return None
    meta: dict[str, object] = {str(key): value for key, value in root.items()}
    errors = len(found.items)
    found.unknown(meta, _ROOT_METADATA_KEYS, ROOT, "metadata")
    format_version = meta.get("format_version")
    path = key_path("metadata", "format_version")
    if "format_version" not in meta:
        found.add("error", ROOT, f"{path} is missing")
    elif not isinstance(format_version, str):
        found.add("error", ROOT, f"{path} is not a string")
    elif _SEMVER.fullmatch(format_version) is None:
        found.add(
            "error",
            ROOT,
            f"{path} '{format_version}' is not a strict semantic version "
            + "(MAJOR.MINOR.PATCH)",
        )
    elif int(format_version.split(".", 1)[0]) not in _KNOWN_MAJORS:
        major = format_version.split(".", 1)[0]
        found.add(
            "error",
            ROOT,
            f"{path} '{format_version}': major version {major} is not known (known: 1)",
        )
    version = meta.get("version", DEFAULT_VERSION)
    path = key_path("metadata", "version")
    if not isinstance(version, str):
        found.add("error", ROOT, f"{path} is not a string")
    elif _SEMVER.fullmatch(version) is None:
        found.add(
            "error",
            ROOT,
            f"{path} '{version}' is not a strict semantic version (MAJOR.MINOR.PATCH)",
        )
    _check_language(meta, language, found)
    _check_domain(meta, domain, found)
    rules = meta.get("rules", {})
    if not isinstance(rules, dict):
        found.add("error", ROOT, f"{key_path('metadata', 'rules')} is not a mapping")
    if "statistics" in meta:
        _check_book_statistics(meta["statistics"], found)
    if len(found.items) > errors and any(
        finding.severity == "error" for finding in found.items[errors:]
    ):
        return None
    gettext = meta.get("gettext", {})
    fields = gettext if isinstance(gettext, dict) else {}
    return {
        "format_version": cast(str, format_version),
        "version": cast(str, version),
        "language": normalize_language_tag(cast(str, meta["language"])),
        "domain": cast(str, meta["domain"]),
        "gettext": {key: cast(JSONValue, fields.get(key, "")) for key in GETTEXT_KEYS},
        "rules": cast("dict[str, JSONValue]", rules),
    }


def _check_language(
    meta: Mapping[str, object], expected: str | None, found: _Findings
) -> None:
    """Check the root ``language``: present, a valid tag, the expected one."""
    path = key_path("metadata", "language")
    if "language" not in meta:
        found.add("error", ROOT, f"{path} is missing")
        return
    value = meta["language"]
    if not isinstance(value, str):
        found.add("error", ROOT, f"{path} is not a string")
        return
    if not is_valid_language_tag(value):
        found.add("error", ROOT, f"{path} '{value}' is not a valid language tag")
        return
    if expected is None:
        return
    normalized = normalize_language_tag(value)
    if normalized != normalize_language_tag(expected):
        found.add("error", ROOT, f"{path} '{normalized}' is not '{expected}'")


def _check_domain(
    meta: Mapping[str, object], expected: str | None, found: _Findings
) -> None:
    """Check the root ``domain``: present, a string, the expected one."""
    path = key_path("metadata", "domain")
    if "domain" not in meta:
        found.add("error", ROOT, f"{path} is missing")
        return
    value = meta["domain"]
    if not isinstance(value, str):
        found.add("error", ROOT, f"{path} is not a string")
    elif expected is not None and value != expected:
        found.add("error", ROOT, f"{path} '{value}' is not '{expected}'")


def _check_book_statistics(value: object, found: _Findings) -> None:
    """Check the types of the root ``statistics``; it is not compared."""
    base = ("metadata", "statistics")
    if not isinstance(value, dict):
        found.add("error", ROOT, f"{key_path(*base)} is not a mapping")
        return
    statistics: dict[str, object] = {str(key): item for key, item in value.items()}
    found.unknown(statistics, _BOOK_STATISTICS_KEYS, ROOT, *base)
    for key in _BOOK_STATISTICS_INTS:
        if key in statistics and not _is_int(statistics[key], 0):
            found.add("error", ROOT, f"{key_path(*base, key)} is not an integer >= 0")
    flags = statistics.get("flags", {})
    if not isinstance(flags, dict) or not all(
        isinstance(flag, str) and flag != "" and _is_int(number, 0)
        for flag, number in flags.items()
    ):
        found.add(
            "error",
            ROOT,
            f"{key_path(*base, 'flags')} is not a mapping of flags to integers >= 0",
        )
    if not _is_text_list(statistics.get("tokens", [])):
        found.add(
            "error", ROOT, f"{key_path(*base, 'tokens')} is not a list of strings"
        )


def _read_content(
    value: object, where: str, found: _Findings
) -> tuple[list[str], list[list[str]]] | None:
    """Check the ``messages`` of an entry; return its declensions, or None."""
    if isinstance(value, list):
        found.add(
            "error",
            where,
            f"{key_path('messages')} is a matrix (format 0.10.0): expected "
            + '{"principal": [...], "alternatives": [...]}',
        )
        return None
    if not isinstance(value, dict):
        found.add("error", where, f"{key_path('messages')} is not a mapping")
        return None
    content: dict[str, object] = {str(key): item for key, item in value.items()}
    errors = len(found.items)
    found.unknown(content, _CONTENT_KEYS, where, "messages")
    principal = content.get("principal")
    if "principal" not in content:
        found.add("error", where, f"{key_path('messages', 'principal')} is missing")
    elif not isinstance(principal, list):
        found.add("error", where, f"{key_path('messages', 'principal')} is not a list")
    elif len(principal) == 0:
        found.add(
            "error",
            where,
            f"{key_path('messages', 'principal')} is empty: it holds at least the "
            + "singular",
        )
    else:
        for segment, text in enumerate(principal):
            if not isinstance(text, str):
                found.add(
                    "error",
                    where,
                    f"{key_path('messages', 'principal', segment)} is not a string",
                )
    alternatives = content.get("alternatives")
    if "alternatives" not in content:
        found.add("error", where, f"{key_path('messages', 'alternatives')} is missing")
    elif not isinstance(alternatives, list):
        found.add(
            "error", where, f"{key_path('messages', 'alternatives')} is not a list"
        )
    else:
        for index, alternative in enumerate(alternatives):
            if not isinstance(alternative, list):
                found.add(
                    "error",
                    where,
                    f"{key_path('messages', 'alternatives', index)} is not a list",
                )
                continue
            for segment, text in enumerate(alternative):
                if not isinstance(text, str):
                    found.add(
                        "error",
                        where,
                        f"{key_path('messages', 'alternatives', index, segment)} "
                        + "is not a string",
                    )
    if len(found.items) > errors:
        return None
    texts = cast("list[str]", principal)
    others = cast("list[list[str]]", alternatives)
    for index, alternative in enumerate(others):
        if len(alternative) != len(texts):
            found.add(
                "error",
                where,
                f"{key_path('messages', 'alternatives', index)} has "
                + f"{len(alternative)} segments, {key_path('messages', 'principal')} "
                + f"has {len(texts)}",
            )
    if len(found.items) > errors:
        return None
    for declension, segments in enumerate([texts, *others]):
        for segment, text in enumerate(segments):
            try:
                _, positional = read_fields(text)
            except ValueError as e:
                found.add(
                    "error",
                    where,
                    f"text ({declension}, {segment}) is not a valid format string: "
                    + str(e),
                )
                continue
            for field in positional:
                found.add(
                    "warning",
                    where,
                    f"text ({declension}, {segment}) has a positional token "
                    + f"'{{{field}}}': tokens are passed by name",
                )
    if any(finding.severity == "error" for finding in found.items[errors:]):
        return None
    return list(texts), [list(alternative) for alternative in others]


def _read_locations(
    value: object,
    content: tuple[list[str], list[list[str]]] | None,
    where: str,
    found: _Findings,
) -> list[JSONValue]:
    """Check the ``locations`` of an entry; return the valid ones."""
    path = ("metadata", "locations")
    if not isinstance(value, list):
        found.add("error", where, f"{key_path(*path)} is not a list")
        return []
    locations: list[JSONValue] = []
    for index, item in enumerate(value):
        if not _is_location(item):
            found.add(
                "error",
                where,
                f"{key_path(*path, index)} is not a location "
                + '{"file", "line", "declension", "segment"}',
            )
            continue
        location = cast("dict[str, JSONValue]", item)
        locations.append(location)
        if content is None:
            continue
        principal, alternatives = content
        declension = location["declension"]
        segment = location["segment"]
        if isinstance(declension, int) and declension > len(alternatives):
            found.add(
                "warning",
                where,
                f"{key_path(*path, index)}: declension {declension} is beyond the "
                + f"content (0..{len(alternatives)}): to be corrected",
            )
        if isinstance(segment, int) and segment >= len(principal):
            found.add(
                "warning",
                where,
                f"{key_path(*path, index)}: segment {segment} is beyond the content "
                + f"(0..{len(principal) - 1}): to be corrected",
            )
    return locations


def _is_location(value: object) -> bool:
    """Tell whether ``value`` is a location object of format 1.0.0."""
    if not isinstance(value, dict) or frozenset(value) != _LOCATION_KEYS:
        return False
    file = value["file"]
    if not isinstance(file, str) or file == "":
        return False
    if not _is_int(value["line"], 1):
        return False
    return all(
        value[key] is None or _is_int(value[key], 0)
        for key in ("declension", "segment")
    )


def _read_flags(value: object, where: str, found: _Findings) -> list[JSONValue]:
    """Check the ``flags`` of an entry; return them without repetition."""
    path = ("metadata", "flags")
    if not isinstance(value, list):
        found.add("error", where, f"{key_path(*path)} is not a list")
        return []
    flags: list[JSONValue] = []
    for index, flag in enumerate(value):
        if not isinstance(flag, str):
            found.add("error", where, f"{key_path(*path, index)} is not a string")
        elif flag == "":
            found.add("error", where, f"{key_path(*path, index)} is empty")
        elif flag in flags:
            found.add(
                "warning",
                where,
                f"{key_path(*path)}: '{flag}' is repeated: the repetition is removed",
            )
        else:
            flags.append(flag)
    return flags


def _read_status(meta: Mapping[str, object], where: str, found: _Findings) -> bool:
    """Read the status of an entry; return True if it is ``complete``."""
    if "status" not in meta:
        return False
    status = meta["status"]
    if status in ("draft", "complete"):
        return status == "complete"
    found.add(
        "warning",
        where,
        f"{key_path('metadata', 'status')} {status!r} is not 'draft' or 'complete': "
        + "read as draft",
    )
    return False


def _read_entry(key: str, value: object, found: _Findings) -> _Entry | None:
    """Check one entry; return it as read, or None on an error."""
    where = key
    if not isinstance(value, dict):
        found.add("error", where, "entry is not a mapping")
        return None
    entry: dict[str, object] = {str(name): item for name, item in value.items()}
    errors = len(found.items)
    found.unknown(entry, _ENTRY_KEYS, where)
    content: tuple[list[str], list[list[str]]] | None = None
    if "messages" not in entry:
        found.add("error", where, f"{key_path('messages')} is missing")
    else:
        content = _read_content(entry["messages"], where, found)
    if "metadata" not in entry:
        found.add("error", where, f"{key_path('metadata')} is missing")
        return None
    raw = entry["metadata"]
    if not isinstance(raw, dict):
        found.add("error", where, f"{key_path('metadata')} is not a mapping")
        return None
    meta: dict[str, object] = {str(name): item for name, item in raw.items()}
    found.unknown(meta, _ENTRY_METADATA_KEYS, where, "metadata")
    complete = _read_status(meta, where, found)
    absent: Severity = "error" if complete else "warning"
    identifier = meta.get("id")
    path = key_path("metadata", "id")
    if "id" not in meta:
        found.add("error", where, f"{path} is missing")
    elif not isinstance(identifier, str) or identifier == "":
        found.add("error", where, f"{path} is not a non-empty string")
    elif identifier != key:
        found.add("error", where, f"{path} '{identifier}' is not the key of the entry")
    data_meta: dict[str, JSONValue] = {"id": key}
    if "context" not in meta:
        found.add(absent, where, f"{key_path('metadata', 'context')} is missing")
    elif not isinstance(meta["context"], str):
        found.add("error", where, f"{key_path('metadata', 'context')} is not a string")
    data_meta["context"] = cast(JSONValue, meta.get("context", ""))
    if "locations" not in meta:
        found.add(absent, where, f"{key_path('metadata', 'locations')} is missing")
        data_meta["locations"] = []
    else:
        data_meta["locations"] = _read_locations(
            meta["locations"], content, where, found
        )
    if "flags" not in meta:
        found.add(absent, where, f"{key_path('metadata', 'flags')} is missing")
        data_meta["flags"] = []
    else:
        data_meta["flags"] = _read_flags(meta["flags"], where, found)
    for name in _COMMENT_KEYS:
        if name not in meta:
            found.add(absent, where, f"{key_path('metadata', name)} is missing")
        elif not _is_text_list(meta[name]):
            found.add(
                "error", where, f"{key_path('metadata', name)} is not a list of strings"
            )
        data_meta[name] = cast(JSONValue, meta.get(name, []))
    data_meta["status"] = "complete" if complete else "draft"
    rules = meta.get("rules", {})
    if not isinstance(rules, dict):
        found.add("error", where, f"{key_path('metadata', 'rules')} is not a mapping")
    data_meta["rules"] = cast(JSONValue, rules)
    if "statistics" not in meta:
        found.add(absent, where, f"{key_path('metadata', 'statistics')} is missing")
    else:
        _check_entry_statistics(meta["statistics"], where, found)
    observed = None if content is None else observe(*content)
    broken = _read_record(meta, data_meta, observed, complete, where, found)
    if content is not None and not is_filled(content[0][0]) and complete:
        broken.append("principal singular not filled")
    if any(finding.severity == "error" for finding in found.items[errors:]):
        return None
    principal, alternatives = cast("tuple[list[str], list[list[str]]]", content)
    data: dict[str, JSONValue] = {
        "messages": {
            "principal": cast("list[JSONValue]", principal),
            "alternatives": cast("list[JSONValue]", alternatives),
        },
        "metadata": data_meta,
    }
    # The Book counters sum the records as written: the record read when it
    # is kept, otherwise the record of the content.
    record: dict[str, JSONValue] = (
        {"count": data_meta["count"], "fill_mask": data_meta["fill_mask"]}
        if "count" in data_meta
        else cast("dict[str, JSONValue]", observed)
    )
    return {"data": data, "complete": complete, "broken": broken, "record": record}


def _check_entry_statistics(value: object, where: str, found: _Findings) -> None:
    """Check the types of the ``statistics`` of an entry; it is not compared."""
    path = ("metadata", "statistics")
    if not isinstance(value, dict):
        found.add("error", where, f"{key_path(*path)} is not a mapping")
        return
    statistics: dict[str, object] = {str(key): item for key, item in value.items()}
    found.unknown(statistics, _ENTRY_STATISTICS_KEYS, where, *path)
    for key in ("words", "characters"):
        if key in statistics and not _is_int(statistics[key], 0):
            found.add("error", where, f"{key_path(*path, key)} is not an integer >= 0")


def _read_record(
    meta: Mapping[str, object],
    data_meta: dict[str, JSONValue],
    observed: dict[str, JSONValue] | None,
    complete: bool,
    where: str,
    found: _Findings,
) -> list[str]:
    """
    Check the record of an entry and keep it in ``data_meta`` when it is
    used; return the defects that make a ``complete`` message broken.
    """
    missing = [name for name in ("count", "fill_mask") if name not in meta]
    if missing and not complete:
        return []
    if missing:
        names = " and ".join(key_path("metadata", name) for name in missing)
        return [f"no record ({names} missing)"]
    record = {"count": meta["count"], "fill_mask": meta["fill_mask"]}
    defects = record_defects(record)
    if defects:
        if complete:
            for defect in defects:
                found.add("error", where, f"record not well formed: {defect}")
        else:
            found.add(
                "warning",
                where,
                "record ignored, not well formed: " + "; ".join(defects),
            )
        return []
    data_meta["count"] = cast(JSONValue, record["count"])
    data_meta["fill_mask"] = cast(JSONValue, record["fill_mask"])
    if observed is None:
        return []
    differences = record_differences(record, observed)
    if not differences:
        return []
    if complete:
        return ["the content differs from the record: " + "; ".join(differences)]
    found.add(
        "info",
        where,
        "the content differs from the record (completeness not validated): "
        + "; ".join(differences),
    )
    return []


def book_count(entries: Iterable[Mapping[str, object]]) -> dict[str, JSONValue]:
    """
    Compute the root ``count`` of a Book from its entries.

    Each entry gives its status and the record of its content, as a writer
    writes them (``{"status": ..., "count": ..., "fill_mask": ...}``).

    :param entries: The status and record of each entry.
    :type entries: Iterable[Mapping[str, object]]
    :return: The ``count`` of the Book, keys in written order.
    :rtype: dict[str, JSONValue]
    """
    totals = dict.fromkeys(BOOK_COUNT_KEYS, 0)
    for entry in entries:
        count = cast("Mapping[str, object]", entry["count"])
        mask = cast("Mapping[str, object]", entry["fill_mask"])
        totals["messages"] += 1
        totals["complete" if entry["status"] == "complete" else "draft"] += 1
        for key in ("declensions", "alternatives", "singulars", "plurals"):
            totals[key] += cast(int, count[key])
        values = [
            *cast("list[bool]", mask["principal"]),
            *(
                value
                for alternative in cast("list[list[bool]]", mask["alternatives"])
                for value in alternative
            ),
        ]
        totals["segments"] += len(values)
        totals["filled"] += sum(1 for value in values if value)
        totals["empty"] += sum(1 for value in values if not value)
    return {key: value for key, value in totals.items()}


def book_statistics(
    entries: Iterable[Mapping[str, JSONInput]],
) -> dict[str, JSONValue]:
    """
    Compute the root ``statistics`` of a Book from its entries as written.

    :param entries: The entries, ``messages`` and ``metadata`` with their
        ``statistics``, ``locations``, ``flags``, ``rules`` and ``count``.
    :type entries: Iterable[Mapping[str, JSONInput]]
    :return: The ``statistics`` of the Book, keys in written order.
    :rtype: dict[str, JSONValue]
    """
    words = characters = with_alternatives = with_plurals = with_rules = 0
    locations = 0
    flags: dict[str, JSONValue] = {}
    tokens: set[str] = set()
    for entry in entries:
        content = cast("Mapping[str, Sequence[object]]", entry["messages"])
        meta = cast("Mapping[str, object]", entry["metadata"])
        statistics = cast("Mapping[str, int]", meta["statistics"])
        words += statistics["words"]
        characters += statistics["characters"]
        with_alternatives += 1 if len(content["alternatives"]) > 0 else 0
        with_plurals += 1 if len(content["principal"]) > 1 else 0
        with_rules += 1 if len(cast("Mapping[str, object]", meta["rules"])) > 0 else 0
        locations += len(cast("Sequence[object]", meta["locations"]))
        for flag in cast("Sequence[str]", meta["flags"]):
            flags[flag] = cast(int, flags.get(flag, 0)) + 1
        count = cast("Mapping[str, Mapping[str, object]]", meta["count"])
        names = count["tokens"]
        for text in cast("Sequence[Sequence[str]]", names["principal"]):
            tokens.update(text)
        for alternative in cast(
            "Sequence[Sequence[Sequence[str]]]", names["alternatives"]
        ):
            for text in alternative:
                tokens.update(text)
    return {
        "words": words,
        "characters": characters,
        "messages_with_alternatives": with_alternatives,
        "messages_with_plurals": with_plurals,
        "messages_with_rules": with_rules,
        "locations": locations,
        "flags": flags,
        "tokens": cast("list[JSONValue]", sorted(tokens)),
    }


def read_book(
    data: Mapping[str, object], language: str | None = None, domain: str | None = None
) -> tuple[BookData | None, list[Finding]]:
    """
    Read the content of a Book file in format 1.0.0.

    Every rule of the format reference is checked, with its severity,
    against ``language`` and ``domain`` when given. The content is
    returned as the format says to read it: absent values replaced,
    repeated flags removed, a record not well formed ignored in a draft,
    an invalid status and a broken message read as ``draft``.

    :param data: The content of the file, as parsed.
    :type data: Mapping[str, object]
    :param language: The language expected from the place of the file, or
        None to skip the comparison.
    :type language: str | None
    :param domain: The domain expected from the place of the file, or None
        to skip the comparison.
    :type domain: str | None
    :return: The content read, None if there is an error, and every
        finding, in the order they are found.
    :rtype: tuple[BookData | None, list[Finding]]
    """
    found = _Findings()
    root: dict[str, JSONValue] | None = None
    if "metadata" not in data:
        found.add("error", ROOT, f"{key_path('metadata')} is missing")
    else:
        root = _read_root(data["metadata"], language, domain, found)
    entries: dict[str, _Entry] = {}
    unread = 0
    for key, value in data.items():
        if key == "metadata" or key in RESERVED_KEYS:
            continue
        if key == "":
            found.add("error", ROOT, "an identifier is empty")
            unread += 1
            continue
        entry = _read_entry(key, value, found)
        if entry is None:
            unread += 1
        else:
            entries[key] = entry
    book_complete = len(entries) > 0 and all(
        entry["complete"] for entry in entries.values()
    )
    for key, entry in entries.items():
        if not entry["complete"] or not entry["broken"]:
            continue
        defects = "; ".join(entry["broken"])
        meta = cast("dict[str, JSONValue]", entry["data"]["metadata"])
        meta["status"] = "draft"
        if book_complete:
            found.add(
                "warning",
                key,
                f"complete message broken ({defects}): read as draft, and its Book "
                + "with it",
            )
        else:
            found.add(
                "info", key, f"complete message broken ({defects}): read as draft"
            )
    # The Book counters are compared only when every entry could be read.
    if root is not None and unread == 0 and isinstance(data["metadata"], dict):
        _check_book_count(
            cast("Mapping[str, object]", data["metadata"]), entries, found
        )
    if any(finding.severity == "error" for finding in found.items) or root is None:
        return None, found.items
    content: BookData = {
        "metadata": root,
        "entries": {key: entry["data"] for key, entry in entries.items()},
    }
    return content, found.items


def _check_book_count(
    meta: Mapping[str, object], entries: Mapping[str, _Entry], found: _Findings
) -> None:
    """Compare the root ``count`` with the entries read."""
    path = ("metadata", "count")
    if "count" not in meta:
        found.add(
            "warning",
            ROOT,
            f"{key_path(*path)} is missing: recomputed at the next write",
        )
        return
    count = meta["count"]
    if not isinstance(count, dict):
        found.add("error", ROOT, f"{key_path(*path)} is not a mapping")
        return
    values: dict[str, object] = {str(key): item for key, item in count.items()}
    found.unknown(values, frozenset(BOOK_COUNT_KEYS), ROOT, *path)
    typed = True
    for key in BOOK_COUNT_KEYS:
        if key in values and not _is_int(values[key], 0):
            found.add("error", ROOT, f"{key_path(*path, key)} is not an integer >= 0")
            typed = False
    if not typed:
        return
    expected = book_count(
        {"status": "complete" if entry["complete"] else "draft", **entry["record"]}
        for entry in entries.values()
    )
    for key in BOOK_COUNT_KEYS:
        if key not in values:
            found.add(
                "warning",
                ROOT,
                f"{key_path(*path, key)} is missing: recomputed at the next write",
            )
        elif values[key] != expected[key]:
            found.add(
                "warning",
                ROOT,
                f"{key_path(*path, key)} is {values[key]}, the entries give "
                + f"{expected[key]}: recomputed at the next write",
            )


def inspect_book_data(
    data: Mapping[str, object], language: str | None = None, domain: str | None = None
) -> list[Finding]:
    """
    Check the content of a Book file and list what is wrong with it.

    The same checks as :func:`read_book`, which this function calls; only
    the findings are returned.

    :param data: The content of the file, as parsed.
    :type data: Mapping[str, object]
    :param language: The language expected, or None to skip the comparison.
    :type language: str | None
    :param domain: The domain expected, or None to skip the comparison.
    :type domain: str | None
    :return: The findings, in the order they are found.
    :rtype: list[Finding]
    """
    return read_book(data, language, domain)[1]


def read_book_data(file_path: Path | str) -> dict[str, object]:
    """
    Read the content of a Book file, in the format given by its extension
    (DD-34), without checking it.

    :param file_path: Path to the ``.i18t`` file.
    :type file_path: Path | str
    :return: The content of the file, keyed by the root keys.
    :rtype: dict[str, object]
    :raises FileNotFoundError: If the file does not exist.
    :raises FormatError: If the content cannot be parsed, or is not a
        mapping.
    """
    try:
        # The reader is typed as returning a mapping; YAML may give any
        # value, so the result is checked as an object.
        data = cast(
            object, _utils.load_by_format(file_path, _utils.detect_format(file_path))
        )
    except (ValueError, YAMLError) as e:
        raise FormatError(f"unreadable content: {e}") from e
    if not isinstance(data, dict):
        raise FormatError("content is not a mapping")
    return {str(key): value for key, value in data.items()}


def build_path(base_path: str, *sub_dirs: str) -> str:
    """
    Constructs, cleans, and validates a path by combining a base path with one or more subdirectories.

    This function ensures that the constructed path does not contain any elements
    that could corrupt the path, such as '..'. It also verifies that the path exists.

    :param base_path: The starting path.
    :type base_path: Union[Path, str]
    :param sub_dirs: One or more subdirectory names to append to the base path.
    :type sub_dirs: str
    :return: The combined, cleaned, and validated path as a string.
    :rtype: str
    :raises IOError: If the constructed path is invalid or does not exist.
    """
    # Construct the initial path
    constructed_path = _utils.build_path(base_path, *sub_dirs)

    # Remove any '..' or other invalid elements
    cleaned_path = Path(*[part for part in constructed_path.parts if part != ".."])

    # Check if the cleaned path exists
    if not cleaned_path.exists():
        raise IOError(f"The path '{cleaned_path}' does not exist.")

    return str(cleaned_path)


def build_book_filename(
    domain: str, fmt: TranslationFileFormat | None = None
) -> tuple[TranslationFileFormat, str]:
    """
    Resolve the storage format (default + validation) and the corresponding
    `.i18t` filename for a translation domain, without requiring a `Book`
    instance.

    This is the single place where the default-format and filename-building
    rules for a translation dictionary are applied — used by `Book`
    (via `loader.py`, never imported here directly, DD-06) to keep its own
    file format default/validation consistent across its constructor and
    its `add_file_format()`/`update_file_format()` methods, and reusable
    from `core.py`, `sync.py`, or a future CLI without constructing a `Book` first.

    :param domain: The translation domain name.
    :type domain: str
    :param fmt: The desired storage format ("json" or "yaml"). Defaults to
                "json" if ``None``.
    :type fmt: TranslationFileFormat | None
    :return: A ``(format, filename)`` tuple, e.g. ``("json", "messages.json.i18t")``.
    :rtype: tuple[TranslationFileFormat, str]
    :raises ValueError: If ``fmt`` is not a recognised translation format.
    """
    _fmt = _utils.validate_translation_format(fmt)
    filename = f"{domain}.{_fmt}.{I18N_TOOLS_TRANSLATION_FILE_EXT}"
    return _fmt, filename


def file_exists(file_path: str) -> bool:
    """
    Checks if a file exists at the given path.

    This function verifies the existence of a file at the specified path.

    :param file_path: The path to the file.
    :type file_path: str
    :return: True if the file exists, False otherwise.
    :rtype: bool
    """
    return _utils.exist_path(file_path)


def is_absolute_path(path: str) -> bool:
    return _utils.is_absolute_path(path)


def create_directory(path: str) -> None:
    """
    Creates a directory at the specified path.

    This function ensures that the directory and any necessary parent directories
    are created. If the directory already exists, no action is taken.

    :param path: The path to the directory to be created.
    :type path: str
    """
    _utils.create_directory(path)


# Create operations


def create_template(
    repository: StrictNestedDictionary, module: str, domain: str
) -> None:
    """
    Creates an empty template file for a given domain in the specified module.

    This function generates an empty template file (.pot) in the appropriate
    directory structure for the specified module and domain.

    :param repository: The data structure representing the translation repository.
    :type repository: StrictNestedDictionary
    :param module: The module path.
    :type module: str
    :param domain: The domain name.
    :type domain: str
    """
    from babel.messages.catalog import Catalog

    _utils.check_domains(repository, module, [domain])
    path = build_path(
        repository[["paths", "repository"]],
        module,
        I18N_TOOLS_LOCALE,
        I18N_TOOLS_TEMPLATE,
    )
    catalog = Catalog(
        project=repository[["details", "name"]],
        version=repository[["details", "version"]],
        copyright_holder=f"i18n-tools ({i18n_tools_version}) builder",
        msgid_bugs_address=repository[["details", "report-bugs-to"]],
        fuzzy=(
            bool(repository[["details", "flags", "fuzzy"]])
            if ["details", "flags", "fuzzy"] in repository.paths()
            else True
        ),
    )
    catalog.header_comment = f"""
# This POT file is generated for PROJECT project.
# By ORGANIZATION and is dedicated to {domain} domain
# of translations in {module} module of PROJECT project.
#
# The aim of this project is described as :
# {repository[["details", "description"]]}
#
# It will be used as a template for translation of {domain} domain
# in specific language.
#
# This file is distributed under the same license as the PROJECT
# project.
"""
    catalog.domain = domain
    catalog.mime_headers = [
        (
            "Project-Id-Version",
            f"{repository[['details', 'name']]} {repository[['details', 'version']]}",
        ),
        ("Report-Msgid-Bugs-To", repository[["details", "report-bugs-to"]]),
        ("POT-Creation-Date", repository[["details", "creation_date"]]),
        ("PO-Revision-Date", "YEAR-MO-DA HO:MI+ZONE"),
        ("Last-Translator", ""),
        ("Language-Team", repository[["details", "language_team"]]),
        ("Language", ""),
        ("MIME-Version", "1.0"),
        (
            "Content-Type",
            f"{repository[['details', 'content_type']]}; charset=utf-8",
        ),
        ("Content-Transfer-Encoding", "8bit"),
        (
            "Generated-By",
            f"i18n-tools ({i18n_tools_version}) using Babel ({babel_version})",
        ),
    ]

    template_file = path + f"/{domain}.pot"
    if not _utils.exist_path(template_file):
        _utils.save_text(template_file, catalog)
    else:
        raise FileExistsError(
            f"The path '{template_file}' already exists. You cannot overwrite it."
        )


def create_catalog(
    repository: StrictNestedDictionary, module: str, language: str, domain: str
) -> None:
    """
    Creates an empty translation catalog for a given language and domain in the specified module.

    This function generates an empty translation catalog (.po) in the appropriate
    directory structure for the specified module, language, and domain.

    :param repository: The data structure representing the translation repository.
    :type repository: StrictNestedDictionary
    :param module: The module path.
    :type module: str
    :param language: The language code.
    :type language: str
    :param domain: The domain name.
    :type domain: str
    """

    _utils.check_domains(repository, module, [domain])
    path = build_path(
        repository[["paths", "repository"]],
        module,
        I18N_TOOLS_LOCALE,
        language,
        I18N_TOOLS_MESSAGES,
    )
    catalog = fetch_template(repository, module, domain)
    catalog_path = path + f"/{domain}.po"
    catalog.locale = Locale.parse(language, sep="-")
    catalog.domain = domain
    if not _utils.exist_path(catalog_path):
        _utils.save_text(catalog_path, catalog)
        _utils.convert_catalog(catalog_path)
    else:
        raise FileExistsError(
            f"The path '{catalog_path}' already exists. You cannot overwrite it"
        )


def create_dictionary(
    repository: StrictNestedDictionary,
    module: str,
    language: str,
    domain: str,
    fmt: TranslationFileFormat | None = None,
) -> None:
    """
    Creates an empty translation dictionary for a given language and domain in the specified module.

    This function generates an empty translation dictionary (.json) in the appropriate
    directory structure for the specified module, language, and domain.

    :param repository: The data structure representing the translation repository.
    :type repository: StrictNestedDictionary
    :param module: The module path.
    :type module: str
    :param language: The language code.
    :type language: str
    :param domain: The domain name.
    :type domain: str
    """
    _utils.check_domains(repository, module, [domain])
    path = build_path(
        repository[["paths", "repository"]],
        module,
        I18N_TOOLS_LOCALE,
        language,
        I18N_TOOLS_MESSAGES,
    )
    # Default behavior remains JSON when fmt is None
    dictionary_path = _utils.build_dictionary_path(path, domain, fmt)
    _fmt = _utils.validate_translation_format(fmt)
    if not _utils.exist_path(dictionary_path):
        _utils.save_by_format(dictionary_path, {}, _fmt)
    else:
        raise FileExistsError(
            f"The path '{dictionary_path}' already exists. You cannot overwrite it"
        )


# Read operations


def fetch_template(
    repository: StrictNestedDictionary, module: str, domain: str
) -> Catalog:
    """
    Fetches the content of a template file.

    This function reads and returns the content of the specified template file.

    :param repository: The data structure representing the translation repository.
    :type repository: StrictNestedDictionary
    :param module: The module path.
    :type module: str
    :param domain: The domain name.
    :type domain: str
    :return: The content of the template file.
    :rtype: str
    """

    _utils.check_domains(repository, module, [domain])
    path = build_path(
        repository[["paths", "repository"]],
        module,
        I18N_TOOLS_LOCALE,
        I18N_TOOLS_TEMPLATE,
    )
    template_file = path + f"/{domain}.pot"
    catalog = _utils.load_text(template_file)
    catalog.domain = domain
    catalog.copyright_holder = "i18n-tools builder"

    return catalog


def fetch_catalog(
    repository: StrictNestedDictionary, module: str, language: str, domain: str
) -> Catalog:
    """
    Fetches the translation catalog for a given language and domain.

    This function reads and returns the translation catalog from the specified .po file.

    :param repository: The data structure representing the translation repository.
    :type repository: StrictNestedDictionary
    :param module: The module path.
    :type module: str
    :param language: The language code.
    :type language: str
    :param domain: The domain name.
    :type domain: str
    :return: The translation catalog.
    :rtype: Catalog
    """
    _utils.check_domains(repository, module, [domain])
    path = build_path(
        repository[["paths", "repository"]],
        module,
        I18N_TOOLS_LOCALE,
        language,
        I18N_TOOLS_MESSAGES,
    )
    catalog_path = path + f"/{domain}.po"
    catalog = _utils.load_text(catalog_path)
    catalog.domain = domain
    catalog.copyright_holder = "i18n-tools builder"

    return catalog


def fetch_dictionary(
    repository: StrictNestedDictionary,
    module: str,
    language: str,
    domain: str,
    fmt: TranslationFileFormat | None = None,
) -> dict[str, JSONValue]:
    """
    Fetches the translation dictionary for a given language and domain.

    This function reads and returns the translation dictionary from the specified .json file.

    :param repository: The data structure representing the translation repository.
    :type repository: StrictNestedDictionary
    :param module: The module path.
    :type module: str
    :param language: The language code.
    :type language: str
    :param domain: The domain name.
    :type domain: str
    :return: The translation dictionary.
    :rtype: dict[str, JSONValue]
    """

    _utils.check_domains(repository, module, [domain])
    path = build_path(
        repository[["paths", "repository"]],
        module,
        I18N_TOOLS_LOCALE,
        language,
        I18N_TOOLS_MESSAGES,
    )
    dictionary_path = _utils.build_dictionary_path(path, domain, fmt)
    _fmt = _utils.validate_translation_format(fmt)
    dictionary = _utils.load_by_format(dictionary_path, _fmt)

    return dictionary


# Update operations


def update_catalog(
    repository: StrictNestedDictionary,
    module: str,
    language: str,
    domain: str,
    data: Mapping[str | tuple[str, ...], dict[str, str]],
) -> None:
    """
    Updates the translation catalog for a given language and domain.

    This function saves the provided translation catalog to the specified .po file
    and updates the corresponding .mo file.

    :param repository: The data structure representing the translation repository.
    :type repository: StrictNestedDictionary
    :param module: The module path.
    :type module: str
    :param language: The language code.
    :type language: str
    :param domain: The domain name.
    :type domain: str
    :param data: An adapted translation dictionary.
    :type data: Mapping[str | tuple[str, ...], dict[str, str]]
    """

    # TODO: Must update template file as well

    _utils.check_domains(repository, module, [domain])
    path = build_path(
        repository[["paths", "repository"]],
        module,
        I18N_TOOLS_LOCALE,
        language,
        I18N_TOOLS_MESSAGES,
    )
    catalog_path = path + f"/{domain}.po"
    catalog = _utils.load_text(catalog_path)

    for key, value in data.items():
        # Handle pluralizable messages
        string_value = value.get("string", "")

        # If the key is a tuple/list (pluralizable) and the string is not,
        # convert the string to a tuple with appropriate number of elements
        if isinstance(key, (tuple, list)) and not isinstance(
            string_value, (tuple, list)
        ):
            # For pluralizable messages, string should be a tuple/list
            # with the same number of elements as the key
            if string_value:
                # If we have a string, use it as the first element (singular form)
                # and add empty strings for the plural forms
                string_value = tuple([string_value] + [""] * (len(key) - 1))
            else:
                # If we don't have a string, create a tuple with empty strings
                string_value = tuple([""] * len(key))

        _ = catalog.add(
            id=key,
            string=string_value,
            locations=[
                (
                    (loc.split(":")[0], int(loc.split(":")[1]))
                    if ":" in loc
                    else (loc, 0)
                )
                for loc in value.get("locations", [])
                if isinstance(loc, str)
            ],
            previous_id=value.get("previous_id", ""),
            flags=["python-format"],
        )

    _utils.save_text(catalog_path, catalog)
    _utils.convert_catalog(catalog_path)


def update_dictionary(
    repository: StrictNestedDictionary,
    module: str,
    language: str,
    domain: str,
    data: Mapping[str, JSONInput],
    fmt: TranslationFileFormat | None = None,
) -> None:
    """
    Updates the translation dictionary for a given language and domain.

    This function saves the provided translation dictionary to the specified .json file.

    :param repository: The data structure representing the translation repository.
    :type repository: StrictNestedDictionary
    :param module: The module path.
    :type module: str
    :param language: The language code.
    :type language: str
    :param domain: The domain name.
    :type domain: str
    :param data: The new translation dictionary.
    :type data: Mapping[str, JSONInput]
    """

    _utils.check_domains(repository, module, [domain])
    path = build_path(
        repository[["paths", "repository"]],
        module,
        I18N_TOOLS_LOCALE,
        language,
        I18N_TOOLS_MESSAGES,
    )
    dictionary_path = _utils.build_dictionary_path(path, domain, fmt)
    _fmt = _utils.validate_translation_format(fmt)
    dictionary = _utils.load_by_format(dictionary_path, _fmt)

    if not check_json_integrity(data):
        raise ValueError(
            f"The dictionary {data} is not compatible with i18n-tools translations"
        )

    merged: dict[str, JSONInput] = {**dictionary, **data}

    _utils.save_by_format(dictionary_path, merged, _fmt)


def dump_dictionary(
    repository: StrictNestedDictionary,
    module: str,
    language: str,
    domain: str,
    data: Mapping[str, JSONInput],
    fmt: TranslationFileFormat | None = None,
) -> None:
    """
    Dump the translation dictionary for a given language and domain.

    This function saves the provided translation dictionary to the specified .json file.

    :param repository: The data structure representing the translation repository.
    :type repository: StrictNestedDictionary
    :param module: The module path.
    :type module: str
    :param language: The language code.
    :type language: str
    :param domain: The domain name.
    :type domain: str
    :param data: The new translation dictionary.
    :type data: Mapping[str, JSONInput]
    """

    _utils.check_domains(repository, module, [domain])
    path = build_path(
        repository[["paths", "repository"]],
        module,
        I18N_TOOLS_LOCALE,
        language,
        I18N_TOOLS_MESSAGES,
    )
    dictionary_path = _utils.build_dictionary_path(path, domain, fmt)
    _fmt = _utils.validate_translation_format(fmt)

    if not check_json_integrity(data):
        raise ValueError(
            f"The dictionary {data} is not compatible with i18n-tools translations"
        )

    _utils.save_by_format(dictionary_path, data, _fmt)


# Delete operations


def remove_template(
    repository: StrictNestedDictionary, module: str, domain: str
) -> None:
    """
    Removes a template file for a given domain in the specified module.

    This function deletes the specified template file if it exists.

    :param repository: The data structure representing the translation repository.
    :type repository: StrictNestedDictionary
    :param module: The module path.
    :type module: str
    :param domain: The domain name.
    :type domain: str
    :raises FileNotFoundError: If the template file does not exist.
    """

    _utils.check_domains(repository, module, [domain])
    path = build_path(
        repository[["paths", "repository"]],
        module,
        I18N_TOOLS_LOCALE,
        I18N_TOOLS_TEMPLATE,
    )
    template_path = path + f"/{domain}.pot"
    _utils.remove_file(template_path)


def remove_catalog(
    repository: StrictNestedDictionary, module: str, language: str, domain: str
) -> None:
    """
    Removes a translation catalog and its corresponding machine file for a given language and domain in the specified module.

    This function deletes the specified .po and .mo files if they exist.

    :param repository: The data structure representing the translation repository.
    :type repository: StrictNestedDictionaryNestedDictionary
    :param module: The module path.
    :type module: str
    :param language: The language code.
    :type language: str
    :param domain: The domain name.
    :type domain: str
    :raises FileNotFoundError: If the catalog or machine file does not exist.
    """

    path = build_path(
        repository[["paths", "repository"]],
        module,
        I18N_TOOLS_LOCALE,
        language,
        I18N_TOOLS_MESSAGES,
    )
    catalog_path = path + f"/{domain}.po"
    machine_path = path + f"/{domain}.mo"
    _utils.remove_file(catalog_path)
    _utils.remove_file(machine_path)


def remove_dictionary(
    repository: StrictNestedDictionary,
    module: str,
    language: str,
    domain: str,
    fmt: TranslationFileFormat | None = None,
) -> None:
    """
    Removes a translation dictionary for a given language and domain in the specified module.

    This function deletes the specified .json file if it exists.

    :param repository: The data structure representing the translation repository.
    :type repository: StrictNestedDictionary
    :param module: The module path.
    :type module: str
    :param language: The language code.
    :type language: str
    :param domain: The domain name.
    :type domain: str
    :raises FileNotFoundError: If the dictionary file does not exist.
    """
    _utils.check_domains(repository, module, [domain])
    path = build_path(
        repository[["paths", "repository"]],
        module,
        I18N_TOOLS_LOCALE,
        language,
        I18N_TOOLS_MESSAGES,
    )
    dictionary_path = _utils.build_dictionary_path(path, domain, fmt)
    _utils.remove_file(dictionary_path)


# Managing configuration files


def load_config(config_path: str | None = None) -> dict[str, JSONValue]:
    """
    Load the configuration file (YAML, TOML, or JSON) from the application directories
    (not from the package i18n-tools) and return its contents as a dictionary.

    :param config_path: Optional path to the configuration file. If None, it searches \
    for it in the root of the application.
    :raises FileNotFoundError: If no configuration file is found in the application directories.
    :raises ValueError: If the file format is unsupported.
    :raises Exception: For other errors during loading.
    """

    # Si le chemin de configuration est fourni, utiliser ce chemin
    if config_path:
        if not _utils.exist_path(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        return _settings.load_config_file(config_path)

    # Sinon, rechercher dans les répertoires applicatifs (racine et répertoires locaux)
    search_dirs = [
        Path.cwd(),  # Répertoire racine de l'application
        Path.cwd() / I18N_TOOLS_LOCALE,  # Sous-répertoire locales de l'application
        Path.cwd()
        / I18N_TOOLS_LOCALE
        / I18N_TOOLS_CONFIG,  # Sous-répertoire configuration
    ]

    possible_files = ["i18n-tools.yaml", "i18n-tools.toml", "i18n-tools.json"]

    # Recherche dans les répertoires définis
    for directory in search_dirs:
        for file_name in possible_files:
            config_file_path = directory / file_name
            if config_file_path.exists():
                return _settings.load_config_file(config_file_path)

    raise FileNotFoundError(
        "No configuration file found in the application directories (root or locales)."
    )


def save_config(file_path: str, data: Mapping[str, JSONInput]) -> None:
    """
    Save configuration data to a file.

    Supports JSON, YAML, and TOML formats.

    :param file_path: Path to the configuration file.
    :param data: The dictionary containing configuration data.
    """

    _settings.save_config_file(file_path, data)


def build_translation_lang_files(
    repository: StrictNestedDictionary,
    module: str,
    domain: str,
    lang: str,
    fmt: TranslationFileFormat | None = None,
) -> tuple[str, str, str]:
    """
    Build from repository TLD, path for translation files

    :param repository: The data structure which represents the repository information.
    :type repository: StrictNestedDictionary
    :param module: Module name
    :type module: str
    :param domain: Domain name
    :type domain: str
    :param lang: language code
    :type lang: str
    :param fmt: Translation file format
    :type fmt: TranslationFileFormat | None
    :return: a tuple of a file path
    """
    _fmt = _utils.validate_translation_format(fmt)
    repository_path = repository[["paths", "repository"]]
    normalized_lang = normalize_language_tag(lang)
    lang_path = build_path(
        repository_path, module, I18N_TOOLS_LOCALE, normalized_lang, I18N_TOOLS_MESSAGES
    )
    json_file_path = lang_path + f"/{domain}.{_fmt}.{I18N_TOOLS_TRANSLATION_FILE_EXT}"
    po_file_path = lang_path + f"/{domain}.po"
    pot_file = (
        build_path(repository_path, module, I18N_TOOLS_LOCALE, I18N_TOOLS_TEMPLATE)
        + f"/{domain}.pot"
    )

    return json_file_path, po_file_path, pot_file


def verify_paths_and_modules(repository: StrictNestedDictionary) -> None:
    """
    Verify that the repository paths and modules exist.

    This function checks if the base path is absolute and if all specified modules
    and their corresponding paths exist in the repository.

    :param repository: The data structure which represents the repository information.
    :raises ValueError: If the base path is not an absolute path.
    :raises FileNotFoundError: If any module path does not exist.
    """

    repository_path = repository[["paths", "repository"]]

    if not _utils.is_absolute_path(repository_path):
        raise ValueError(
            f"The repository_path must be an absolute path: {repository[['paths', 'repository']]}"
        )

    for module in repository[["paths", "modules"]]:
        module_path = repository_path + "/" + module + "/" + "locales"
        if not file_exists(module_path):
            raise FileNotFoundError(f"The module path does not exist: {module_path}")


def verify_available_languages(
    repository: StrictNestedDictionary, languages: list[str]
) -> None:
    """
    Verify that languages in translation sets are registered in the repository.

    :param repository: The data structure which represents the repository information.
    :type repository: dict[str, Any].
    :param languages: languages in translation set.
    :type languages: list[str].
    :return: Nothing
    :rtype: None
    :raises ValueError: If any language does not exist in allowed languages.
    """
    for language in languages:
        if language not in get_all_languages(repository[["languages", "hierarchy"]]):
            raise ValueError(
                f"The language {language} is not registered in the repository"
            )


def _verify_target_module(
    repository: StrictNestedDictionary, target_module: str
) -> None:
    """
    Verify that a target module is registered in the repository.

    :param repository: The data structure which represents the repository information.
    :type repository: dict[str, Any].
    :param target_module: module where translation should be located.
    :type target_module: str.
    :return: Nothing
    :rtype: None
    :raises ValueError: If any module is not registered in the repository.
    """
    if target_module not in repository[["paths", "modules"]]:
        raise ValueError(
            f"The target module {target_module} is not registered in the repository"
        )


def verify_target_domain(
    repository: StrictNestedDictionary, target_module: str, target_domain: str
) -> None:
    """
    Verify that a target domain is registered in the repository.

    :param repository: The data structure which represents the repository information.
    :type repository: dict[str, Any].
    :param target_module: module where translation should be located.
    :type target_module: str.
    :param target_domain: domain of translation.
    :type target_domain: str.
    :return: Nothing
    :rtype: None
    :raises ValueError: If the target module or the target domain is not
                         registered in the repository.
    """
    _verify_target_module(repository, target_module)
    if target_domain not in repository[["domains", target_module]]:
        raise ValueError(
            f"The target domain '{target_domain}' is not registered in the repository"
        )


# ---------------------------------------------------------------------------
# Low-level operations offered to loader.py
#
# loader.py reaches the low-level layer only through this module. Each
# function below delegates to _utils for now; this is where checks on these
# operations belong once they exist.
# ---------------------------------------------------------------------------


def path_exists(path: Path | str) -> bool:
    """Return whether a file or directory exists at ``path``."""
    return _utils.exist_path(path)


def create_empty_file(file_path: Path | str) -> None:
    """Create an empty file at ``file_path``."""
    _utils.create_empty_file(file_path)


def create_empty_json(file_path: Path | str) -> None:
    """Create a JSON file holding an empty object at ``file_path``."""
    _utils.create_empty_json(file_path)


def load_text(file_path: Path | str) -> Catalog:
    """Load a catalog from a PO file."""
    return _utils.load_text(file_path)


def detect_format(path: Path | str) -> TranslationFileFormat:
    """Detect the serialisation format of a file from its extension."""
    return _utils.detect_format(path)


def load_json(file_path: Path | str) -> dict[str, JSONValue]:
    """Load a JSON file and return its content."""
    return _utils.load_json(file_path)


def save_json(file_path: Path | str, data: Mapping[str, JSONInput]) -> None:
    """Save a dictionary to a JSON file."""
    _utils.save_json(file_path, data)


def load_by_format(
    file_path: Path | str, fmt: TranslationFileFormat
) -> dict[str, JSONValue]:
    """Load a dictionary file in the given format (json|yaml)."""
    return _utils.load_by_format(file_path, fmt)


def save_by_format(
    file_path: Path | str, data: Mapping[str, JSONInput], fmt: TranslationFileFormat
) -> None:
    """Save a dictionary to a file in the given format (json|yaml)."""
    _utils.save_by_format(file_path, data, fmt)


def build_dictionary_path(
    base_path: Path | str, domain: str, fmt: TranslationFileFormat | None
) -> str:
    """Build a dictionary file path from a base directory, a domain and a format."""
    return _utils.build_dictionary_path(base_path, domain, fmt)


def create_gzip(file_path: Path | str) -> None:
    """Write a gzip-compressed copy of ``file_path``."""
    _utils.create_gzip(file_path)


def non_traversal_path(
    root_path: str, module_list: list[str], members: list[tarfile.TarInfo]
) -> list[tarfile.TarInfo]:
    """Keep the archive members that extract inside the expected module paths."""
    return _utils.non_traversal_path(root_path, module_list, members)


def check_module(repository: StrictNestedDictionary, module_list: list[str]) -> None:
    """Raise if a module of ``module_list`` is not defined in the repository."""
    _utils.check_module(repository, module_list)


def check_domains(
    repository: StrictNestedDictionary, module: str, domain_list: list[str]
) -> None:
    """Raise if a domain of ``domain_list`` is not defined for ``module``."""
    _utils.check_domains(repository, module, domain_list)
