"""
Synchronization Module
======================

This module is responsible for providing control functions for other modules, such as checking the number of elements and differences between translations. It verifies data integrity across all files for each domain and language, ensuring consistency and completeness.

Key Responsibilities:
    - Provide control functions for other modules.
    - Verify data integrity and completeness across all files.
    - Propose solutions for incomplete translations using online translators.
"""

from pathlib import Path
from typing import Dict

from .loaders.utils import _create_empty_file, _create_empty_json
from .locale import validate_and_normalize_language_tags


def check_repository(tld: str, domains: Dict, languages: Dict):
    """
    Checks and creates necessary files in the translation repository.

    :param tld: Absolute root path of the translation repository.
    :param domains: Dictionary of translation domains.
    :param languages: Dictionary of translation languages.
    :raises ValueError: If tld is not an absolute path.
    :raises FileNotFoundError: If tld does not exist.
    """
    # Verify that tld is an absolute path and exists
    tld_path = Path(tld)
    if not tld_path.is_absolute():
        raise ValueError(f"The tld path must be absolute: {tld}")
    if not tld_path.exists():
        raise FileNotFoundError(f"The tld path does not exist: {tld}")

    # Validate and normalize languages
    all_languages = [languages["source"]] + [
        lang for sublist in languages["hierarchy"].values() for lang in sublist
    ]
    validated_languages = validate_and_normalize_language_tags(all_languages)

    for module, domain_list in domains.items():
        # Determine the path for the module or package
        module_path = tld_path / module
        locales_path = module_path / "locales"
        locales_path.mkdir(parents=True, exist_ok=True)

        for domain in domain_list:
            for lang in validated_languages:
                lang_path = locales_path / lang / "LC_MESSAGES"
                lang_path.mkdir(parents=True, exist_ok=True)

                # Create .json, .pot, and .po files
                json_file = lang_path / f"{domain}.json"
                pot_file = lang_path / f"{domain}.pot"
                po_file = lang_path / f"{domain}.po"

                if not json_file.exists():
                    _create_empty_json(str(json_file))

                if not pot_file.exists():
                    _create_empty_file(str(pot_file))

                if not po_file.exists():
                    _create_empty_file(str(po_file))


# TODO: look for json files to be gzipped in domains repository (used before making archives)
# TODO: look for rebuild partially repository from gzipped or archive files
