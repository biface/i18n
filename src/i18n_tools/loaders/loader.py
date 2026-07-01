"""
This module handles the file operations necessary for internationalization
(i18n) tools. It focuses on loading and saving configuration files,
managing `.pot` files for translation projects, and orchestrating
repository-wide operations (scaffolding, archiving, aggregation, and
translation-set CRUD).

**Key Features:**
    - Load and save configuration files in YAML, TOML, or JSON formats.
    - Search for configuration files in application directories.
    - Load and save `.pot` files, including metadata headers and translation entries.
    - Build, verify, archive, and restore a whole repository.
    - Add, update, remove, and aggregate translation sets across modules,
      domains, and languages.

`loader.py` is the sole bridge between `/models/` and the rest of
`/loaders/` (DD-06, DD-NN). `handler.py` and `utils.py` must never be
imported directly from `/models/` — models talk only to this module,
which can in turn be used standalone (returning raw dicts, no model
objects required) or together with model instances (e.g. ``Book``,
``Repository``).
"""

import tarfile
from pathlib import Path
from typing import Any

from ndict_tools import StrictNestedDictionary

from i18n_tools.__static__ import (
    I18N_TOOLS_BACKUP,
    I18N_TOOLS_CONFIG,
    I18N_TOOLS_LOCALE,
    I18N_TOOLS_MESSAGES,
    I18N_TOOLS_TEMPLATE,
)
from i18n_tools.loaders.handler import (
    _verify_available_languages,
    _verify_paths_and_modules,
    _verify_target_domain,
)
from i18n_tools.loaders.handler import build_book_filename as _build_book_filename
from i18n_tools.loaders.handler import (
    build_path,
    build_translation_lang_files,
    check_json_integrity,
    create_catalog,
    create_dictionary,
    create_directory,
    create_template,
    dump_dictionary,
    fetch_dictionary,
)
from i18n_tools.loaders.handler import file_exists as _file_exists
from i18n_tools.loaders.handler import is_absolute_path as _is_absolute_path
from i18n_tools.loaders.handler import (
    normalize_module_identifier as _normalize_module_identifier,
)
from i18n_tools.loaders.handler import (
    update_dictionary,
)
from i18n_tools.loaders.utils import (
    _build_dictionary_path,
    _check_domains,
    _check_module,
    _create_gzip,
    _detect_format,
    _exist_path,
    _load_by_format,
    _load_json,
    _non_traversal_path,
    _save_by_format,
    _save_json,
)
from i18n_tools.locale import get_all_languages


def load_locale_json(file_path: str) -> dict[str, Any]:
    """
    This function load a JSON file in the locales repository and containing i18next data. The structure of this
    dictionary is as follows::

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


def load_book(file_path: str) -> dict[str, Any]:
    """
    Load a .i18t dictionary file and return its contents as a filtered dict (DD-15, DD-16, DD-34).

    The serialisation format is detected from the file extension (DD-34),
    symmetrically to :func:`save_book`. The reserved keys ``.i18n_tools``
    and ``metadata`` are silently ignored.

    :param file_path: Path to the .i18t translation file.
    :type file_path: str
    :return: Mapping of msgid to i18n_tools entry dict
             ``{"messages": matrix, "metadata": {}}``.
    :rtype: dict[str, Any]
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
    data: dict[str, Any] = {"metadata": book.metadata.to_dict()}
    for msg in book.messages.values():
        # load_locale_json / check_json_integrity expect each entry to be
        # the raw messages matrix (a list of lists), not the full
        # {"messages": ..., "metadata": ...} dict produced by
        # message_to_i18n_tools_format.  We extract only the "messages" key.
        data[msg.id] = message_to_i18n_tools_format(msg)["messages"]
    _save_by_format(file_path, data, fmt)


