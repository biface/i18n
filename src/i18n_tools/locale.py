"""
locale.py
=========

This module manages locale settings for the i18n-tools package. It ensures
correct handling of language-specific formats and regional preferences.

**Key Features:**
- Handle locale-specific formats for dates, numbers, and currencies.
- Manage active locale settings for translations.

**License:**
This file is distributed under the `CeCILL-C Free Software License Agreement
<https://cecill.info/licences/Licence_CeCILL-C_V1-en.html>`_. By using or
modifying this file, you agree to abide by the terms of this license.

**Author(s):**
This module is authored and maintained as part of the i18n-tools package.
"""

import re

# RFC 5646 Regex for language tags
LANGUAGE_TAG_REGEX = re.compile(
    r"^(?:(?P<language>[a-zA-Z]{2,3}(-[a-zA-Z]{3})?|[a-zA-Z]{4}|[a-zA-Z]{5,8})"
    r"(?:-(?P<script>[a-zA-Z]{4}))?"
    r"(?:-(?P<region>[a-zA-Z]{2}|\d{3}))?"
    r"(?:-(?P<variant>[a-zA-Z0-9]{5,8}|\d[a-zA-Z0-9]{3}))*"
    r"(?:-(?P<extension>[a-wy-zA-WY-Z0-9](?:-[a-zA-Z0-9]{2,8})+))*"
    r"(?:-x(?:-[a-zA-Z0-9]{1,8})+)?$)"
)


def is_valid_language_tag(tag: str) -> bool:
    """
    Validate a language tag according to RFC 5646.

    :param tag: The IETF language tag to validate.
    :return: True if the tag is valid, False otherwise.
    """
    return bool(LANGUAGE_TAG_REGEX.match(tag))


def normalize_language_tag(tag: str) -> str:
    """
    Normalize a language tag to a standard format.

    :param tag: The IETF language tag to normalize.
    :return: A normalized tag (lowercase with title-case script/region).
    """
    if not is_valid_language_tag(tag):
        raise ValueError(f"Invalid language tag: {tag}")

    parts = tag.split("-")
    normalized_parts = []

    for i, part in enumerate(parts):
        # Language part (first part)
        if i == 0:
            normalized_parts.append(part.lower())
        # Script part (4 letters, title-case)
        elif len(part) == 4 and part.isalpha():
            normalized_parts.append(part.title())
        # Region part (2 letters or 3 digits, uppercase)
        elif (len(part) == 2 and part.isalpha()) or (len(part) == 3 and part.isdigit()):
            normalized_parts.append(part.upper())
        # Variants, extensions, and private-use parts (leave as is)
        else:
            normalized_parts.append(part.lower())

    return "-".join(normalized_parts)