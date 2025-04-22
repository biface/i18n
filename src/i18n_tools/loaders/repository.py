from __future__ import annotations

import tarfile
from typing import Tuple, Dict

from ndict_tools import NestedDictionary

from i18n_tools.__static__ import (
    I18N_TOOLS_BACKUP,
    I18N_TOOLS_CONFIG,
    I18N_TOOLS_LOCALE,
    I18N_TOOLS_MESSAGES,
    I18N_TOOLS_TEMPLATE,
)
from i18n_tools.locale import get_all_languages, normalize_language_tag

from .handler import (
    build_path,
    create_catalog,
    create_dictionary,
    create_directory,
    create_template,
    fetch_dictionary,
    file_exists, update_dictionary, update_catalog, dump_dictionary, dump_catalog
)
from .utils import _exist_path, _is_absolute_path, _non_traversal_path, _check_module, _check_domains, _save_json, _create_gzip


def _translation_lang_files(
    repository: NestedDictionary, module: str, domain: str, lang: str
) -> Tuple[str, str, str]:
    """
    Build from repository TLD, path for translation files

    :param repository: The data structure containing the repository information.
    :type repository: NestedDictionary
    :param module: Module name
    :type module: str
    :param domain: Domain name
    :type domain: str
    :param lang: language code
    :type lang: str
    :return: a tuple of a file path
    """
    repository_path = repository[["paths", "repository"]]
    normalized_lang = normalize_language_tag(lang)
    lang_path = build_path(repository_path, module, I18N_TOOLS_LOCALE, normalized_lang, I18N_TOOLS_MESSAGES)
    json_file_path = lang_path + f"/{domain}.json"
    po_file_path = lang_path + f"/{domain}.po"
    pot_file = build_path(repository_path, module, I18N_TOOLS_LOCALE, I18N_TOOLS_TEMPLATE) + f"/{domain}.pot"

    return json_file_path, po_file_path, pot_file


def _verify_paths_and_modules(repository: NestedDictionary) -> None:
    """
    Verify that the repository paths and modules exist.

    This function checks if the base path is absolute and if all specified modules
    and their corresponding paths exist in the repository.
    :param repository: The data structure containing the repository information.
    :raises ValueError: If the base path is not an absolute path.
    :raises FileNotFoundError: If any module path does not exist.
    """

    repository_path = repository[["paths", "repository"]]

    if not _is_absolute_path(repository_path):
        raise ValueError(
            f"The repository_path must be an absolute path: {repository[['paths', 'repository']]}"
        )

    for module in repository[["paths", "modules"]]:
        module_path = repository_path + "/" + module + "/" + "locales"
        if not file_exists(module_path):
            raise FileNotFoundError(f"The module path does not exist: {module_path}")


def _verify_available_languages(
    repository: NestedDictionary, languages: list[str]
) -> None:
    """
    Verify that languages in translation set are registered in the repository
    :param repository: Dictionary containing the base path and list of modules.
    :type repository: Dict[str, Any].
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


def _verify_target_module(repository: NestedDictionary, target_module: str) -> None:
    """
    Verify that target module is registered in the repository
    :param repository: Dictionary containing the base path and list of modules.
    :type repository: Dict[str, Any].
    :param target_module: module where translation should be located.
    :type target_module: str.
    :return: Nothing
    :rtype: None
    :raises ValueError: If any module is not registered in the repository.
    """
    if target_module not in repository[["paths","modules"]]:
        raise ValueError(
            f"The target module {target_module} is not registered in the repository"
        )


def _verify_target_domain(
    repository: NestedDictionary, target_module: str, target_domain: str
) -> None:
    """
    Verify that target domain is registered in the repository
    :param repository: Dictionary containing the base path and list of modules.
    :type repository: Dict[str, Any].
    :param target_module: module where translation should be located.
    :type target_module: str.
    :param target_domain: domain of translation.
    :type target_domain: str.
    :return: Nothing
    :rtype: None
    :raises ValueError: If any domain is not registered in the repository.
    """
    try:
        _verify_target_module(repository, target_module)
        if target_domain not in repository[["domains", target_module]]:
            raise IndexError(
                f"The target domain '{target_domain}' is not registered in the repository"
            )
    except IndexError as e:
        raise e
    except Exception as e:
        raise ValueError(
            f"The target module '{target_module}' is not registered in the repository"
        )

def _update_json_translations(existing_translations: Dict, translation_data: Dict):
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
    repository: NestedDictionary, module: str, archive_name: str
) -> None:
    """
    Create a tar.gz archive of a module's contents, including all subdirectories and files,
    by identifying the top-level module from the given module/package path.

    :param repository: The data representing the repository..
    :type repository: NestedDictionary
    :param module: The module or module/package path (e.g., "mod-1/pkg-1").
    :type module: str
    :param archive_name: The name of the archive file.
    :type archive_name: str
    :return: None
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
    repository: NestedDictionary, module: str, archive_name: str
) -> None:
    """
    Restore a module's contents from a tar.gz archive.

    :param repository: The data representing the repository.
    :type repository: NestedDictionary
    :param module: The module or sub-module path (e.g., "mod-1/pkg-1").
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


def build_repository(repository: NestedDictionary) -> None:
    """
    This function builds the repository from the modulee and populates files in the repository directory respectively
    to domains and language registered in the repository. It checks existence of already existing files and only creates
    the necessary files and directories.

    :param repository: The data representing the repository.
    :type repository: NestedDictionary
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

                if not file_exists(language_directory):
                    print(f"Creating directory {language_directory}")
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


