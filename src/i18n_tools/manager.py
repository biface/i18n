from pathlib import Path
from typing import Any, Dict, Set, Tuple

from polib import POEntry, POFile

from i18n_tools.loader import (
    file_exists,
    load_locale_json,
    load_locale_po,
    save_locale_json,
    save_locale_po,
)
from i18n_tools.locale import get_all_languages, normalize_language_tag


def _translation_lang_files(
    repository: Dict[str, Any], module: str, domain: str, lang: str
) -> Tuple[Path, Path]:
    """
    Build from repository TLD, path for .po files

    :param repository: Dictionary containing the base path and list of modules
    :type repository: Dict[str, Any]
    :param module: Module name
    :type module: str
    :param domain: Domain name
    :type domain: str
    :param lang: language code
    :type lang: str
    :return: a tuple of file path
    """
    repository_path = Path(repository["base"])
    normalized_lang = normalize_language_tag(lang)
    lang_path = repository_path / module / "locales" / normalized_lang / "LC_MESSAGES"
    lang_path.mkdir(parents=True, exist_ok=True)

    json_file_path = lang_path / f"{domain}.json"
    po_file_path = lang_path / f"{domain}.po"

    return json_file_path, po_file_path


def _verify_paths_and_modules(repository: Dict[str, Any]):
    """
    Verify that the repository paths and modules exist.

    This function checks if the base path is absolute and if all specified modules
    and their corresponding paths exist in the repository.
    :param repository: Dictionary containing the base path and list of modules.
    :raises ValueError: If the base path is not an absolute path.
    :raises FileNotFoundError: If any module path does not exist.
    """
    repository_path = Path(repository["base"])
    if not repository_path.is_absolute():
        raise ValueError(
            f"The repository_path must be an absolute path: {repository_path}"
        )

    for module in repository["modules"]:
        module_path = repository_path / module / "locales"
        if not file_exists(module_path):
            raise FileNotFoundError(f"The module path does not exist: {module_path}")


