"""
This module handles the file operations necessary for internationalization
(i18n) tools. It focuses on loading and saving configuration files and
managing `.pot` files for translation projects.

**Key Features:**
    - Load and save configuration files in YAML, TOML, or JSON formats.
    - Search for configuration files in application directories.
    - Load and save `.pot` files, including metadata headers and translation entries.

"""

from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

from i18n_tools.loaders.handler import build_book_filename as _build_book_filename
from i18n_tools.loaders.handler import check_json_integrity
from i18n_tools.loaders.utils import (
    _create_gzip,
    _detect_format,
    _load_by_format,
    _load_json,
    _save_by_format,
    _save_json,
)


def load_locale_json(file_path: str) -> Dict[str, Any]:
    """
    This function load a JSON file in the locales repository and containing i18next data. The structure of this
    dictionary is as follows:

        {
            "msgid_001": [
                    ["msgstr_001_000", "msgstr_001_001"],
                    ["msgplr_001_1_000", "msgplr_001_1_001"],
                    ["msgplr_001_2_000", "msgplr_001_2_001"]
                ],
            "msgid_002": [
                    ["msgstr_002_000"],
                    ["msgplr_002_1_000"],
                    ["msgplr_002_2_000"]
                ]
        }

    :param file_path: Path to the JSON locale file.
    :type file_path: str
    :return: JSON locale data content.
    :rtype: dict
    :raises FileNotFoundError: If the file is not found.
    :raises ValueError: If the file is not a valid JSON or fails the integrity check.
    """
    data = _load_json(file_path)
    if not check_json_integrity(data):
        raise ValueError(f"Integrity check failed for file: {file_path}")
    return data


def load_book(file_path: str) -> Dict[str, Any]:
    """
    Load a .i18t dictionary file and return its contents as a filtered dict (DD-15, DD-16, DD-34).

    The serialisation format is detected from the file extension (DD-34),
    symmetrically to :func:`save_book`. The reserved keys ``.i18n_tools``
    and ``metadata`` are silently ignored.

    :param file_path: Path to the .i18t translation file.
    :type file_path: str
    :return: Mapping of msgid to i18n_tools entry dict
             ``{"messages": matrix, "metadata": {}}``.
    :rtype: Dict[str, Any]
    :raises FileNotFoundError: If the file does not exist.
    :raises ValueError: If the file fails the integrity check.
    """
    fmt = _detect_format(file_path)
    data = _load_by_format(file_path, fmt)
    if not check_json_integrity(data):
        raise ValueError(f"Integrity check failed for file: {file_path}")
    result = {}
    for msgid, matrix in data.items():
        if msgid in (".i18n_tools", "metadata"):
            continue
        result[msgid] = {"messages": matrix, "metadata": {}}
    return result


def save_book(book: Any, file_path: str) -> None:
    """
    Serialize a Book to a .i18t file.

    The serialisation format (JSON or YAML) is detected from the file
    extension. The structure written to disk follows the native .i18t format::

        {
            "metadata": { ... },
            "<msgid>": { "messages": [...], "metadata": { ... } },
            ...
        }

    :param book: The Book instance to persist.
    :type book: Book
    :param file_path: Full path (directory + filename) of the target .i18t file.
    :type file_path: str
    :raises FileNotFoundError: If the parent directory does not exist.

    References
    ----------
    - biface/i18n#42 : strict separation models / loaders (DD-06)
    - biface/i18n#46 : loader ↔ models bridge and native serialisation (DD-15, DD-16)
    - biface/i18n#56 : .i18t naming convention and format detection (DD-34)
    - biface/i18n#57 : Book.save() persistence
    """
    from i18n_tools.converter import message_to_i18n_tools_format

    fmt = _detect_format(file_path)
    data: Dict[str, Any] = {"metadata": book.metadata.to_dict()}
    for msg in book.messages.values():
        # load_locale_json / check_json_integrity expect each entry to be
        # the raw messages matrix (a list of lists), not the full
        # {"messages": ..., "metadata": ...} dict produced by
        # message_to_i18n_tools_format.  We extract only the "messages" key.
        data[msg.id] = message_to_i18n_tools_format(msg)["messages"]
    _save_by_format(file_path, data, fmt)