def verify_repository(repository: NestedDictionary) -> bool:
    """
    Verifies that the translation repository is properly constructed.
    Checks the existence of required directories and files for each module, domain, and language.

    :param repository: The data representing the repository.
    :type repository: NestedDictionary
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
            module_directory = build_path(repository[["paths", "repository"]], module, I18N_TOOLS_LOCALE)
            if not _exist_path(module_directory):
                return False

            # Check template directory
            module_template_directory = build_path(module_directory, I18N_TOOLS_TEMPLATE)
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
                    language_directory = build_path(module_directory, language, I18N_TOOLS_MESSAGES)
                    if not _exist_path(language_directory):
                        return False

                    # Check catalog file
                    catalog_path = build_path(language_directory, f"{domain}.po")
                    if not _exist_path(catalog_path):
                        return False

                    # Check dictionary file
                    dictionary_path = build_path(language_directory, f"{domain}.json")
                    if not _exist_path(dictionary_path):
                        return False

        # All checks passed
        return True

    except Exception as e:
        print(f"Error verifying repository: {str(e)}")
        return False

def aggregate_dictionaries(repository: NestedDictionary, module: str, domain: str) -> None:
    """
    This function aggregates all dictionaries for a given module and domain into a single JSON file.
    :param repository:
    :param module:
    :param domain:
    :return:
    """

    languages = get_all_languages(repository[["languages", "hierarchy"]])
    domain_dictionary = {".i18n_tools": repository["details"].to_dict()}

    for language in languages:
        try:
            domain_dictionary[language] = fetch_dictionary(repository, module, language, domain)
        except Exception as e:
            raise e

    module_directory = build_path(repository[["paths", "repository"]], module, I18N_TOOLS_LOCALE)
    _save_json(module_directory + f"/{domain}.json", domain_dictionary)
    _create_gzip(module_directory + f"/{domain}.json")





def add_translation_set(
    repository: NestedDictionary, module: str, domain: str, translations: Dict
):
    """
    Adds a translation set to the translation repository using JSON and PO files.

    This function verifies the repository structure, updates the translation files
    for each module, domain, and language, and ensures that the translations conform
    to the languages defined in the repository.

    :param repository: The data structure containing the repository information.
    :type repository: NestedDictionary
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

        json_file_path, po_file_path, pot_file_path = _translation_lang_files(
            repository, module, domain, lang
        )

        # Load existing translations
        existing_translations = fetch_dictionary(repository, module, lang, domain) if file_exists(json_file_path) else {}
        existing_translations = _update_json_translations(existing_translations, translation_data)
        update_dictionary(repository, module, lang, domain, existing_translations)

        # Load existing PO file
        # update_catalog(repository, module, lang, domain, existing_translations)


def update_translation_set(
    repository: NestedDictionary, module: str, domain: str, translations: Dict
):
    """
    Updates existing translations in the translation repository using JSON and PO files.

    This function verifies the repository structure, updates the translation files
    for each module, domain, and language, and ensures that the translations conform
    to the languages defined in the repository.

    :param repository: The data structure containing the repository information.
    :type repository: NestedDictionary
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

        json_file_path, po_file_path, pot_file_path = _translation_lang_files(
            repository, module, domain, lang
        )

        # Load existing translations
        existing_translations = fetch_dictionary(repository, module, lang, domain) if file_exists(json_file_path) else {}

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
    repository: NestedDictionary, module: str, domain: str, translations: Dict
):
    """
    Removes specified translations from the translation repository using JSON and PO files.

    This function verifies the repository structure, removes the specified translations
    from the translation files for each module, domain, and language, and ensures that
    the translations conform to the languages defined in the repository.

    :param repository: Dictionary containing the base path, modules, domains, and languages.
    :type repository: Dict[str, Any]
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

        json_file_path, po_file_path, pot_file_path = _translation_lang_files(
            repository, module, domain, lang
        )

        # Load existing translations
        existing_translations = fetch_dictionary(repository, module, lang, domain) if file_exists(json_file_path) else {}

        # Remove specified translations
        for msgid, options in msgids.items():
            if msgid in existing_translations:
                print(f"Removing translation for msgid '{msgid}' in language '{lang}'")
                del existing_translations[msgid]

        print(f"Existing translations: {existing_translations}")
        dump_dictionary(repository, module, lang, domain, existing_translations)
        # update_catalog(repository, module, lang, domain, existing_translations)
