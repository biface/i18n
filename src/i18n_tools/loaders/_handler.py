"""
This module handles the manipulation of files within the repository using utils.py. It calculates paths, controls file names and access, and retrieves data contained in translation files.

Key Responsibilities:
    - Manipulate files within the repository.
    - Calculate paths, control file names and access.
    - Retrieve data from translation files.

"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, TypeGuard

from babel import __version__ as babel_version
from babel.core import Locale
from ndict_tools import StrictNestedDictionary

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
from ..locale import (
    get_all_languages,
    is_valid_language_tag,
    language_family,
    language_script,
    normalize_language_tag,
)
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


def check_json_integrity(data: dict[str, Any]) -> bool:
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
# Integrity of a Book file
# -----------------------------------------------------------------------------

# Root metadata keys of a Book file whose value is a string, then all known keys.
_ROOT_TEXT_KEYS = frozenset(
    {
        "project_id_version",
        "report_msgid_bugs_to",
        "pot_creation_date",
        "language_team",
        "header_comment",
    }
)
_ROOT_KNOWN_KEYS = _ROOT_TEXT_KEYS | {"language", "domain", "statistics", "count"}

# Entry metadata keys whose value is a string or a list of strings, then all
# known keys.
_ENTRY_TEXT_KEYS = frozenset({"version", "language", "context"})
_ENTRY_TEXT_LIST_KEYS = frozenset({"flags", "user_comments", "auto_comments"})
_ENTRY_KNOWN_KEYS = (
    _ENTRY_TEXT_KEYS
    | _ENTRY_TEXT_LIST_KEYS
    | {
        "locations",
        "singular_count",
        "plural_counts",
    }
)

ROOT = "root"
"""``where`` value of a finding about the root of the file."""


@dataclass(frozen=True)
class Finding:
    """
    One anomaly found in the content of a Book file.

    :ivar severity: ``"error"`` makes the file unusable; ``"warning"``
        reports a point the user has to look at, the file still loads.
    :ivar where: ``ROOT`` or the identifier of the message entry.
    :ivar message: What is wrong, in plain words.
    """

    severity: Literal["error", "warning"]
    where: str
    message: str


def _is_int(value: object) -> bool:
    """Tell whether ``value`` is an int and not a bool."""
    return isinstance(value, int) and not isinstance(value, bool)


def _is_text_list(value: object) -> bool:
    """Tell whether ``value`` is a list of strings."""
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _is_location(value: object) -> bool:
    """Tell whether ``value`` is a ``[file, line]`` pair, line >= 1."""
    if not isinstance(value, list) or len(value) != 2:
        return False
    file, line = value
    return isinstance(file, str) and _is_int(line) and line >= 1


def _describe_script(tag: str) -> str:
    """Describe the script of ``tag``, stating whether it is explicit."""
    script, explicit = language_script(tag)
    if script is None:
        return "unknown script"
    return f"{script} ({'explicit' if explicit else 'inferred'})"


def _check_language(
    value: object, expected: str | None, where: str, findings: list[Finding]
) -> None:
    """
    Compare a language read from the file with the expected one.

    An absent or empty language is accepted. A different language of the
    same family is a warning, a different family an error.
    """
    if value is None or value == "":
        return
    if not isinstance(value, str):
        findings.append(Finding("error", where, "language is not a string"))
        return
    if not is_valid_language_tag(value):
        findings.append(Finding("error", where, f"invalid language tag '{value}'"))
        return
    if expected is None:
        return
    found = normalize_language_tag(value)
    if found == expected:
        return
    if language_family(found) != language_family(expected):
        findings.append(
            Finding(
                "error",
                where,
                f"language '{found}' is not of the family of '{expected}'",
            )
        )
        return
    message = f"language '{found}' differs from '{expected}' (same family)"
    if language_script(found)[0] != language_script(expected)[0]:
        message += (
            f"; scripts differ: {_describe_script(found)}"
            f" vs {_describe_script(expected)}"
        )
    findings.append(Finding("warning", where, message))


def _is_text_matrix(matrix: list[list[object]]) -> TypeGuard[list[list[str]]]:
    """Tell whether every cell of a well-formed matrix is a string."""
    return all(isinstance(cell, str) for row in matrix for cell in row)


def _check_counts(
    matrix: list[list[str]], metadata: dict[str, object], where: str
) -> list[Finding]:
    """
    Compare the stored counters of an entry with its matrix.

    ``singular_count`` is the number of declensions (the length of the
    singular row); ``plural_counts[i]`` the number of non-empty plurals of
    declension ``i``. A mismatch is a warning: the counters are recomputed.
    """
    findings: list[Finding] = []
    singular_count = len(matrix[0])
    plural_counts = [
        sum(1 for row in matrix[1:] if row[column] != "")
        for column in range(singular_count)
    ]
    if "singular_count" in metadata:
        stored = metadata["singular_count"]
        if not _is_int(stored):
            findings.append(Finding("error", where, "singular_count is not an int"))
        elif stored != singular_count:
            findings.append(
                Finding(
                    "warning",
                    where,
                    f"singular_count is {stored}, the matrix has {singular_count}",
                )
            )
    if "plural_counts" in metadata:
        stored = metadata["plural_counts"]
        if not isinstance(stored, list) or not all(_is_int(n) for n in stored):
            findings.append(
                Finding("error", where, "plural_counts is not a list of int")
            )
        elif stored != plural_counts:
            findings.append(
                Finding(
                    "warning",
                    where,
                    f"plural_counts is {stored}, the matrix has {plural_counts}",
                )
            )
    return findings


def _check_entry_metadata(
    metadata: dict[str, object], expected_language: str | None, where: str
) -> list[Finding]:
    """Check the types of the known keys of an entry metadata."""
    findings: list[Finding] = []
    for key, value in metadata.items():
        if key == "language":
            _check_language(value, expected_language, where, findings)
        elif key in _ENTRY_TEXT_KEYS:
            if not isinstance(value, str):
                findings.append(Finding("error", where, f"{key} is not a string"))
        elif key in _ENTRY_TEXT_LIST_KEYS:
            if not _is_text_list(value):
                findings.append(
                    Finding("error", where, f"{key} is not a list of strings")
                )
        elif key == "locations":
            if not isinstance(value, list) or not all(
                _is_location(item) for item in value
            ):
                findings.append(
                    Finding(
                        "error",
                        where,
                        "locations is not a list of [file, line] pairs",
                    )
                )
        elif key not in _ENTRY_KNOWN_KEYS:
            findings.append(
                Finding("warning", where, f"unknown metadata key '{key}' ignored")
            )
    return findings


def _count_words(matrix: list[list[str]]) -> int:
    """Count the whitespace-separated words of every cell of a matrix."""
    return sum(len(cell.split()) for row in matrix for cell in row)


def _check_root(
    root: object,
    language: str | None,
    domain: str | None,
    total_messages: int,
    total_words: int,
) -> list[Finding]:
    """Check the root metadata of a Book file."""
    if not isinstance(root, dict):
        return [Finding("error", ROOT, "metadata is not a mapping")]
    findings: list[Finding] = []
    for key, value in root.items():
        if key == "language":
            _check_language(value, language, ROOT, findings)
        elif key == "domain":
            if value is None or value == "":
                continue
            if not isinstance(value, str):
                findings.append(Finding("error", ROOT, "domain is not a string"))
            elif domain is not None and value != domain:
                findings.append(
                    Finding("error", ROOT, f"domain '{value}' is not '{domain}'")
                )
        elif key in _ROOT_TEXT_KEYS:
            if not isinstance(value, str):
                findings.append(Finding("error", ROOT, f"{key} is not a string"))
        elif key == "statistics":
            expected = {"total_messages": total_messages, "total_words": total_words}
            if value != expected:
                findings.append(
                    Finding(
                        "warning",
                        ROOT,
                        f"statistics are {value}, the content gives {expected}",
                    )
                )
        elif key == "count":
            expected_count = {"messages": total_messages}
            if value != expected_count:
                findings.append(
                    Finding(
                        "warning",
                        ROOT,
                        f"count is {value}, the content gives {expected_count}",
                    )
                )
        elif key not in _ROOT_KNOWN_KEYS:
            findings.append(
                Finding("warning", ROOT, f"unknown metadata key '{key}' kept")
            )
    return findings


def inspect_book_data(
    data: dict[str, object], language: str | None = None, domain: str | None = None
) -> list[Finding]:
    """
    Check the content of a Book file and list what is wrong with it.

    Every entry other than the reserved ``.i18n_tools`` and ``metadata``
    keys is a native entry ``{"messages": matrix, "metadata": {...}}`` or
    a bare matrix (legacy form).

    Errors: malformed matrix or non-string cell, wrong type of a known
    metadata value, invalid language tag, a language of another family
    than ``language``, a domain other than ``domain``.

    Warnings: a language of the same family as ``language`` but different
    (with the scripts when they differ), counters or statistics that do
    not match the content, unknown metadata keys (kept at the root,
    ignored in an entry).

    An absent or empty language or domain is accepted.

    :param data: The content of the file, as read.
    :type data: dict[str, object]
    :param language: The normalized language expected, or None to skip
        the comparison.
    :type language: str | None
    :param domain: The domain expected, or None to skip the comparison.
    :type domain: str | None
    :return: The findings, errors and warnings, in file order.
    :rtype: list[Finding]
    """
    findings: list[Finding] = []
    total_messages = 0
    total_words = 0
    for where, value in data.items():
        if where in (".i18n_tools", "metadata"):
            continue
        total_messages += 1
        metadata: object = {}
        if isinstance(value, dict):
            if "messages" not in value:
                findings.append(Finding("error", where, "no messages matrix"))
                continue
            matrix: object = value["messages"]
            metadata = value.get("metadata", {})
        else:
            matrix = value
        if not _check_matrix(matrix):
            findings.append(Finding("error", where, "malformed messages matrix"))
            continue
        if not _is_text_matrix(matrix):
            findings.append(Finding("error", where, "a matrix cell is not a string"))
            continue
        total_words += _count_words(matrix)
        if not isinstance(metadata, dict):
            findings.append(Finding("error", where, "metadata is not a mapping"))
            continue
        entry_metadata: dict[str, object] = {
            str(key): item for key, item in metadata.items()
        }
        findings.extend(_check_entry_metadata(entry_metadata, language, where))
        findings.extend(_check_counts(matrix, entry_metadata, where))
    if "metadata" in data:
        findings.extend(
            _check_root(data["metadata"], language, domain, total_messages, total_words)
        )
    return findings


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
    format default/validation consistent across its constructor and its
    `add_format()`/`update_format()` methods, and reusable from `core.py`,
    `sync.py`, or a future CLI without constructing a `Book` first.

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
) -> dict[str, Any]:
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
    :rtype: dict[str, Any]
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
    data: dict[Any, dict[str, str]],
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
    :type data: Dict[str, Dict[str, str]]
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
    data: dict[str, Any],
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
    :type data: dict[str, Any]
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

    for key, item in data.items():
        dictionary[key] = item

    _utils.save_by_format(dictionary_path, dictionary, _fmt)


def dump_dictionary(
    repository: StrictNestedDictionary,
    module: str,
    language: str,
    domain: str,
    data: dict[str, Any],
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
    :type data: dict[str, Any]
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


def load_config(config_path: str | None = None) -> dict[str, Any]:
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


def save_config(file_path: str, data: dict[str, Any]) -> None:
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


def load_json(file_path: Path | str) -> dict[str, Any]:
    """Load a JSON file and return its content."""
    return _utils.load_json(file_path)


def save_json(file_path: Path | str, data: dict[str, Any]) -> None:
    """Save a dictionary to a JSON file."""
    _utils.save_json(file_path, data)


def load_by_format(file_path: Path | str, fmt: TranslationFileFormat) -> dict[str, Any]:
    """Load a dictionary file in the given format (json|yaml)."""
    return _utils.load_by_format(file_path, fmt)


def save_by_format(
    file_path: Path | str, data: dict[str, Any], fmt: TranslationFileFormat
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