def aggregate_locale_json(
    structure: Dict[str, Any],
    domains: Dict[str, List[str]],
    languages: Dict[str, List[str]],
) -> Dict[str, Any]:
    """
    Aggregate JSON locale files based on the given structure, domains, and languages.

    :param structure: Dictionary containing 'base' path and list of 'modules'.
    :type structure: Dict[str, Any]
    :param domains: Dictionary where keys are module names and values are lists of domains.
    :type domains: Dict[str, List[str]]
    :param languages: Dictionary where keys are language codes and values are lists of regional variants.
    :type languages: Dict[str, List[str]]
    :return: A consolidated dictionary of locale data.
    :rtype: dict
    """
    aggregated_data = {}
    base_path = Path(structure["base"])
    modules = structure["modules"]

    for module in modules:
        module_path = base_path / module / "locales"
        module_data = {}

        for domain in domains.get(module, []):
            domain_data = {}

            for lang, variants in languages.items():
                # Include the main language in the list of variants
                all_variants = [lang] + variants

                for variant in all_variants:
                    file_path = module_path / variant / f"{domain}.json"

                    if file_path.exists():
                        data = load_locale_json(file_path)
                        domain_data[variant] = data

            module_data[domain] = domain_data

        aggregated_data[module] = module_data

    return aggregated_data


def save_locale_json(file_path: str, data: Dict[str, Any]) -> None:
    """
    Save data to a JSON locale file.

    :param file_path: Path to the JSON locale file.
    :type file_path: str
    :param data: Dictionary containing locale data.
    :type data: dict
    :raises FileNotFoundError: If the directory for the file is not found.
    """
    _save_json(file_path, data)


def save_aggregated_locale_json(
    aggregated_data: Dict[str, Any], base_path: str
) -> None:
    """
    Save the aggregated locale JSON data as gzipped files for each domain in the locales directory,
    and create a gzipped file for the entire module or sub-module at the base of its directory.

    :param aggregated_data: The aggregated dictionary of locale data.
    :type aggregated_data: dict
    :param base_path: The base path where the locales directories are located.
    :type base_path: str
    """
    for module, module_data in aggregated_data.items():
        # Handle sub-modules by splitting the module key
        module_parts = module.split("/")
        module_name = module_parts[-1]
        module_dir = Path(base_path) / "/".join(module_parts)

        locales_path = module_dir / "locales"
        locales_path.mkdir(parents=True, exist_ok=True)

        # Save individual domain files
        for domain, domain_data in module_data.items():
            json_file_path = locales_path / f"{domain}.json"
            _save_json(json_file_path, domain_data)
            _create_gzip(json_file_path)
            json_file_path.unlink()

        # Save aggregated module data
        module_json_path = module_dir / f"{module_name}.json"
        _save_json(module_json_path, module_data)
        _create_gzip(module_json_path)
        module_json_path.unlink()


def build_book_filename(domain: str, fmt: Union[str, None] = None) -> Tuple[str, str]:
    """
    Pass-through to :func:`i18n_tools.loaders.handler.build_book_filename`.

    Kept here so that `Book` (`models/corpus.py`) only ever talks to
    `loader.py`, consistent with the existing `load_book`/`save_book`
    pattern (DD-06, DD-08) — never directly to `handler.py`.

    :param domain: The translation domain name.
    :type domain: str
    :param fmt: The desired storage format ("json" or "yaml"). Defaults to
                "json" if ``None``.
    :type fmt: Union[str, None]
    :return: A ``(format, filename)`` tuple.
    :rtype: Tuple[str, str]
    :raises ValueError: If ``fmt`` is not a recognised translation format.
    """
    return _build_book_filename(domain, fmt)
