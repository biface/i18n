"""
Converter Module
================

This module provides functions to manipulate and convert internationalization
(i18n) data between different formats. It includes utilities for generating
headers for `.pot` files, converting data between various i18n formats
(i18n_tools, i18n, i18next, and Babel), and creating deterministic message IDs.

**Key Features:**

    - Convert between PO/POT files (Babel format) and i18next JSON format.
    - Convert between i18n_tools dictionary format and other formats.
    - Provide a unified format that works across different i18n libraries.
    - Generate deterministic message IDs using weights and base values.
    - Create metadata headers for `.pot` files, including author and team
      information.

**Usage Examples:**

1. Convert a PO file to i18next JSON format:

   ```python
   from i18n_tools.converter import load_and_convert_po_to_i18next

   i18next_data = load_and_convert_po_to_i18next('path/to/messages.po')
   ```

2. Convert i18next JSON to Babel Catalog format:

   ```python
   from i18n_tools.converter import convert_i18next_to_catalog

   catalog = convert_i18next_to_catalog(i18next_data, locale='en', domain='messages')
   ```

3. Convert between formats using the command-line interface:

   ```bash
   python -m i18n_tools.converter input.po output.json --input-format po --output-format json
   ```

**Format Descriptions:**

1. **Babel Catalog Format**: Used by the Babel library for PO/POT files. Stores translations
   with metadata, plural forms, and context information.

2. **i18next JSON Format**: Used by the i18next library. Typically a flat or nested JSON structure
   with keys as message IDs and values as translations. Supports plural forms with `_plural` suffix.

3. **i18n_tools Format**: A specialized JSON format used by i18n_tools. Stores translations as
   arrays of arrays, with the first array containing singular forms and subsequent arrays
   containing plural forms.

4. **Unified Format**: An intermediate format used internally by this module to facilitate
   conversion between other formats. Preserves all metadata, plural forms, and context information.

**License:**
This file is distributed under the `CeCILL-C Free Software License Agreement
<https://cecill.info/licences/Licence_CeCILL-C_V1-en.html>`_. By using or
modifying this file, you agree to abide by the terms of this license.

**Author(s):**
This module is authored and maintained as part of the i18n-tools package.

"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from babel.messages.catalog import Catalog, Message
from ndict_tools import NestedDictionary

from i18n_tools.loaders import (
    fetch_catalog,
    fetch_dictionary,
)
from i18n_tools.loaders.loader import (
    load_locale_json,
    load_locale_po,
    save_locale_json,
    save_locale_pot,
)
from i18n_tools.locale import get_all_languages


def _initialize_pot_file(file_path: str, domain: str, authors: Dict, language: str):
    """
    Initializes a .pot file with necessary metadata and entries for relevant authors.

    :param file_path: Path to the .pot file.
    :param domain: Domain of translation.
    :param authors: Dictionary of authors.
    :param language: Language code for the current .pot file.
    """
    # TODO To be removed

    pot_catalog = Catalog()
    now = datetime.now().strftime("%Y-%m-%d %H:%M%z")

    pot_catalog.project = "i18n-tools"
    pot_catalog.version = "1.0"
    pot_catalog.msgid_bugs_addr = ""
    pot_catalog.creation_date = now
    pot_catalog.revision_date = now
    pot_catalog.last_translator = f"FULL NAME <EMAIL@ADDRESS>"
    pot_catalog.language_team = f"{language} <LL@li.org>"
    pot_catalog.mime_version = "1.0"
    pot_catalog.content_type = "text/plain; charset=UTF-8"
    pot_catalog.content_transfer_encoding = "8bit"
    pot_catalog.fuzzy = False

    # Add entries for authors who can translate the specified language
    for author_id, author_info in authors.items():
        if language in author_info["languages"]:
            pot_catalog.add(
                id=f"Translation by {author_info['first_name']} {author_info['last_name']}",
                string="",
                locations=[(domain, 0)],
            )

    save_locale_pot(file_path, pot_catalog)


def populate_pot_files(config: Dict, domains: Dict, languages: Dict, authors: Dict):
    """
    Populates .pot files in the translation repository.

    :param config: Dictionary containing configuration with 'repository_path' and 'modules'.
    :param domains: Dictionary of translation domains.
    :param languages: Dictionary of translation languages.
    :param authors: Dictionary of authors.
    :raises ValueError: If repository_path is not an absolute path.
    """

    # TODO To be removed

    repository_path = Path(config["base"])

    # Verify that repository_path is an absolute path
    if not repository_path.is_absolute():
        raise ValueError(
            f"The repository_path must be an absolute path: {repository_path}"
        )

    # Flatten the language hierarchy to get a complete list of languages
    all_languages = get_all_languages(languages["hierarchy"])

    for module in config["modules"]:
        # Ensure the module exists in the domains dictionary
        if module in domains:
            module_path = repository_path / module
            locales_path = module_path / "locales"
            locales_path.mkdir(parents=True, exist_ok=True)

            for domain in domains[module]:
                for lang in all_languages:
                    lang_path = locales_path / lang / "LC_MESSAGES"
                    lang_path.mkdir(parents=True, exist_ok=True)

                    pot_file_path = lang_path / f"{domain}.pot"
                    _initialize_pot_file(str(pot_file_path), domain, authors, lang)


# Unified Format Conversion Functions


def catalog_to_unified_format(catalog: Catalog) -> Dict[str, Any]:
    """
    Convert a Babel Catalog to a unified format dictionary.

    The unified format is a dictionary with the following structure:
    {
        "message_id": {
            "translation": "translated text",
            "plural_forms": {
                "0": "singular form",
                "1": "plural form 1",
                "2": "plural form 2",
                ...
            },
            "context": "context information",
            "metadata": {
                "locations": [...],
                "flags": [...],
                "comments": [...],
                ...
            }
        },
        ...
    }

    :param catalog: Babel Catalog object
    :type catalog: Catalog
    :return: Dictionary in unified format
    :rtype: Dict[str, Any]
    """
    unified = {}

    for message in catalog:
        if not message.id:  # Skip header
            continue

        message_id = message.id
        if isinstance(message_id, tuple):
            # Handle plural forms
            singular = message_id[0]
            message_entry = {
                "translation": (
                    message.string
                    if isinstance(message.string, str)
                    else message.string[0]
                ),
                "plural_forms": {},
                "context": message.context or "",
                "metadata": {
                    "locations": [f"{loc[0]}:{loc[1]}" for loc in message.locations],
                    "flags": list(message.flags),
                    "comments": message.user_comments,
                    "auto_comments": message.auto_comments,
                },
            }

            # Add plural forms
            if isinstance(message.string, (tuple, list)):
                for i, form in enumerate(message.string):
                    message_entry["plural_forms"][str(i)] = form

            unified[singular] = message_entry
        else:
            # Handle singular forms
            unified[message_id] = {
                "translation": message.string,
                "plural_forms": {},
                "context": message.context or "",
                "metadata": {
                    "locations": [f"{loc[0]}:{loc[1]}" for loc in message.locations],
                    "flags": list(message.flags),
                    "comments": message.user_comments,
                    "auto_comments": message.auto_comments,
                },
            }

    return unified


def unified_format_to_catalog(
    unified: Dict[str, Any], locale: str = None, domain: str = None
) -> Catalog:
    """
    Convert a unified format dictionary to a Babel Catalog.

    :param unified: Dictionary in unified format
    :type unified: Dict[str, Any]
    :param locale: Locale for the catalog
    :type locale: str
    :param domain: Domain for the catalog
    :type domain: str
    :return: Babel Catalog object
    :rtype: Catalog
    """
    catalog = Catalog(locale=locale, domain=domain)

    for message_id, entry in unified.items():
        # Parse locations
        locations = []
        for loc_str in entry.get("metadata", {}).get("locations", []):
            if ":" in loc_str:
                file, line = loc_str.split(":", 1)
                try:
                    locations.append((file, int(line)))
                except ValueError:
                    locations.append((file, 0))
            else:
                locations.append((loc_str, 0))

        # Handle plural forms
        plural_forms = entry.get("plural_forms", {})
        if plural_forms:
            # Create a tuple of strings for plural forms
            plural_strings = []
            for i in range(len(plural_forms)):
                plural_strings.append(plural_forms.get(str(i), ""))

            # Create a tuple of message IDs (singular, plural)
            if isinstance(message_id, str):
                msg_id_tuple = (message_id, f"{message_id}_plural")
            else:
                msg_id_tuple = message_id

            catalog.add(
                id=msg_id_tuple,
                string=(
                    tuple(plural_strings)
                    if plural_strings
                    else entry.get("translation", "")
                ),
                locations=locations,
                flags=entry.get("metadata", {}).get("flags", []),
                user_comments=entry.get("metadata", {}).get("comments", []),
                auto_comments=entry.get("metadata", {}).get("auto_comments", []),
                context=entry.get("context", ""),
            )
        else:
            # Handle singular form
            catalog.add(
                id=message_id,
                string=entry.get("translation", ""),
                locations=locations,
                flags=entry.get("metadata", {}).get("flags", []),
                user_comments=entry.get("metadata", {}).get("comments", []),
                auto_comments=entry.get("metadata", {}).get("auto_comments", []),
                context=entry.get("context", ""),
            )

    return catalog


def i18next_to_unified_format(i18next_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert i18next JSON format to unified format.

    i18next format is typically:
    {
        "key1": "value1",
        "key2": "value2",
        "key3_plural": "plural value",
        "key3": "singular value",
        "nested": {
            "key": "nested value"
        }
    }

    :param i18next_data: Dictionary in i18next format
    :type i18next_data: Dict[str, Any]
    :return: Dictionary in unified format
    :rtype: Dict[str, Any]
    """
    unified = {}

    # Process flat keys first
    for key, value in i18next_data.items():
        if isinstance(value, dict):
            # Skip nested objects for now
            continue

        if key.endswith("_plural"):
            # Handle plural form
            singular_key = key[:-7]  # Remove '_plural' suffix
            if singular_key not in unified:
                unified[singular_key] = {
                    "translation": "",
                    "plural_forms": {"1": value},
                    "context": "",
                    "metadata": {},
                }
            else:
                unified[singular_key]["plural_forms"]["1"] = value
        else:
            # Check if this is a singular form with a plural counterpart
            plural_key = f"{key}_plural"
            if plural_key in i18next_data:
                if key not in unified:
                    unified[key] = {
                        "translation": value,
                        "plural_forms": {"0": value, "1": i18next_data[plural_key]},
                        "context": "",
                        "metadata": {},
                    }
                else:
                    unified[key]["translation"] = value
                    unified[key]["plural_forms"]["0"] = value
            else:
                # Regular singular form
                unified[key] = {
                    "translation": value,
                    "plural_forms": {},
                    "context": "",
                    "metadata": {},
                }

    # Process nested objects
    for key, value in i18next_data.items():
        if isinstance(value, dict):
            nested_unified = i18next_to_unified_format(value)
            for nested_key, nested_value in nested_unified.items():
                full_key = f"{key}.{nested_key}"
                unified[full_key] = nested_value

    return unified


