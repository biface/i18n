"""
loaders.py
==========

This module handles the file operations necessary for internationalization
(i18n) tools. It focuses on loading and saving configuration files and
managing `.pot` files for translation projects.

**Key Features:**
    - Load and save configuration files in YAML, TOML, or JSON formats.
    - Search for configuration files in application directories.
    - Load and save `.pot` files, including metadata headers and translation
  entries.

**License:**
This file is distributed under the `CeCILL-C Free Software License Agreement
<https://cecill.info/licences/Licence_CeCILL-C_V1-en.html>`_. By using or
modifying this file, you agree to abide by the terms of this license.

**Author(s):**
This module is authored and maintained as part of the i18n-tools package.
"""

import tarfile
from pathlib import Path
from typing import Any, Dict, List

from babel.messages.catalog import Catalog
from babel.messages.mofile import read_mo, write_mo
from babel.messages.pofile import read_po, write_po

from i18n_tools.loaders.utils import (
    _create_gzip,
    _load_json,
    _non_traversal_path,
    _save_json,
)


def _load_po(file_path: str) -> Catalog:
    """
    Load a PO file and return its content as a Babel Catalog.
    :param file_path: Path to the PO file.
    :type file_path: str
    :return: Babel Catalog object.
    :rtype: Catalog
    :raises FileNotFoundError: File not found.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as po_file:
            return read_po(po_file)
    except Exception as exception:
        raise FileNotFoundError(f'File "{file_path}" not found.') from exception


def _save_po(file_path: str, po_data: Catalog) -> None:
    """
    Save a PO file using Babel.
    :param file_path: Path to the PO file.
    :type file_path: str
    :param po_data: Babel Catalog object.
    :type po_data: Catalog
    :return: None
    :raises FileNotFoundError: File not found.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as po_file:
            write_po(po_file, po_data)
    except Exception as exception:
        raise FileNotFoundError(f'File "{file_path}" not found.') from exception


