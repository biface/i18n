"""
converter.py
============

This module provides functions to manipulate and convert internationalization
(i18n) data between different formats. It includes utilities for generating
headers for `.pot` files, converting data between `i18n` and `i18next` formats,
and creating deterministic message IDs.

**Key Features:**

    - Convert PO files to i18next JSON format and vice versa.
    - Generate deterministic message IDs using weights and base values.
    - Create metadata headers for `.pot` files, including author and team
      information.

**License:**
This file is distributed under the `CeCILL-C Free Software License Agreement
<https://cecill.info/licences/Licence_CeCILL-C_V1-en.html>`_. By using or
modifying this file, you agree to abide by the terms of this license.

**Author(s):**
This module is authored and maintained as part of the i18n-tools package.

"""

from datetime import datetime
from pathlib import Path
from typing import Dict

from babel.messages.catalog import Catalog

from i18n_tools.loaders.loader import save_locale_pot
from i18n_tools.locale import get_all_languages


def _initialize_pot_file(file_path: str, domain: str, authors: Dict, language: str):
    """
    Initializes a .pot file with necessary metadata and entries for relevant authors.

    :param file_path: Path to the .pot file.
    :param domain: Domain of translation.
    :param authors: Dictionary of authors.
    :param language: Language code for the current .pot file.
    """
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
