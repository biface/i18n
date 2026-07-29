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
from typing import Any

from .__static__ import I18N_TOOLS_MESSAGES, I18N_TOOLS_TEMPLATE
from .loaders.loader import build_book_filename
from .loaders.utils import _create_empty_file, _create_empty_json
from .locale import get_all_languages, validate_and_normalize_language_tags


def check_repository(
    tld: str, domains: dict[str, list[str]], languages: dict[str, Any]
):
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

    # Validate and normalize languages — source plus every language in the
    # hierarchy, both the parent (fallback) keys themselves (e.g. "fr") and
    # their variants (e.g. "fr-FR", "fr-BE"). Uses the same
    # get_all_languages() helper as core.load_corpus(), so the two always
    # agree on which languages must have files on disk.
    all_languages = [languages["source"]] + list(
        get_all_languages(languages["hierarchy"])
    )
    validated_languages = validate_and_normalize_language_tags(all_languages)

    for module, domain_list in domains.items():
        # Determine the path for the module or package
        module_path = tld_path / module
        locales_path = module_path / "locales"
        locales_path.mkdir(parents=True, exist_ok=True)

        for domain in domain_list:
            # .pot is a per-domain template, shared across all languages created once in templates/, not
            # duplicated inside each language's LC_MESSAGES/.
            templates_path = locales_path / I18N_TOOLS_TEMPLATE
            templates_path.mkdir(parents=True, exist_ok=True)
            pot_file = templates_path / f"{domain}.pot"
            if not pot_file.exists():
                _create_empty_file(str(pot_file))

            for lang in validated_languages:
                lang_path = locales_path / lang / I18N_TOOLS_MESSAGES
                lang_path.mkdir(parents=True, exist_ok=True)

                # Create the native .i18t translation file (DD-34 naming,
                # via build_book_filename — the same helper Book itself
                # uses, so this stays in sync with Book's actual filename
                # convention) and a companion .po file.
                _, json_filename = build_book_filename(domain)
                json_file = lang_path / json_filename
                po_file = lang_path / f"{domain}.po"

                if not json_file.exists():
                    _create_empty_json(str(json_file))

                if not po_file.exists():
                    _create_empty_file(str(po_file))


# TODO: look for json files to be gzipped in domains repository (used before making archives)
# TODO: look for rebuild partially repository from gzipped or archive files
