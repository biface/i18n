from pathlib import Path
from typing import Any, Dict

from polib import POEntry, POFile

from i18n_tools.loader import (
    load_locale_json,
    load_locale_po,
    save_locale_json,
    save_locale_po,
)
from i18n_tools.locale import get_all_languages, normalize_language_tag


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
        if not module_path.exists():
            raise FileNotFoundError(f"The module path does not exist: {module_path}")


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


def add_translation_set(repository: Dict[str, Any], translations: Dict):
    #FIXME : Working on add translation in target domain.
    """
    Adds a translation set to the translation repository using JSON and PO files.

    This function verifies the repository structure, updates the translation files
    for each module, domain, and language, and ensures that the translations conform
    to the languages defined in the repository.

    :param repository: Dictionary containing the base path, modules, domains, and languages.
    :param translations: Dictionary containing the translations to be added.
    :raises ValueError: If the repository path is not absolute or if a language is not supported.
    :raises FileNotFoundError: If any module path does not exist.
    """
    _verify_paths_and_modules(repository)

    repository_path = Path(repository["base"])
    all_languages = get_all_languages(repository["languages"])

    for lang, translation_data in translations.items():
        if lang not in all_languages:
            raise ValueError(f"Language '{lang}' is not supported in the repository.")

        normalized_lang = normalize_language_tag(lang)
        for module in repository["modules"]:
            for domain in repository["domains"][module]:
                lang_path = (
                    repository_path
                    / module
                    / "locales"
                    / normalized_lang
                    / "LC_MESSAGES"
                )
                lang_path.mkdir(parents=True, exist_ok=True)

                json_file_path = lang_path / f"{domain}.json"
                po_file_path = lang_path / f"{domain}.po"

                # Load existing translations
                existing_translations = (
                    load_locale_json(str(json_file_path))
                    if json_file_path.exists()
                    else {}
                )
                existing_translations = _update_json_translations(
                    existing_translations, translation_data
                )
                save_locale_json(str(json_file_path), existing_translations)

                # Load existing PO file
                po_file = (
                    load_locale_po(str(po_file_path))
                    if po_file_path.exists()
                    else POFile()
                )
                _update_po_translations(po_file, existing_translations)
                save_locale_po(str(po_file_path), po_file)


# TODO : add update and remove and check missing translations both in json and po files