def _load_pot(file_path: str) -> Catalog:
    """
    Load a POT file and return its content as a Babel Catalog.
    :param file_path: Path to the POT file.
    :type file_path: str
    :return: Babel Catalog object.
    :rtype: Catalog
    :raises FileNotFoundError: File not found.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as pot_file:
            return read_po(pot_file)
    except Exception as exception:
        raise FileNotFoundError(f'File "{file_path}" not found.') from exception


def _save_pot(file_path: str, pot_data: Catalog) -> None:
    """
    Save a POT file using Babel.
    :param file_path: Path to the POT file.
    :type file_path: str
    :param pot_data: Babel Catalog object.
    :type pot_data: Catalog
    :return: None
    :raises FileNotFoundError: File not found.
    """
    try:
        with open(file_path, "w", encoding="utf-8") as pot_file:
            write_po(pot_file, pot_data)
    except Exception as exception:
        raise FileNotFoundError(f'File "{file_path}" not found.') from exception


def _load_mo(file_path: str) -> Catalog:
    """
    Load a MO file and return its content as a Babel Catalog.
    :param file_path: Path to the MO file.
    :type file_path: str
    :return: Babel Catalog object.
    :rtype: Catalog
    :raises FileNotFoundError: File not found.
    """
    try:
        with open(file_path, "rb") as mo_file:
            return read_mo(mo_file)
    except Exception as exception:
        raise FileNotFoundError(f'File "{file_path}" not found.') from exception


def _save_mo(file_path: str, mo_data: Catalog) -> None:
    """
    Save a MO file using Babel.
    :param file_path: Path to the MO file.
    :type file_path: str
    :param mo_data: Babel Catalog object.
    :type mo_data: Catalog
    :return: None
    :raises FileNotFoundError: File not found.
    """
    try:
        with open(file_path, "wb") as mo_file:
            write_mo(mo_file, mo_data)
    except Exception as exception:
        raise FileNotFoundError(f'File "{file_path}" not found.') from exception


def check_json_integrity(data: Dict[str, Any]) -> bool:
    """
    Check the integrity of the JSON locale data.

    :param data: The JSON locale data.
    :type data: dict
    :return: True if the data is valid, False otherwise.
    :rtype: bool
    """
    for key, value in data.items():
        if not isinstance(value, list):
            return False

        # Check that each item in the list is a list
        if not all(isinstance(item, list) for item in value):
            return False

        # Check that there is at least one non-empty list
        if not any(len(item) > 0 for item in value):
            return False

        # Check that all lists have the same length
        lengths = [len(item) for item in value]
        if len(set(lengths)) != 1:
            return False

    return True


def load_locale_json(file_path: str) -> Dict[str, Any]:
    """
    This function load a JSON file in the locales repository and containing i18next data. The structure of this
    dictionary is as follows:

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

    :param file_path: Path to the JSON locale file.
    :type file_path: str
    :return: JSON locale data content.
    :rtype: dict
    :raises FileNotFoundError: If the file is not found.
    :raises ValueError: If the file is not a valid JSON or fails the integrity check.
    """
    data = _load_json(file_path)
    if not check_json_integrity(data):
        raise ValueError(f"Integrity check failed for file: {file_path}")
    return data


def aggregate_locale_json(
    structure: Dict[str, Any],
    domains: Dict[str, List[str]],
    languages: Dict[str, List[str]],
) -> Dict[str, Any]:
    """
    Aggregate JSON locale files based on the given structure, domains, and languages.

    :param structure: Dictionary containing 'base' path and list of 'modules'.
    :type structure: Dict[str, Any]
    :param domains: Dictionary where keys are module names and values are lists of domains.
    :type domains: Dict[str, List[str]]
    :param languages: Dictionary where keys are language codes and values are lists of regional variants.
    :type languages: Dict[str, List[str]]
    :return: A consolidated dictionary of locale data.
    :rtype: dict
    """
    aggregated_data = {}
    base_path = Path(structure["base"])
    modules = structure["modules"]

    for module in modules:
        module_path = base_path / module / "locales"
        module_data = {}

        for domain in domains.get(module, []):
            domain_data = {}

            for lang, variants in languages.items():
                # Include the main language in the list of variants
                all_variants = [lang] + variants

                for variant in all_variants:
                    file_path = module_path / variant / f"{domain}.json"

                    if file_path.exists():
                        data = load_locale_json(file_path)
                        domain_data[variant] = data

            module_data[domain] = domain_data

        aggregated_data[module] = module_data

    return aggregated_data


def load_locale_po(file_path: str) -> Catalog:
    """
    Public interface to load a PO locale file with integrity check.

    :param file_path: Path to the PO locale file.
    :type file_path: str
    :return: Babel Catalog object.
    :rtype: Catalog
    :raises FileNotFoundError: If the file is not found.
    :raises ValueError: If the file is not a valid PO file or fails the integrity check.
    """
    return _load_po(file_path)


def save_locale_json(file_path: str, data: Dict[str, Any]) -> None:
    """
    Save data to a JSON locale file.

    :param file_path: Path to the JSON locale file.
    :type file_path: str
    :param data: Dictionary containing locale data.
    :type data: dict
    :raises FileNotFoundError: If the directory for the file is not found.
    """
    _save_json(file_path, data)


def save_aggregated_locale_json(
    aggregated_data: Dict[str, Any], base_path: str
) -> None:
    """
    Save the aggregated locale JSON data as gzipped files for each domain in the locales directory,
    and create a gzipped file for the entire module or sub-module at the base of its directory.

    :param aggregated_data: The aggregated dictionary of locale data.
    :type aggregated_data: dict
    :param base_path: The base path where the locales directories are located.
    :type base_path: str
    """
    for module, module_data in aggregated_data.items():
        # Handle sub-modules by splitting the module key
        module_parts = module.split("/")
        module_name = module_parts[-1]
        module_dir = Path(base_path) / "/".join(module_parts)

        locales_path = module_dir / "locales"
        locales_path.mkdir(parents=True, exist_ok=True)

        # Save individual domain files
        for domain, domain_data in module_data.items():
            json_file_path = locales_path / f"{domain}.json"
            _save_json(json_file_path, domain_data)
            _create_gzip(json_file_path)
            json_file_path.unlink()

        # Save aggregated module data
        module_json_path = module_dir / f"{module_name}.json"
        _save_json(module_json_path, module_data)
        _create_gzip(module_json_path)
        module_json_path.unlink()


def save_locale_po(file_path: str, po_data: Catalog) -> None:
    """
    The public interface to _save_po
    :param file_path:
    :param po_data:
    :return:
    """
    _save_po(file_path, po_data)


def save_locale_pot(file_path: str, po_data: Catalog) -> None:
    """
    The public interface to _save_pot
    :param file_path:
    :param po_data:
    :return:
    """
    _save_pot(file_path, po_data)


def create_module_archive(root_path: str, module: str, archive_name: str) -> None:
    """
    Create a tar.gz archive of a module's contents, including all subdirectories and files,
    by identifying the top-level module from the given module/package path.

    :param root_path: The base path where the modules are located.
    :type root_path: str
    :param module: The module or module/package path (e.g., "mod-1/pkg-1").
    :type module: str
    :param archive_name: The name of the archive file.
    :type archive_name: str
    :return: None
    :rtype: None
    """

    # Convert root_path to a Path object and resolve it to an absolute path
    # This ensures that the path is absolute and any symbolic links are resolved
    root_path = Path(root_path).resolve()

    # Identify the top-level module from the given module path
    # This is done by splitting the module path and taking the first part
    # For example, if module is "mod-1/pkg-1", top_level_module will be "mod-1"
    top_level_module = module.split("/")[0]

    # Construct the full path to the top-level module
    # This is the directory that will be archived
    module_path = (root_path / top_level_module).resolve()

    # Construct the path for the archive file
    # The archive will be created in the root_path directory with the given archive_name
    archive_path = root_path / f"{archive_name}.tar.gz"

    # Open the archive file in write mode with gzip compression
    with tarfile.open(archive_path, "w:gz") as tar:
        # Add the top-level module to the archive
        # The arcname parameter ensures that the directory structure is preserved in the archive
        # This means the archive will contain the top-level module directory and all its contents
        tar.add(module_path, arcname=top_level_module)


def restore_module_from_archive(root_path: str, module: str, archive_name: str) -> None:
    """
    Restore a module's contents from a tar.gz archive.

    :param root_path: The base path where the modules are located.
    :type root_path: str
    :param module: The module or sub-module path (e.g., "mod-1/pkg-1").
    :type module: str
    :param archive_name: The name of the archive file.
    :type archive_name: str
    """

    # Split the module path to get the top-level module
    module_parts = module.split("/")
    top_level_module = module_parts[0]

    # Construct the path for the archive file
    archive_path = Path(root_path) / f"{archive_name}.tar.gz"

    # Construct the full path to the module
    module_path = Path(root_path) / module

    # Check if the archive file exists
    if archive_path.exists():
        # Open the archive file in read mode with gzip compression
        with tarfile.open(archive_path, "r:gz") as tar:
            # Extract all members that are safe to extract
            tar.extractall(
                path=root_path,
                members=_non_traversal_path(
                    root_path, [top_level_module], tar.getmembers()
                ),
            )
    else:
        # Raise an error if the archive file does not exist
        raise FileNotFoundError(f"Archive file '{archive_path}' not found.")