def unified_format_to_i18next(
    unified: Dict[str, Any], flatten: bool = True
) -> Dict[str, Any]:
    """
    Convert unified format to i18next JSON format.

    :param unified: Dictionary in unified format
    :type unified: Dict[str, Any]
    :param flatten: Whether to flatten nested keys using dot notation
    :type flatten: bool
    :return: Dictionary in i18next format
    :rtype: Dict[str, Any]
    """
    i18next = {}

    for key, entry in unified.items():
        # Handle nested keys if not flattening
        if not flatten and "." in key:
            parts = key.split(".")
            current = i18next
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = entry.get("translation", "")

            # Add plural form if available
            if entry.get("plural_forms", {}).get("1"):
                current[f"{parts[-1]}_plural"] = entry["plural_forms"]["1"]
        else:
            # Add singular form
            i18next[key] = entry.get("translation", "")

            # Add plural form if available
            if entry.get("plural_forms", {}).get("1"):
                i18next[f"{key}_plural"] = entry["plural_forms"]["1"]

    return i18next


def i18n_tools_to_unified_format(
    i18n_tools_data: Dict[str, List[List[str]]],
) -> Dict[str, Any]:
    """
    Convert i18n_tools JSON format to unified format.

    i18n_tools format is:
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

    :param i18n_tools_data: Dictionary in i18n_tools format
    :type i18n_tools_data: Dict[str, List[List[str]]]
    :return: Dictionary in unified format
    :rtype: Dict[str, Any]
    """
    unified = {}

    for key, value_lists in i18n_tools_data.items():
        if key == ".i18n_tools":  # Skip metadata
            continue

        entry = {
            "translation": value_lists[0][0] if value_lists and value_lists[0] else "",
            "plural_forms": {},
            "context": "",
            "metadata": {},
        }

        # Add plural forms
        for i, plural_list in enumerate(value_lists[1:], 1):
            if plural_list:
                entry["plural_forms"][str(i)] = plural_list[0]

        unified[key] = entry

    return unified


