"""
Converter Module
================

This module is responsible for converting data between different internationalization (i18n) formats as described in
package documentation. It serves as a bridge between various translation systems, allowing seamless conversion and
interoperability.

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

   - Proprietary format designed for this project.
   - Stored in JSON files with a structured format for efficient handling of translations.
   - Supports multiple message alternatives and plural forms using nested arrays.
   - Includes comprehensive metadata for each message (locations, flags, comments).
   - Supports global metadata for translation domains (project info, team info, statistics).
   - **Strengths:** Rich support for alternative messages, detailed metadata, optimized for this project's specific needs.

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


Unified Format Structure
^^^^^^^^^^^^^^^^^^^^^^^^

The unified format is a dictionary with the following structure:

.. code-block:: python

    {
        "message_id": {  # The unique identifier for the message (string)
            "translation": "The translated text for the message",  # (string)
            "plural_forms": {  # A dictionary containing plural forms of the translation
                0: "The singular form of the translation",  # (string)
                1: "The first plural form of the translation",  # (string)
                2: "The second plural form of the translation",  # (string)
                # Additional plural forms as needed
            },
            "context": "Optional context information for the translation",  # (string)
            "metadata": {  # A dictionary containing metadata about the translation
                "locations": ["A list of source code locations where the message is used"],  # (list of strings)
                "flags": ["A list of flags providing additional information about the message"],  # (list of strings)
                "comments": ["Translator comments associated with the message"],  # (list of strings)
                "auto_comments": ["Developer comments extracted from the source code"],  # (list of strings)
                # Additional metadata as needed
            },
            "alternatives": { # A dictionary containing alternative messages for the message
                0: "Alternative message 1"
                1: "Alternative message 2"
                },
            "alternative_plural_forms": {  # A dictionary containing plural forms for alternative messages
                0: {  # Index of the alternative message (corresponds to index in alternatives list)
                    1: "First plural form of alternative message 1",  # (string)
                    2: "Second plural form of alternative message 1",  # (string)
                },
                1: {  # Index of the alternative message (corresponds to index in alternatives list)
                    1: "First plural form of alternative message 2",  # (string)
                    2: "Second plural form of alternative message 2",  # (string)
                }
            }
        },
        "metadata": {  # Global metadata for the translation domain
            "project_id_version": "Project name and version",  # (string)
            "report_msgid_bugs_to": "Email address for reporting message ID bugs",  # (string)
            "pot_creation_date": "Date when the POT file was created",  # (string)
            "language_team": "Name and email of the language team",  # (string)
            "domain": "Translation domain name",  # (string)
            "header_comment": "Comment in the header of the catalog",  # (string)
            "copyright_holder": "Copyright holder information",  # (string)
            "statistics": {  # Statistics about the translations
                "total_messages": 1234,  # (integer)
                "total_words": 5678  # (integer)
            }
        }
    }

Extended ID Convention for Alternative Messages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To integrate alternative messages from the proprietary `i18n_tools` format into classic translation formats like Babel and i18next, an extended ID convention is used:

1. **Main Message**:
   - Base ID (e.g., ``id``) for the main message.
   - Example in PO format: ``msgid "id"`` / ``msgstr "main_msg"``
   - Example in i18next: ``{"id": "main_msg"}``

2. **Alternative Messages**:
   - Extended IDs with numerical suffix (e.g., ``id_001``, ``id_002``) for alternatives.
   - Example in PO format: ``msgid "id_001"`` / ``msgstr "alt_1_msg"``
   - Example in i18next: ``{"id_001": "alt_1_msg"}``

3. **Plural Forms**:
   - ``_plural`` suffix for plural forms of main message and alternatives.
   - Example in PO format: ``msgid "id_plural"`` / ``msgid_plural "plural_form"``
   - Example in i18next: ``{"id_plural": "plural_form"}``

This convention ensures clarity and compatibility with existing translation tools while preserving the rich alternative message functionality of the `i18n_tools` format.

Module Components
-----------------

This module is organized into several functional groups:

1. **Unified Format Conversion Functions**

   - Functions that convert between the unified format and other formats
   - Examples: ``catalog_to_unified_format``, ``unified_format_to_i18next``

2. **High-level Conversion Functions**

   - Direct conversion between formats without explicitly using the unified format
   - Examples: ``convert_catalog_to_i18next``, ``convert_i18n_tools_to_catalog``

3. **File Loading and Conversion Functions**

   - Utilities for loading files in one format and converting them to another
   - Examples: ``load_and_convert_po_to_i18next``, ``load_and_convert_json_to_catalog``

4. **Repository Interaction Functions**

   - Functions that interact with the translation repository
   - Example: ``seek_translation``

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
    - Interact with translation repositories to find and manipulate translations.
"""