def _verify_available_languages(
    repository: Dict[str, Any], languages: list[str]
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
        if language not in get_all_languages(repository["languages"]):
            raise ValueError(
                f"The language {language} is not registered in the repository"
            )


def _verify_target_module(repository: Dict[str, Any], target_module: str) -> None:
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
    if target_module not in repository["modules"]:
        raise ValueError(
            f"The target module {target_module} is not registered in the repository"
        )


def _verify_target_domain(
    repository: Dict[str, Any], target_module: str, target_domain: str
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
        if target_domain not in repository["domains"][target_module]:
            raise ValueError(
                f"The target domain {target_domain} is not registered in the repository"
            )
    except ValueError as e:
        raise ValueError(
            f"The target module {target_module} is not registered in the repository"
        ) from e


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
        if msgid in existing_translations:
            for i, msgstr in enumerate(msgstr_list):
                if i < len(existing_translations[msgid]):
                    existing_translations[msgid][i].extend(msgstr)
                else:
                    existing_translations[msgid].append(msgstr)
        else:
            existing_translations[msgid] = msgstr_list
    return existing_translations


def _create_po_entry(
    msgid: str, msgid_plural: str, msgstr: str, msgstr_plural: Dict[int, str] = None
) -> POEntry:
    """
    Create a POEntry with the given parameters.

    This function creates a POEntry object with the specified msgid, msgid_plural, msgstr,
    and optionally msgstr_plural.

    :param msgid: The message ID.
    :type msgid: str
    :param msgid_plural: The plural form of the message ID.
    :param msgstr: The singular translation string.
    :type msgstr: str
    :param msgstr_plural: Optional dictionary of plural translation strings.
    :type msgstr_plural: Dict[int, str]
    :return: A POEntry object with the specified parameters.
    :rtype: POEntry
    """
    po_entry = POEntry(msgid=msgid, msgstr=msgstr)
    if msgstr_plural:
        msgstr_plural[0] = msgstr
        po_entry.msgid_plural = msgid_plural
        po_entry.msgstr_plural = msgstr_plural
    return po_entry


def _update_po_translations(po_file: POFile, translations: Dict):
    """
    Update translations in a PO file with new data.

    This function updates the PO file with new translation data.
    It handles both singular and plural forms of translations.

    :param po_file: The POFile object to be updated.
    :param translations: Dictionary of translations to be added or updated.
    """
    for msgid, msgs_list in translations.items():
        msgstr_list = msgs_list[0]
        msgplr_list = msgs_list[1:]
        if len(msgstr_list) == 1:
            msgid_full = msgid
            msgid_plural = f"{msgid_full}_plr"
            msgstr = msgstr_list[0]
            entry = po_file.find(msgid_full)

            if len(msgplr_list) >= 1:
                msgstr_plural = {
                    i: msgs_list[i][0] for i in range(1, len(msgplr_list) + 1)
                }
                if entry:
                    msgstr_plural[0] = msgstr
                    entry.msgstr_plural = msgstr_plural
                else:
                    po_entry = _create_po_entry(
                        msgid_full, msgid_plural, msgstr_list[0], msgstr_plural
                    )
                    po_file.append(po_entry)
            else:
                if entry:
                    entry.msgstr = msgstr
                else:
                    po_entry = _create_po_entry(msgid_full, msgid_plural, msgstr)
                    po_file.append(po_entry)
        else:
            for index, msgstr in enumerate(msgstr_list):
                msgid_full = f"{msgid}_{index:03d}"
                msgid_plural = f"{msgid_full}_plr"
                entry = po_file.find(msgid_full)

                if len(msgplr_list) >= 1:
                    msgstr_plural = {
                        i: msgs_list[i][index] for i in range(1, len(msgplr_list) + 1)
                    }
                    if entry:
                        msgstr_plural[0] = msgstr
                        entry.msgstr_plural = msgstr_plural
                    else:
                        po_entry = _create_po_entry(
                            msgid_full, msgid_plural, msgstr, msgstr_plural
                        )
                        po_file.append(po_entry)
                else:
                    if entry:
                        entry.msgstr = msgstr
                    else:
                        po_entry = _create_po_entry(msgid_full, msgid_plural, msgstr)
                        po_file.append(po_entry)


def _remove_po_translations(po_file: POFile, msgids_to_remove: Set[Tuple[str, int]]):
    """
    Remove specified translations from a PO file.

    This function removes the specified msgids from the PO file, including those with options and indices.

    :param po_file: The POFile object to be updated.
    :type po_file: POFile
    :param msgids_to_remove: A set of base msgids with or without options to be removed from the PO file.
    :type msgids_to_remove: Set[Tuple[str, int]]
    :return: Nothing
    :rtype: None
    """
    entries_to_remove = []
    for msgid, options in msgids_to_remove:
        if options > 1:
            for index in range(0, options):
                entries_to_remove.append(f"{msgid}_{index:03d}")
        else:
            entries_to_remove.append(msgid)

    for entry in entries_to_remove:
        po_file.remove(po_file.find(entry))


def add_translation_set(
    repository: Dict[str, Any], module: str, domain: str, translations: Dict
):
    """
    Adds a translation set to the translation repository using JSON and PO files.

    This function verifies the repository structure, updates the translation files
    for each module, domain, and language, and ensures that the translations conform
    to the languages defined in the repository.

    :param repository: Dictionary containing the base path, modules, domains, and languages.
    :type repository: Dict[str, Any]
    :param module: Module where should be located domain of translations.
    :type module: str
    :param domain: The domain of the translation set.
    :type domain: str
    :param translations: Dictionary containing the translations to be added.
    :raises ValueError: If the repository path is not absolute or if a language is not supported.
    :raises FileNotFoundError: If any module path does not exist.
    """
    # verifying components
    _verify_paths_and_modules(repository)
    _verify_available_languages(repository, list(translations.keys()))
    _verify_target_domain(repository, module, domain)

    for lang, translation_data in translations.items():

        json_file_path, po_file_path = _translation_lang_files(
            repository, module, domain, lang
        )

        # Load existing translations
        existing_translations = (
            load_locale_json(str(json_file_path)) if json_file_path.exists() else {}
        )
        existing_translations = _update_json_translations(
            existing_translations, translation_data
        )
        save_locale_json(str(json_file_path), existing_translations)

        # Load existing PO file
        po_file = (
            load_locale_po(str(po_file_path)) if po_file_path.exists() else POFile()
        )
        _update_po_translations(po_file, existing_translations)
        save_locale_po(str(po_file_path), po_file)


def update_translation_set(
    repository: Dict[str, Any], module: str, domain: str, translations: Dict
):
    """
    Updates existing translations in the translation repository using JSON and PO files.

    This function verifies the repository structure, updates the translation files
    for each module, domain, and language, and ensures that the translations conform
    to the languages defined in the repository.

    :param repository: Dictionary containing the base path, modules, domains, and languages.
    :type repository: Dict[str, Any]
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

        json_file_path, po_file_path = _translation_lang_files(
            repository, module, domain, lang
        )

        # Load existing translations
        existing_translations = (
            load_locale_json(str(json_file_path)) if json_file_path.exists() else {}
        )

        # Update existing translations
        for msgid, new_translations in translation_data.items():
            if msgid not in existing_translations:
                raise KeyError(
                    f"msgid '{msgid}' does not exist in the current translations for language '{lang}'."
                )
            # Replace or extend existing translations
            existing_translations[msgid] = new_translations

        save_locale_json(str(json_file_path), existing_translations)

        # Load existing PO file
        po_file = (
            load_locale_po(str(po_file_path)) if po_file_path.exists() else POFile()
        )
        _update_po_translations(po_file, existing_translations)
        save_locale_po(str(po_file_path), po_file)


def remove_translation_set(
    repository: Dict[str, Any], module: str, domain: str, translations: Dict
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

        json_file_path, po_file_path = _translation_lang_files(
            repository, module, domain, lang
        )

        # Load existing translations
        existing_translations = (
            load_locale_json(str(json_file_path)) if json_file_path.exists() else {}
        )

        # Remove specified translations
        for msgid, options in msgids.items():
            if msgid in existing_translations:
                del existing_translations[msgid]

        save_locale_json(str(json_file_path), existing_translations)

        # Load existing PO file
        po_file = (
            load_locale_po(str(po_file_path)) if po_file_path.exists() else POFile()
        )

        # Remove specified translations from PO file
        msgids_to_remove = {
            (msgid, len(options[0])) for msgid, options in msgids.items()
        }
        _remove_po_translations(po_file, msgids_to_remove)
        save_locale_po(str(po_file_path), po_file)