def unified_format_to_i18n_tools(unified: Dict[str, Any]) -> Dict[str, List[List[str]]]:
    """
    Convert unified format to i18n_tools JSON format.

    :param unified: Dictionary in unified format
    :type unified: Dict[str, Any]
    :return: Dictionary in i18n_tools format
    :rtype: Dict[str, List[List[str]]]
    """
    i18n_tools = {}

    for key, entry in unified.items():
        # Start with the singular form
        value_lists = [[entry.get("translation", "")]]

        # Add plural forms
        plural_forms = entry.get("plural_forms", {})
        max_plural = max([int(k) for k in plural_forms.keys()]) if plural_forms else 0

        for i in range(1, max_plural + 1):
            value_lists.append([plural_forms.get(str(i), "")])

        i18n_tools[key] = value_lists

    # Add metadata
    i18n_tools[".i18n_tools"] = {"version": "1.0", "format": "i18n_tools"}

    return i18n_tools


# High-level conversion functions


def convert_catalog_to_i18next(
    catalog: Catalog, flatten: bool = True
) -> Dict[str, Any]:
    """
    Convert a Babel Catalog directly to i18next JSON format.

    :param catalog: Babel Catalog object
    :type catalog: Catalog
    :param flatten: Whether to flatten nested keys using dot notation
    :type flatten: bool
    :return: Dictionary in i18next format
    :rtype: Dict[str, Any]
    """
    unified = catalog_to_unified_format(catalog)
    return unified_format_to_i18next(unified, flatten)