def aggregate_locale_json(
    structure: dict[str, Any],
    domains: dict[str, list[str]],
    languages: dict[str, list[str]],
) -> dict[str, Any]:
    """
    Aggregate JSON locale files based on the given structure, domains, and languages.

    Distinct from :func:`aggregate_dictionaries`: this function works from
    generic, caller-supplied parameters (no ``Repository`` instance, no
    embedded metadata) and reads files directly from disk by path. Kept
    alongside it as a separate, legitimate responsibility — not a
    duplicate (DD-NN, #69).

    :param structure: Dictionary containing 'base' path and list of 'modules'.
    :type structure: dict[str, Any]
    :param domains: Dictionary where keys are module names and values are lists of domains.
    :type domains: dict[str, list[str]]
    :param languages: Dictionary where keys are language codes and values are lists of regional variants.
    :type languages: dict[str, list[str]]
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


def save_locale_json(file_path: str, data: dict[str, Any]) -> None:
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
    aggregated_data: dict[str, Any], base_path: str
) -> None:
    """
    Save the aggregated locale JSON data as gzipped files for each domain in the locales directory,
    and create a gzipped file for the entire module or sub-module at the base of its directory.

    Companion to :func:`aggregate_locale_json` — see that function's
    docstring for why it is kept distinct from :func:`aggregate_dictionaries`
    (DD-NN, #69).

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


def build_book_filename(domain: str, fmt: str | None = None) -> tuple[str, str]:
    """
    Pass-through to :func:`i18n_tools.loaders.handler.build_book_filename`.

    Kept here so that `Book` (`models/corpus.py`) only ever talks to
    `loader.py`, consistent with the existing `load_book`/`save_book`
    pattern (DD-06, DD-08) — never directly to `handler.py`.

    :param domain: The translation domain name.
    :type domain: str
    :param fmt: The desired storage format ("json" or "yaml"). Defaults to
                "json" if ``None``.
    :type fmt: str | None
    :return: A ``(format, filename)`` tuple.
    :rtype: tuple[str, str]
    :raises ValueError: If ``fmt`` is not a recognised translation format.
    """
    return _build_book_filename(domain, fmt)


def file_exists(file_path: str) -> bool:
    """
    Pass-through to :func:`i18n_tools.loaders.handler.file_exists`.

    Kept here so that `Repository` (`models/repository.py`) only ever talks
    to `loader.py`, consistent with the `build_book_filename` pattern
    (DD-06, DD-NN) — never directly to `handler.py`.

    :param file_path: The path to check.
    :type file_path: str
    :return: True if the path exists, False otherwise.
    :rtype: bool
    """
    return _file_exists(file_path)


def is_absolute_path(path: str) -> bool:
    """
    Pass-through to :func:`i18n_tools.loaders.handler.is_absolute_path`.

    Kept here so that `Repository` (`models/repository.py`) only ever talks
    to `loader.py`, consistent with the `build_book_filename` pattern
    (DD-06, DD-NN) — never directly to `handler.py`.

    :param path: The path to check.
    :type path: str
    :return: True if the path is absolute, False otherwise.
    :rtype: bool
    """
    return _is_absolute_path(path)


def normalize_module_identifier(path: str) -> str:
    """
    Pass-through to :func:`i18n_tools.loaders.handler.normalize_module_identifier`.

    Kept here so that `Repository` (`models/repository.py`) only ever talks
    to `loader.py`, consistent with the `build_book_filename` pattern
    (DD-06, DD-NN) — never directly to `handler.py`.

    :param path: A module identifier or an absolute file-system path.
    :type path: str
    :return: The normalized module identifier.
    :rtype: str
    """
    return _normalize_module_identifier(path)


def _update_json_translations(
    existing_translations: dict[str, Any], translation_data: dict[str, Any]
):
    """
    Update translations in JSON with new data.

    This function merges new translation data into the existing translations.
    If a message ID already exists, it extends the existing translations with the new data.

    :param existing_translations: Dictionary of existing translations.
    :param translation_data: Dictionary of new translation data to be merged.
    :return: Updated dictionary of translations.
    """
    for msgid, msgstr_list in translation_data.items():
        existing_translations[msgid] = msgstr_list
    return existing_translations


def create_module_archive(
    repository: StrictNestedDictionary, module: str, archive_name: str
) -> None:
    """
    Create a tar.gz archive of a module's contents, including all subdirectories and files,
    by identifying the top-level module from the given module/package path.

    :param repository: The data structure which represents the repository information.
    :type repository: StrictNestedDictionary
    :param module: The module or module/package path (e.g., "mod-1/pkg-1").
    :type module: str
    :param archive_name: The name of the archive file.
    :type archive_name: str
    :return: Nothing
    :rtype: None
    """

    # Identify the top-level module from the given module path
    # This is done by splitting the module path and taking the first part
    # For example, if module is "mod-1/pkg-1", top_level_module will be "mod-1"
    top_level_module = module.split("/")[0]

    # Build the path to backup directory as <
    archive_path = build_path(repository[["paths", "repository"]], top_level_module)

    # Construct the full path to the top-level module
    # This is the directory that will be archived
    backup_path = build_path(
        repository[["paths", "repository"]],
        top_level_module,
        I18N_TOOLS_LOCALE,
        I18N_TOOLS_CONFIG,
        I18N_TOOLS_BACKUP,
    )

    # Construct the path for the archive file
    # The archive will be created in the root_path directory with the given archive_name
    archive = backup_path + f"/{archive_name}.tar.gz"

    # Open the archive file in write mode with gzip compression
    with tarfile.open(archive, "w:gz") as tar:
        # Add the top-level module to the archive
        # The arcname parameter ensures that the directory structure is preserved in the archive
        # This means the archive will contain the top-level module directory and all its contents
        tar.add(archive_path, arcname=top_level_module)


def restore_module_from_archive(
    repository: StrictNestedDictionary, module: str, archive_name: str
) -> None:
    """
    Restore a module's contents from a tar.gz archive.

    :param repository: The data structure which represents the repository information.
    :type repository: StrictNestedDictionary
    :param module: The module or submodule path (e.g., "mod-1/pkg-1").
    :type module: str
    :param archive_name: The name of the archive file.
    :type archive_name: str
    """

    # Split the module path to get the top-level module
    module_parts = module.split("/")
    top_level_module = module_parts[0]

    # Construct the path for the archive file
    archive_path = (
        build_path(
            repository[["paths", "repository"]],
            top_level_module,
            I18N_TOOLS_LOCALE,
            I18N_TOOLS_CONFIG,
            I18N_TOOLS_BACKUP,
        )
        + f"/{archive_name}.tar.gz"
    )

    # Check if the archive file exists
    if _exist_path(archive_path):
        # Open the archive file in read mode with gzip compression
        with tarfile.open(archive_path, "r:gz") as tar:
            # Extract all members that are safe to extract
            tar.extractall(
                path=repository[["paths", "repository"]],
                members=_non_traversal_path(
                    repository[["paths", "repository"]],
                    [top_level_module],
                    tar.getmembers(),
                ),
            )
    else:
        # Raise an error if the archive file does not exist
        raise FileNotFoundError(f"Archive file '{archive_path}' not found.")


def build_repository(repository: StrictNestedDictionary) -> None:
    """
    This function builds the repository from the modulee and populates files in the repository directory respectively
    to domains and language registered in the repository. It checks the existence of already existing files and only creates
    the necessary files and directories.

    :param repository: The data structure which represents the repository information.
    :type repository: StrictNestedDictionary
    :return: Nothing
    :type: None
    """
    # Get the list of modules from the repository
    modules = repository[["paths", "modules"]]

    # Get the list of languages from the repository
    languages = get_all_languages(repository[["languages", "hierarchy"]])

    # Iterate through each module
    for module in modules:
        # Get the list of domains for this module
        domains = repository[["domains", module]]

        module_directory = (
            repository[["paths", "repository"]] + "/" + module + "/" + I18N_TOOLS_LOCALE
        )
        module_template_directory = module_directory + "/" + I18N_TOOLS_TEMPLATE

        if not _exist_path(module_template_directory):
            create_directory(module_template_directory)

        # Iterate through each domain
        for domain in domains:
            try:
                # Create a template for this module and domain
                create_template(repository, module, domain)
            except FileExistsError:
                # Skip if the template already exists
                pass

            # Iterate through each language
            for language in languages:

                language_directory = (
                    module_directory + "/" + language + "/" + I18N_TOOLS_MESSAGES
                )

                if not _file_exists(language_directory):
                    create_directory(language_directory)

                try:
                    # Create a catalog for this module, language, and domain
                    create_catalog(repository, module, language, domain)
                except FileExistsError:
                    # Skip if the catalog already exists
                    pass

                try:
                    # Create a dictionary for this module, language, and domain
                    create_dictionary(repository, module, language, domain)
                except FileExistsError:
                    # Skip if the dictionary already exists
                    pass


def verify_repository(repository: StrictNestedDictionary) -> bool:
    """
    Verifies that the translation repository is properly constructed.
    Checks the existence of required directories and files for each module, domain, and language.

    :param repository: The data structure which represents the repository information.
    :type repository: StrictNestedDictionary
    :return: True if the repository is properly constructed, False otherwise.
    :rtype: bool
    """
    try:
        # Get the list of modules from the repository
        modules = repository[["paths", "modules"]]

        # Validate modules
        if not _check_module(repository, modules):
            return False

        # Get the list of languages from the repository
        languages = get_all_languages(repository[["languages", "hierarchy"]])

        if not languages:
            return False

        # Check each module
        for module in modules:
            # Validate domains for this module
            domains = repository[["domains", module]]
            if not _check_domains(repository, module, domains):
                return False

            # Check module directory structure
            module_directory = build_path(
                repository[["paths", "repository"]], module, I18N_TOOLS_LOCALE
            )
            if not _exist_path(module_directory):
                return False

            # Check template directory
            module_template_directory = build_path(
                module_directory, I18N_TOOLS_TEMPLATE
            )
            if not _exist_path(module_template_directory):
                return False

            # Check each domain
            for domain in domains:
                # Check template file
                template_path = build_path(module_template_directory, f"{domain}.pot")
                if not _exist_path(template_path):
                    return False

                # Check each language
                for language in languages:
                    # Check language directory
                    language_directory = build_path(
                        module_directory, language, I18N_TOOLS_MESSAGES
                    )
                    if not _exist_path(language_directory):
                        return False

                    # Check catalog file
                    catalog_path = build_path(language_directory, f"{domain}.po")
                    if not _exist_path(catalog_path):
                        return False

                    # Check dictionary file (default json for backward compatibility)
                    dictionary_path = _build_dictionary_path(
                        language_directory, domain, None
                    )
                    if not _exist_path(dictionary_path):
                        return False

        # All checks passed
        return True

    except Exception:
        return False


def aggregate_dictionaries(
    repository: StrictNestedDictionary, module: str, domain: str
) -> None:
    """
    This function aggregates all dictionaries for a given module and domain into a single JSON file.

    :param repository: The data structure which represents the repository information.
    :type repository: StrictNestedDictionary
    :param module: module where translation should be located.
    :type module: str
    :param domain: domain of translation.
    :type domain: str
    :return: Nothing
    :rtype: None
    :raises Exception: If any error occurs during the aggregation.
    """

    languages = get_all_languages(repository[["languages", "hierarchy"]])
    domain_dictionary = {"metadata": repository["details"].to_dict()}

    for language in languages:
        try:
            domain_dictionary[language] = fetch_dictionary(
                repository, module, language, domain
            )
        except Exception as e:
            raise e

    module_directory = build_path(
        repository[["paths", "repository"]], module, I18N_TOOLS_LOCALE
    )
    _save_json(module_directory + f"/{domain}_aggregated.json", domain_dictionary)
    _create_gzip(module_directory + f"/{domain}_aggregated.json")


def add_translation_set(
    repository: StrictNestedDictionary,
    module: str,
    domain: str,
    translations: dict[str, Any],
):
    """
    Adds a translation set to the translation repository using JSON and PO files.

    This function verifies the repository structure, updates the translation files
    for each module, domain, and language, and ensures that the translations conform
    to the languages defined in the repository.

    :param repository: The data structure which represents the repository information.
    :type repository: StrictNestedDictionary
    :param module: Module where should be located domain of translations.
    :type module: str
    :param domain: The domain of the translation set.
    :type domain: str
    :param translations: Dictionary containing the translations to be added.
    :raises ValueError: If the repository path is not absolute or if a language is not supported.
    :raises FileNotFoundError: If any module path does not exist.
    """
    # Verifying components
    _verify_paths_and_modules(repository)
    _verify_available_languages(repository, list(translations.keys()))
    _verify_target_domain(repository, module, domain)

    for lang, translation_data in translations.items():

        json_file_path, po_file_path, pot_file_path = build_translation_lang_files(
            repository, module, domain, lang
        )

        # Load existing translations
        existing_translations = (
            fetch_dictionary(repository, module, lang, domain)
            if _file_exists(json_file_path)
            else {}
        )
        existing_translations = _update_json_translations(
            existing_translations, translation_data
        )
        update_dictionary(repository, module, lang, domain, existing_translations)

        # BLOCKED (v0.3.x) — update_catalog() incompatible with the i18n-tools format.
        # The native .i18t matrix (messages/plurals/alternatives) does not match
        # the msgid/msgstr structure expected by Babel. See backlog C-09.


def update_translation_set(
    repository: StrictNestedDictionary,
    module: str,
    domain: str,
    translations: dict[str, Any],
):
    """
    Updates existing translations in the translation repository using JSON and PO files.

    This function verifies the repository structure, updates the translation files
    for each module, domain, and language, and ensures that the translations conform
    to the languages defined in the repository.

    :param repository: The data structure which represents the repository information.
    :type repository: StrictNestedDictionary
    :param module: Module where the translation domain should be located.
    :type module: str
    :param domain: The domain of the translation set.
    :type domain: str
    :param translations: Dictionary containing the translations to be updated.
    :raises ValueError: If the repository path is not absolute or if a language is not supported.
    :raises FileNotFoundError: If any module path does not exist.
    :raises KeyError: If a msgid to be updated does not exist in the current translations.
    """
    # Verify components
    _verify_paths_and_modules(repository)
    _verify_available_languages(repository, list(translations.keys()))
    _verify_target_domain(repository, module, domain)

    for lang, translation_data in translations.items():

        json_file_path, po_file_path, pot_file_path = build_translation_lang_files(
            repository, module, domain, lang
        )
        # Load existing translations
        existing_translations = (
            fetch_dictionary(repository, module, lang, domain)
            if _file_exists(json_file_path)
            else {}
        )

        # Update existing translations
        for msgid, new_translations in translation_data.items():
            if msgid not in existing_translations:
                raise KeyError(
                    f"msgid '{msgid}' does not exist in the current translations for language '{lang}'."
                )
            # Replace or extend existing translations
            existing_translations[msgid] = new_translations

        update_dictionary(repository, module, lang, domain, existing_translations)
        # update_catalog(repository, module, lang, domain, existing_translations)


def remove_translation_set(
    repository: StrictNestedDictionary,
    module: str,
    domain: str,
    translations: dict[str, Any],
):
    """
    Removes specified translations from the translation repository using JSON and PO files.

    This function verifies the repository structure, removes the specified translations
    from the translation files for each module, domain, and language, and ensures that
    the translations conform to the languages defined in the repository.

    :param repository: The data structure which represents the repository information.
    :type repository: StrictNestedDictionary
    :param module: Module where the translation domain should be located.
    :type module: str
    :param domain: The domain of the translation set.
    :type domain: str
    :param translations: Dictionary containing the translations to be removed.
    :raises ValueError: If the repository path is not absolute or if a language is not supported.
    :raises FileNotFoundError: If any module path does not exist.
    """
    # Verify components
    _verify_paths_and_modules(repository)
    _verify_available_languages(repository, list(translations.keys()))
    _verify_target_domain(repository, module, domain)

    for lang, msgids in translations.items():

        json_file_path, po_file_path, pot_file_path = build_translation_lang_files(
            repository, module, domain, lang
        )

        # Load existing translations
        existing_translations = (
            fetch_dictionary(repository, module, lang, domain)
            if _file_exists(json_file_path)
            else {}
        )

        # Remove specified translations
        for msgid, options in msgids.items():
            if msgid in existing_translations:
                del existing_translations[msgid]

        dump_dictionary(repository, module, lang, domain, existing_translations)
        # BLOCKED (v0.3.x) — update_catalog() incompatible with the i18n-tools format.
        # The native .i18t matrix (messages/plurals/alternatives) does not match
        # the msgid/msgstr structure expected by Babel. See backlog C-09.
