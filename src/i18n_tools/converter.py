"""
Converter Module
================

This module is responsible for converting data between different internationalization (i18n) formats.
It serves as a bridge between various translation systems, allowing seamless conversion and interoperability.

Supported Translation Formats
-----------------------------

1. **Babel Catalog Format**

   - Used by the Babel library, a standard Python internationalization framework.
   - Stores translations in ``.po`` (Portable Object) and ``.pot`` (Template) files.
   - Supports rich metadata including source locations, comments, and plural forms.
   - Provides programmatic access through the ``Catalog`` and ``Message`` classes.
   - **Strengths:** Comprehensive metadata, industry standard, good for developer workflows.

2. **i18next Format**

   - Used by the popular JavaScript i18n library i18next.
   - Typically stored in JSON files with a simple key-value structure.
   - Supports nested keys using dot notation (e.g., ``"app.title"``).
   - Handles plural forms with a special ``"_plural"`` suffix.
   - **Strengths:** Simplicity, frontend-friendly, easy to integrate with JavaScript applications.

3. **i18n_tools Format**

   - Internal format for this project.
   - Stored in JSON files with a specialized structure for handling translations.
   - Uses arrays to store multiple translations and plural forms.
   - Includes metadata under the ``".i18n_tools"`` key.
   - **Strengths:** Optimized for this project's specific needs, balances simplicity and features.

The Pivotal Role of the Unified Format
--------------------------------------

The unified format serves as a central hub in the conversion process, acting as an intermediate
representation that bridges all supported formats. This hub-and-spoke architecture provides several
key advantages:

1. **Simplified Conversion Logic**

   - Instead of needing direct conversion between each pair of formats (which would require
     ``n*(n-1)`` converters), we only need ``2*n`` converters (``n`` formats to/from unified format).
   - Adding a new format requires implementing only 2 new converters instead of ``2*n``.

2. **Consistent Data Representation**

   - The unified format captures all the essential elements from each format.
   - Ensures no data loss during conversion between different formats.
   - Provides a common language for all conversion operations.

3. **Standardized Metadata Handling**

   - Preserves important context information like comments, source locations, and flags.
   - Maintains plural forms across different systems with varying plural handling approaches.
   - Keeps translation context which is crucial for accurate translations.

Format Structure
----------------

Native ``i18n_tools`` Format Structure
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``i18n_tools`` format is a ``NestedDictionary`` object with the following structure:

.. code-block:: python

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

``i18next`` Format Structure
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``i18next`` format is typically a JSON object with the following structure:

.. code-block:: json

    {
        "key1": "value1",
        "key2": "value2",
        "key3_plural": "plural value",
        "key3": "singular value",
        "nested": {
            "key": "nested value"
        }
    }

Unified Format Structure
^^^^^^^^^^^^^^^^^^^^^^^^

The unified format is a dictionary with the following structure:

.. code-block:: python

    {
        "message_id": {  # The unique identifier for the message (string)
            "translation": "The translated text for the message",  # (string)
            "plural_forms": {  # A dictionary containing plural forms of the translation
                "0": "The singular form of the translation",  # (string)
                "1": "The first plural form of the translation",  # (string)
                "2": "The second plural form of the translation",  # (string)
                # Additional plural forms as needed
            },
            "context": "Optional context information for the translation",  # (string)
            "metadata": {  # A dictionary containing metadata about the translation
                "locations": ["A list of source code locations where the message is used"],  # (list of strings)
                "flags": ["A list of flags providing additional information about the message"],  # (list of strings)
                "comments": ["Translator comments associated with the message"],  # (list of strings)
                "auto_comments": ["Developer comments extracted from the source code"],  # (list of strings)
                # Additional metadata as needed
            }
        }
    }

Conversion Process
------------------

The conversion process follows these general steps:

1. **Source format → Unified format:** Extract all translation data and metadata from the source format.
2. **Unified format → Target format:** Transform the unified representation into the target format.
3. **Handle format-specific features:** Address special cases like nested keys in ``i18next`` or plural forms.

This module provides both low-level conversion functions (to/from unified format) and high-level
direct conversion functions between formats, as well as utilities for loading and saving translations
in different file formats.

Key Responsibilities:
    - Convert between Babel Catalog, i18next, and i18n_tools formats.
    - Provide a unified format as an intermediate representation.
    - Support loading and saving translations in different formats.
    - Preserve translation metadata across format conversions.
"""

from typing import Any, Dict, List, Optional, Union

from babel.messages.catalog import Catalog, Message
from ndict_tools import NestedDictionary

from i18n_tools.loaders import (
    fetch_catalog,
    fetch_dictionary,
    dump_catalog,
    dump_dictionary,
)
from i18n_tools.loaders.utils import _load_json, _load_text, _save_json, _save_text
from i18n_tools.locale import get_all_languages

# -----------------------------------------------------------------------------
# Unified Format Conversion Functions
# -----------------------------------------------------------------------------
#


def catalog_to_unified_format(catalog: Catalog) -> Dict[str, Any]:
    """
    Convert a Babel Catalog to a unified format dictionary.

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


# -----------------------------------------------------------------------------
# High-level conversion functions
# -----------------------------------------------------------------------------
# These functions provide direct conversion between formats without going
# through the unified format explicitly.

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


# -----------------------------------------------------------------------------
# File loading and conversion functions
# -----------------------------------------------------------------------------
# These functions provide utilities for loading files in one format and
# converting them to another format.

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
    catalog = _load_text(po_file_path)
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
    i18next_data = _load_json(json_file_path)
    return convert_i18next_to_catalog(i18next_data, locale, domain)


# -----------------------------------------------------------------------------
# Repository interaction functions
# -----------------------------------------------------------------------------
# These functions interact with the translation repository to find and
# manipulate translations.

def seek_translation(
    repository: NestedDictionary,
    module: str,
    domain: str,
    lang: str,
    message_id: str,
    alternative: int = 0,
) -> NestedDictionary:
    """
    Seek a translation in the repository.

    :param repository: Repository containing translations
    :type repository: NestedDictionary
    :param module: Module name
    :type module: str
    :param domain: Domain name
    :type domain: str
    :param lang: Language code
    :type lang: str
    :param message_id: Message ID to find
    :type message_id: str
    :param alternative: Alternative index (for plural forms)
    :type alternative: int
    :return: Translation data
    :rtype: NestedDictionary
    :raises KeyError: If the message ID is not found
    """
    translation = NestedDictionary(
        {"msg_id": "", "msgstr": "", "msgstr_plural": {}}, indent=2, strict=True
    )

    try:
        translations = fetch_dictionary(repository, module, domain, lang)
        if message_id in translations.keys():
            translation["msg_id"] = message_id
            messages = translations[message_id]

            # Add the translation string
            if messages and len(messages) > 0 and len(messages[0]) > alternative:
                translation["msgstr"] = messages[0][alternative]

            # Add plural forms if available
            if messages and len(messages) > 1:
                for i, plural_form in enumerate(messages[1:], 1):
                    if plural_form and len(plural_form) > alternative:
                        translation["msgstr_plural"][str(i)] = plural_form[alternative]
        else:
            raise KeyError(f"{message_id} not found in {module}/{domain} in {lang}")
    except Exception as e:
        raise e

    return translation