import re
from typing import Any, Dict, List, Optional, Union

from babel.messages.catalog import Catalog, Message
from ndict_tools import StrictNestedDictionary

from i18n_tools.loaders import (
    dump_catalog,
    dump_dictionary,
    fetch_catalog,
    fetch_dictionary,
)
from i18n_tools.loaders.utils import _load_json, _load_text, _save_json, _save_text
from i18n_tools.locale import get_all_languages

# -----------------------------------------------------------------------------
# Unified Format Conversion Functions
# -----------------------------------------------------------------------------
#

# FIXME : Conversion to or from i18next and Catalog does not work well...


def catalog_to_unified_format(catalog: Catalog) -> Dict[str, Any]:
    """
    Convert a Babel Catalog to a unified format dictionary.

    :param catalog: Babel Catalog object
    :type catalog: Catalog
    :return: Dictionary in unified format
    :rtype: Dict[str, Any]
    """
    unified = {}
    alternative_messages = {}
    alternative_plurals = {}

    # Extract domain metadata from the catalog
    unified["metadata"] = {
        "project_id_version": f"{getattr(catalog, 'project', '')} {getattr(catalog, 'version', '')}".strip(),
        "report_msgid_bugs_to": getattr(catalog, "msgid_bugs_address", ""),
        "pot_creation_date": "",
        "language_team": "",
        "domain": getattr(catalog, "domain", ""),
        "header_comment": getattr(catalog, "header_comment", ""),
        "copyright_holder": getattr(catalog, "copyright_holder", ""),
    }

    # Extract additional metadata from mime_headers if available
    mime_headers = getattr(catalog, "mime_headers", [])
    for name, value in mime_headers:
        if name == "POT-Creation-Date":
            unified["metadata"]["pot_creation_date"] = value
        elif name == "Language-Team":
            unified["metadata"]["language_team"] = value

    # First pass: collect all messages and identify alternatives
    for message in catalog:
        if not message.id:  # Skip header
            continue

        message_id = message.id

        # Check if this is an alternative message (using the extended ID convention)
        is_alternative = False
        base_id = message_id
        alt_index = None

        if isinstance(message_id, str) and re.search(r"_\d{3}$", message_id):
            # This is an alternative message (e.g., id_001)
            match = re.search(r"(.+)_(\d{3})$", message_id)
            if match:
                base_id = match.group(1)
                alt_index = int(match.group(2))
                is_alternative = True

                # Store the alternative message for later processing
                if base_id not in alternative_messages:
                    alternative_messages[base_id] = {}
                alternative_messages[base_id][alt_index] = message
                continue

        # Check if this is a plural form of an alternative message
        elif isinstance(message_id, tuple) and re.search(r"_\d{3}$", message_id[0]):
            match = re.search(r"(.+)_(\d{3})$", message_id[0])
            if match:
                base_id = match.group(1)
                alt_index = int(match.group(2))

                # Store the alternative plural for later processing
                if base_id not in alternative_plurals:
                    alternative_plurals[base_id] = {}
                alternative_plurals[base_id][alt_index] = message
                continue

        # Process regular messages (non-alternatives)
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
                "alternatives": {},
                "alternative_plural_forms": {},
            }

            # Add plural forms
            if isinstance(message.string, (tuple, list)):
                # Start from index 1 for plural forms (index 0 is already stored as translation)
                for i, form in enumerate(message.string[1:], 1):
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
                "alternatives": {},
                "alternative_plural_forms": {},
            }

    # Second pass: add alternative messages to their base messages
    for base_id, alternatives in alternative_messages.items():
        if base_id not in unified:
            # Create an entry for the base ID if it doesn't exist
            unified[base_id] = {
                "translation": "",
                "plural_forms": {},
                "context": "",
                "metadata": {},
                "alternatives": {},
                "alternative_plural_forms": {},
            }

        # Sort alternatives by index
        sorted_indices = sorted(alternatives.keys())

        # Add alternatives to the base message
        for idx in sorted_indices:
            alt_message = alternatives[idx]
            alt_idx = (
                len(unified[base_id]["alternatives"])
                if "alternatives" in unified[base_id]
                else 0
            )
            unified[base_id]["alternatives"][str(alt_idx)] = alt_message.string

            # Initialize alternative_plural_forms for this alternative
            unified[base_id]["alternative_plural_forms"][str(alt_idx)] = {}

            # Add plural forms for this alternative if they exist
            if base_id in alternative_plurals and idx in alternative_plurals[base_id]:
                plural_message = alternative_plurals[base_id][idx]
                if (
                    isinstance(plural_message.string, (tuple, list))
                    and len(plural_message.string) > 1
                ):
                    # Start from index 1 for plural forms (index 0 is already stored as translation)
                    for i, form in enumerate(plural_message.string[1:], 1):
                        unified[base_id]["alternative_plural_forms"][str(alt_idx)][
                            str(i)
                        ] = form
                elif isinstance(plural_message.string, str):
                    # If the string is a single string, use it as the first plural form
                    unified[base_id]["alternative_plural_forms"][str(alt_idx)][
                        "1"
                    ] = plural_message.string

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
    # Extract metadata from unified format
    metadata = unified.get("metadata", {})

    # Parse project_id_version to get project and version
    project_id_version = metadata.get("project_id_version", "")
    project = project_id_version.split(" ")[0] if project_id_version else ""
    version = (
        " ".join(project_id_version.split(" ")[1:])
        if len(project_id_version.split(" ")) > 1
        else ""
    )

    # Create catalog with metadata
    catalog = Catalog(
        locale=locale,
        domain=domain or metadata.get("domain", None),
        project=project,
        version=version,
        copyright_holder=metadata.get("copyright_holder", ""),
        msgid_bugs_address=metadata.get("report_msgid_bugs_to", ""),
    )

    # Set additional metadata
    if "header_comment" in metadata:
        catalog.header_comment = metadata["header_comment"]

    # Set mime headers
    mime_headers = []
    if "project_id_version" in metadata:
        mime_headers.append(("Project-Id-Version", metadata["project_id_version"]))
    if "report_msgid_bugs_to" in metadata:
        mime_headers.append(("Report-Msgid-Bugs-To", metadata["report_msgid_bugs_to"]))
    if "pot_creation_date" in metadata:
        mime_headers.append(("POT-Creation-Date", metadata["pot_creation_date"]))
    if "language_team" in metadata:
        mime_headers.append(("Language-Team", metadata["language_team"]))

    if mime_headers:
        catalog.mime_headers = mime_headers

    for message_id, entry in unified.items():
        # Skip global metadata
        if message_id == "metadata":
            continue
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

        # Get metadata
        flags = entry.get("metadata", {}).get("flags", [])
        user_comments = entry.get("metadata", {}).get("comments", [])
        auto_comments = entry.get("metadata", {}).get("auto_comments", [])
        context = entry.get("context", "")

        # Handle plural forms
        plural_forms = entry.get("plural_forms", {})
        if plural_forms:
            # Create a tuple of strings for plural forms, starting with the singular form at index 0
            translation = entry.get("translation", "")
            plural_strings = [translation]  # Start with the singular form at index 0
            max_plural = (
                max([int(k) for k in plural_forms.keys()]) if plural_forms else 0
            )
            for i in range(1, max_plural + 1):
                plural_strings.append(plural_forms.get(str(i), ""))

            # Create a tuple of message IDs (singular, plural)
            if isinstance(message_id, str):
                msg_id_tuple = (message_id, f"{message_id}_plural")
            else:
                msg_id_tuple = message_id

            catalog.add(
                id=msg_id_tuple,
                string=tuple(plural_strings),
                locations=locations,
                flags=flags,
                user_comments=user_comments,
                auto_comments=auto_comments,
                context=context,
            )
        else:
            # Handle singular form
            catalog.add(
                id=message_id,
                string=entry.get("translation", ""),
                locations=locations,
                flags=flags,
                user_comments=user_comments,
                auto_comments=auto_comments,
                context=context,
            )

        # Handle alternative messages
        alternatives = entry.get("alternatives", {})
        alternative_plural_forms = entry.get("alternative_plural_forms", {})

        for alt_idx_str, alt_translation in alternatives.items():
            # Convert string index to integer for formatting
            alt_idx = int(alt_idx_str) + 1
            # Create alternative message ID using the extended ID convention (e.g., id_001)
            alt_message_id = f"{message_id}_{alt_idx:03d}"

            # Check if this alternative has plural forms
            if alt_idx_str in alternative_plural_forms:
                # Get plural forms for this alternative
                alt_plural_forms = alternative_plural_forms[alt_idx_str]

                if alt_plural_forms:
                    # Create a tuple of strings for plural forms, starting with the singular form at index 0
                    alt_plural_strings = [
                        alt_translation
                    ]  # Start with the alternative singular form at index 0
                    max_plural = (
                        max([int(k) for k in alt_plural_forms.keys()])
                        if alt_plural_forms
                        else 0
                    )

                    for i in range(1, max_plural + 1):
                        alt_plural_strings.append(alt_plural_forms.get(str(i), ""))

                    # Create a tuple of message IDs (singular, plural)
                    alt_msg_id_tuple = (alt_message_id, f"{alt_message_id}_plural")

                    catalog.add(
                        id=alt_msg_id_tuple,
                        string=tuple(alt_plural_strings),
                        locations=locations,
                        flags=flags,
                        user_comments=user_comments,
                        auto_comments=auto_comments,
                        context=context,
                    )
                else:
                    # Add alternative without plural forms
                    catalog.add(
                        id=alt_message_id,
                        string=alt_translation,
                        locations=locations,
                        flags=flags,
                        user_comments=user_comments,
                        auto_comments=auto_comments,
                        context=context,
                    )
            else:
                # Add alternative without plural forms
                catalog.add(
                    id=alt_message_id,
                    string=alt_translation,
                    locations=locations,
                    flags=flags,
                    user_comments=user_comments,
                    auto_comments=auto_comments,
                    context=context,
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
    alternative_messages = {}
    alternative_plurals = {}

    # First pass: collect all messages and identify alternatives
    for key, value in i18next_data.items():
        if key == "metadata":  # Skip metadata at root level
            continue
        if isinstance(value, dict):
            # Skip nested objects for now
            continue

        # Check if this is an alternative message (using the extended ID convention)
        is_alternative = False
        base_key = key
        alt_index = None

        if re.search(r"_\d{3}$", key) and not key.endswith("_plural"):
            # This is an alternative message (e.g., id_001)
            match = re.search(r"(.+)_(\d{3})$", key)
            if match:
                base_key = match.group(1)
                alt_index = int(match.group(2))
                is_alternative = True

                # Store the alternative message for later processing
                if base_key not in alternative_messages:
                    alternative_messages[base_key] = {}
                alternative_messages[base_key][alt_index] = value
                continue

        # Check if this is a plural form of an alternative message
        elif key.endswith("_plural") and re.search(r"_\d{3}_plural$", key):
            match = re.search(r"(.+)_(\d{3})_plural$", key)
            if match:
                base_key = match.group(1)
                alt_index = int(match.group(2))

                # Store the alternative plural for later processing
                if base_key not in alternative_plurals:
                    alternative_plurals[base_key] = {}
                alternative_plurals[base_key][alt_index] = value
                continue

        # Process regular messages (non-alternatives)
        if key.endswith("_plural"):
            # Handle plural form
            singular_key = key[:-7]  # Remove '_plural' suffix
            if singular_key not in unified:
                unified[singular_key] = {
                    "translation": "",
                    "plural_forms": {"1": value},
                    "context": "",
                    "metadata": {},
                    "alternatives": {},
                    "alternative_plural_forms": {},
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
                        "alternatives": {},
                        "alternative_plural_forms": {},
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
                    "alternatives": {},
                    "alternative_plural_forms": {},
                }

    # Second pass: add alternative messages to their base messages
    for base_key, alternatives in alternative_messages.items():
        if base_key not in unified:
            # Create an entry for the base key if it doesn't exist
            unified[base_key] = {
                "translation": "",
                "plural_forms": {},
                "context": "",
                "metadata": {},
                "alternatives": {},
                "alternative_plural_forms": {},
            }

        # Sort alternatives by index
        sorted_indices = sorted(alternatives.keys())

        # Add alternatives to the base message
        for idx in sorted_indices:
            alt_value = alternatives[idx]
            alt_idx = (
                len(unified[base_key]["alternatives"])
                if unified[base_key]["alternatives"]
                else 0
            )
            unified[base_key]["alternatives"][str(alt_idx)] = alt_value

            # Initialize alternative_plural_forms for this alternative
            unified[base_key]["alternative_plural_forms"][str(alt_idx)] = {}

            # Add plural forms for this alternative if they exist
            if base_key in alternative_plurals and idx in alternative_plurals[base_key]:
                plural_value = alternative_plurals[base_key][idx]
                unified[base_key]["alternative_plural_forms"][str(alt_idx)][
                    "1"
                ] = plural_value

    # Process nested objects
    for key, value in i18next_data.items():
        if key == "metadata":  # Handle global metadata
            unified["metadata"] = value
        elif isinstance(value, dict):
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

    # Add metadata if it exists in the unified format
    if "metadata" in unified:
        i18next["metadata"] = unified["metadata"]

    for key, entry in unified.items():
        # Skip global metadata
        if key == "metadata":
            continue
        # Handle nested keys if not flattening
        if not flatten and "." in key:
            parts = key.split(".")
            current = i18next
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]

            # Add main translation
            current[parts[-1]] = entry.get("translation", "")

            # Add plural form if available
            if entry.get("plural_forms", {}).get("1"):
                current[f"{parts[-1]}_plural"] = entry["plural_forms"]["1"]

            # Add alternative messages
            alternatives = entry.get("alternatives", {})
            alternative_plural_forms = entry.get("alternative_plural_forms", {})

            for alt_idx_str, alt_translation in alternatives.items():
                # Convert string index to integer for formatting
                alt_idx = int(alt_idx_str) + 1
                # Create alternative key using the extended ID convention (e.g., id_001)
                alt_key = f"{parts[-1]}_{alt_idx:03d}"
                current[alt_key] = alt_translation

                # Add plural form for this alternative if available
                if (
                    alt_idx_str in alternative_plural_forms
                    and "1" in alternative_plural_forms[alt_idx_str]
                ):
                    current[f"{alt_key}_plural"] = alternative_plural_forms[
                        alt_idx_str
                    ]["1"]
        else:
            # Add main translation
            i18next[key] = entry.get("translation", "")

            # Add plural form if available
            if entry.get("plural_forms", {}).get("1"):
                i18next[f"{key}_plural"] = entry["plural_forms"]["1"]

            # Add alternative messages
            alternatives = entry.get("alternatives", {})
            alternative_plural_forms = entry.get("alternative_plural_forms", {})

            for alt_idx_str, alt_translation in alternatives.items():
                # Convert string index to integer for formatting
                alt_idx = int(alt_idx_str) + 1
                # Create alternative key using the extended ID convention (e.g., id_001)
                alt_key = f"{key}_{alt_idx:03d}"
                i18next[alt_key] = alt_translation

                # Add plural form for this alternative if available
                if (
                    alt_idx_str in alternative_plural_forms
                    and "1" in alternative_plural_forms[alt_idx_str]
                ):
                    i18next[f"{alt_key}_plural"] = alternative_plural_forms[
                        alt_idx_str
                    ]["1"]

    return i18next