def convert_i18next_to_catalog(
    i18next_data: Dict[str, Any], locale: str = None, domain: str = None
) -> Catalog:
    """
    Convert i18next JSON format directly to a Babel Catalog.

    :param i18next_data: Dictionary in i18next format
    :type i18next_data: Dict[str, Any]
    :param locale: Locale for the catalog
    :type locale: str
    :param domain: Domain for the catalog
    :type domain: str
    :return: Babel Catalog object
    :rtype: Catalog
    """
    unified = i18next_to_unified_format(i18next_data)
    return unified_format_to_catalog(unified, locale, domain)


def convert_catalog_to_i18n_tools(catalog: Catalog) -> Dict[str, List[List[str]]]:
    """
    Convert a Babel Catalog directly to i18n_tools JSON format.

    :param catalog: Babel Catalog object
    :type catalog: Catalog
    :return: Dictionary in i18n_tools format
    :rtype: Dict[str, List[List[str]]]
    """
    unified = catalog_to_unified_format(catalog)
    return unified_format_to_i18n_tools(unified)


def convert_i18n_tools_to_catalog(
    i18n_tools_data: Dict[str, List[List[str]]], locale: str = None, domain: str = None
) -> Catalog:
    """
    Convert i18n_tools JSON format directly to a Babel Catalog.

    :param i18n_tools_data: Dictionary in i18n_tools format
    :type i18n_tools_data: Dict[str, List[List[str]]]
    :param locale: Locale for the catalog
    :type locale: str
    :param domain: Domain for the catalog
    :type domain: str
    :return: Babel Catalog object
    :rtype: Catalog
    """
    unified = i18n_tools_to_unified_format(i18n_tools_data)
    return unified_format_to_catalog(unified, locale, domain)


