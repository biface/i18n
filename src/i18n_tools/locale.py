"""
Locale Module
=============

This module manages the locale of the environment and handles locale changes to adapt to user requests or parameters. It ensures that the locale settings are verified and normalized to the ISO IETF Tag standard.

Key Responsibilities:
    - Manage environment locale and handle locale changes.
    - Verify and normalize locale settings to ISO IETF Tag standard.
"""

from typing import Dict, List, Set

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


def validate_and_normalize_language_tags(tags: list[str]) -> list[str]:
    """
    Validate and normalize a list of language tags.

    :param tags: A list of IETF language tags to validate and normalize.
    :return: A list of normalized language tags.
    :raises ValueError: If any language tag is invalid.
    """
    normalized_tags = []
    for tag in tags:
        if not is_valid_language_tag(tag):
            raise ValueError(f"Invalid language tag: {tag}")
        normalized_tags.append(normalize_language_tag(tag))
    return normalized_tags


def get_all_languages(hierarchy: Dict[str, List[str]]) -> Set[str]:
    """
    Collect all unique languages from the hierarchy dictionary.

    :param hierarchy: Dictionary containing language hierarchies.
    :return: A set of all unique languages.
    """
    all_languages = set(hierarchy.keys())
    for lang_list in hierarchy.values():
        all_languages.update(lang_list)
    return all_languages
