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

import langcodes


def is_valid_language_tag(tag: str) -> bool:
    """
    Vérifie si un tag linguistique est valide selon ISO 639-1 ou ISO 639-3.
    """
    return langcodes.tag_is_valid(tag)


def normalize_language_tag(tag: str) -> str:
    """
    Normalize a language tag to a standard format.

    :param tag: The IETF language tag to normalize.
    :return: A normalized tag (lowercase with title-case script/region).
    """
    if not is_valid_language_tag(tag):
        raise ValueError(f"Invalid language tag: {tag}")

    return langcodes.standardize_tag(tag)