def i18n_tools_to_unified_format(
    i18n_tools_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Convert i18n_tools JSON format to unified format.

    :param i18n_tools_data: Dictionary in i18n_tools format
    :type i18n_tools_data: Dict[str, Any]
    :return: Dictionary in unified format
    :rtype: Dict[str, Any]
    """
    unified = {}

    for key, value in i18n_tools_data.items():
        if key == "metadata" or key == ".i18n_tools":  # Skip metadata at root level
            continue

        # Check if the entry has the new structure with messages and metadata
        if isinstance(value, dict) and "messages" in value and "metadata" in value:
            messages = value["messages"]
            metadata = value["metadata"]

            # Initialize entry with the main message (first alternative)
            entry = {
                "translation": messages[0][0] if messages and messages[0] else "",
                "plural_forms": {},
                "context": "",
                "metadata": {
                    "locations": [
                        (
                            f"{loc[0]}:{loc[1]}"
                            if isinstance(loc, list) and len(loc) >= 2
                            else loc
                        )
                        for loc in metadata.get("locations", [])
                    ],
                    "flags": metadata.get("flags", []),
                    "comments": metadata.get("comments", ""),
                    "auto_comments": [],
                },
                "alternatives": {},
            }

            # Add all alternatives from the first list (except the first one which is already the main translation)
            if messages and len(messages[0]) > 1:
                for i, alt in enumerate(messages[0][1:]):
                    entry["alternatives"][str(i)] = alt

            # Add plural forms for the main message
            for i, plural_list in enumerate(messages[1:], 1):
                if plural_list and plural_list[0]:
                    entry["plural_forms"][str(i)] = plural_list[0]

            # Add plural forms for alternatives
            if messages and len(messages[0]) > 1:
                entry["alternative_plural_forms"] = {}
                for alt_idx, _ in enumerate(messages[0][1:], 0):
                    entry["alternative_plural_forms"][str(alt_idx)] = {}
                    for plural_idx, plural_list in enumerate(messages[1:], 1):
                        if (
                            plural_list
                            and len(plural_list) > alt_idx + 1
                            and plural_list[alt_idx + 1]
                        ):
                            entry["alternative_plural_forms"][str(alt_idx)][
                                str(plural_idx)
                            ] = plural_list[alt_idx + 1]
        else:
            # Handle the old format where value is a list of lists
            value_lists = value

            # Initialize entry with the main message (first alternative)
            entry = {
                "translation": (
                    value_lists[0][0] if value_lists and value_lists[0] else ""
                ),
                "plural_forms": {},
                "context": "",
                "metadata": {},
                "alternatives": {},
            }

            # Add all alternatives from the first list (except the first one which is already the main translation)
            if value_lists and len(value_lists[0]) > 1:
                for i, alt in enumerate(value_lists[0][1:]):
                    entry["alternatives"][str(i)] = alt

            # Add plural forms for the main message
            for i, plural_list in enumerate(value_lists[1:], 1):
                if plural_list and plural_list[0]:
                    entry["plural_forms"][str(i)] = plural_list[0]

            # Add plural forms for alternatives
            if value_lists and len(value_lists[0]) > 1:
                entry["alternative_plural_forms"] = {}
                for alt_idx, _ in enumerate(value_lists[0][1:], 0):
                    entry["alternative_plural_forms"][str(alt_idx)] = {}
                    for plural_idx, plural_list in enumerate(value_lists[1:], 1):
                        if (
                            plural_list
                            and len(plural_list) > alt_idx + 1
                            and plural_list[alt_idx + 1]
                        ):
                            entry["alternative_plural_forms"][str(alt_idx)][
                                str(plural_idx)
                            ] = plural_list[alt_idx + 1]

        unified[key] = entry

    # Add global metadata if available
    if "metadata" in i18n_tools_data:
        unified["metadata"] = i18n_tools_data["metadata"]

    return unified


def unified_format_to_i18n_tools(unified: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert unified format to i18n_tools JSON format.

    :param unified: Dictionary in unified format
    :type unified: Dict[str, Any]
    :return: Dictionary in i18n_tools format
    :rtype: Dict[str, Any]
    """
    i18n_tools = {}

    for key, entry in unified.items():
        if key == "metadata":  # Handle global metadata separately
            continue

        # Start with the singular form and alternatives
        main_translation = entry.get("translation", "")
        alternatives = entry.get("alternatives", {})

        # Create the first list with main translation and alternatives
        first_list = [main_translation]
        # Add alternatives in order of their keys
        for idx in sorted([int(k) for k in alternatives.keys()]):
            first_list.append(alternatives[str(idx)])
        value_lists = [first_list]

        # Add plural forms for main message
        plural_forms = entry.get("plural_forms", {})
        max_plural = max([int(k) for k in plural_forms.keys()]) if plural_forms else 0

        # Add plural forms for alternatives
        alternative_plural_forms = entry.get("alternative_plural_forms", {})

        # Determine the maximum number of plural forms needed
        for i in range(1, max_plural + 1):
            plural_list = [plural_forms.get(str(i), "")]

            # Add plural forms for each alternative
            for alt_idx_str in sorted([str(k) for k in alternatives.keys()]):
                alt_plural = ""
                if (
                    alt_idx_str in alternative_plural_forms
                    and str(i) in alternative_plural_forms[alt_idx_str]
                ):
                    alt_plural = alternative_plural_forms[alt_idx_str][str(i)]
                plural_list.append(alt_plural)

            value_lists.append(plural_list)

        # Create entry with new structure (messages and metadata)
        entry_metadata = entry.get("metadata", {})

        i18n_tools[key] = {
            "messages": value_lists,
            "metadata": {
                "locations": entry_metadata.get("locations", []),
                "flags": entry_metadata.get("flags", []),
                "comments": entry_metadata.get("comments", ""),
                "singular_count": len(first_list),
                "plural_counts": (
                    [len(plural_list) for plural_list in value_lists[1:]]
                    if len(value_lists) > 1
                    else []
                ),
            },
        }

    # Add global metadata
    if "metadata" in unified:
        i18n_tools["metadata"] = unified["metadata"]
    else:
        i18n_tools["metadata"] = {
            "project_id_version": "i18n-tools 1.0",
            "statistics": {"total_messages": len(i18n_tools)},
        }

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
    print("i18n_tools_data keys:", list(i18n_tools_data.keys()))
    unified = i18n_tools_to_unified_format(i18n_tools_data)
    print("unified keys:", list(unified.keys()))
    catalog = unified_format_to_catalog(unified, locale, domain)
    print("catalog keys:", [msg.id for msg in catalog if msg.id])
    return catalog


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
    repository: StrictNestedDictionary,
    module: str,
    domain: str,
    lang: str,
    message_id: str,
    alternative: int = 0,
) -> StrictNestedDictionary:
    """
    Seek a translation in the repository.

    :param repository: Repository containing translations
    :type repository: StrictNestedDictionary
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
    :rtype: StrictNestedDictionary
    :raises KeyError: If the message ID is not found
    """
    translation = StrictNestedDictionary(
        {"msg_id": "", "msgstr": "", "msgstr_plural": {}}
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