def convert_i18next_to_i18n_tools(
    i18next_data: Dict[str, Any],
) -> Dict[str, List[List[str]]]:
    """
    Convert i18next JSON format directly to i18n_tools JSON format.

    :param i18next_data: Dictionary in i18next format
    :type i18next_data: Dict[str, Any]
    :return: Dictionary in i18n_tools format
    :rtype: Dict[str, List[List[str]]]
    """
    unified = i18next_to_unified_format(i18next_data)
    return unified_format_to_i18n_tools(unified)


def convert_i18n_tools_to_i18next(
    i18n_tools_data: Dict[str, List[List[str]]], flatten: bool = True
) -> Dict[str, Any]:
    """
    Convert i18n_tools JSON format directly to i18next JSON format.

    :param i18n_tools_data: Dictionary in i18n_tools format
    :type i18n_tools_data: Dict[str, List[List[str]]]
    :param flatten: Whether to flatten nested keys using dot notation
    :type flatten: bool
    :return: Dictionary in i18next format
    :rtype: Dict[str, Any]
    """
    unified = i18n_tools_to_unified_format(i18n_tools_data)
    return unified_format_to_i18next(unified, flatten)


def load_and_convert_po_to_i18next(
    po_file_path: str, flatten: bool = True
) -> Dict[str, Any]:
    """
    Load a PO file and convert it to i18next JSON format.

    :param po_file_path: Path to the PO file
    :type po_file_path: str
    :param flatten: Whether to flatten nested keys using dot notation
    :type flatten: bool
    :return: Dictionary in i18next format
    :rtype: Dict[str, Any]
    """
    catalog = load_locale_po(po_file_path)
    return convert_catalog_to_i18next(catalog, flatten)


def load_and_convert_json_to_catalog(
    json_file_path: str, locale: str = None, domain: str = None
) -> Catalog:
    """
    Load a JSON file (i18next format) and convert it to a Babel Catalog.

    :param json_file_path: Path to the JSON file
    :type json_file_path: str
    :param locale: Locale for the catalog
    :type locale: str
    :param domain: Domain for the catalog
    :type domain: str
    :return: Babel Catalog object
    :rtype: Catalog
    """
    i18next_data = load_locale_json(json_file_path)
    return convert_i18next_to_catalog(i18next_data, locale, domain)


def seek_translation(
    repository: NestedDictionary,
    module: str,
    domain: str,
    lang: str,
    message_id: str,
    alternative: int = 0,
) -> NestedDictionary:
    """
    This function seeks a translation in the repository.
    :param repository:
    :type repository: NestedDictionary
    :param module:
    :type module: str
    :param domain:
    :type domain: str
    :param lang:
    :type lang: str
    :param message_id:
    :type message_id: str
    :param alternative:
    :type alternative: int
    :return:
    :rtype: NestedDictionary
    """
    translation = NestedDictionary(
        {"msg_id": "", "msgstr": "", "msgstr_plural": {}}, indent=2, strict=True
    )

    try:
        translations = fetch_dictionary(repository, module, domain, lang)
        if message_id in translations.keys():
            translation["mgs_id"] = message_id
            messages = translations[message_id]

        else:
            raise KeyError(f"{message_id} not found in {module}/{domain} in {lang}")
    except Exception as e:
        raise e

    return translation
