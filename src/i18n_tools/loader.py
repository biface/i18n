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

import gzip
import json
import os
import shutil
import tarfile
from pathlib import Path
from typing import Any, Dict, List
from unittest import expectedFailure

import toml
import yaml
from polib import MOFile, POEntry, POFile, mofile, pofile


def build_path(base_path: str, *sub_dirs: str) -> str:
    """
    Constructs a path by combining a base path with one or more subdirectories.

    :param base_path: The starting path.
    :param sub_dirs: One or more subdirectory names to append to the base path.
    :return: The combined path as a string.
    """
    path = Path(base_path)
    for sub_dir in sub_dirs:
        path /= sub_dir
    return str(path.resolve())


def file_exists(file_path: str) -> bool:
    """
    Checks if a file exists.
    :param file_path: a path to a file.
    :type file_path: str
    :return: True if the file exists.
    :rtype: bool
    """
    return Path(file_path).exists()


def create_directory(path: str) -> None:
    """
    Create a directory from a path.
    :param path: a path to a directory.
    :type path: str
    :return: None
    :rtype: None
    """
    Path(path).mkdir(parents=True, exist_ok=True)


def _load_json(file_path: str) -> Dict[str, Any]:
    """
    Load a JSON file without managing data structure and integrity and returns its content as a dictionary.
    :param file_path: Path to the JSON file.
    :type file_path: str
    :return: JSON Translation data content.
    :rtype: dict
    :raises FileNotFoundError: File not found.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as json_file:
            return json.load(json_file)
    except Exception as exception:
        raise FileNotFoundError(f'File "{file_path}" not found.') from exception


def _save_json(file_path: str, data: Dict[str, Any]) -> None:
    """
    Save a JSON file without managing data structure and integrity and returns its content.
    :param file_path: Path to the JSON file.
    :type file_path: str
    :param data: JSON Translation data content.
    :type data: dict
    :return: None
    :raises FileNotFoundError: File not found.
    """
    try:
        with open(file_path, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)
    except Exception as exception:
        raise FileNotFoundError(f'File "{file_path}" not found.') from exception


def _create_empty_json(file_path: str) -> None:
    """
    Create an empty JSON file without managing data structure and integrity and returns its content.
    :param file_path: JSON file path.
    :type file_path: str
    :return: None
    :rtype: None
    :raises FileNotFoundError: File not found.
    """
    try:
        with open(file_path, "w", encoding="utf-8") as json_file:
            json.dump({}, json_file, ensure_ascii=False, indent=4)
    except Exception as exception:
        raise FileNotFoundError(f'File "{file_path}" not found.') from exception


def _load_po(file_path: str) -> POFile:
    """
    Load a PO file without managing data structure and integrity and returns its content.
    :param file_path: Path to the PO file.
    :type file_path: str
    :return: PO file object
    :rtype: POFile
    :raises FileNotFoundError: File not found.
    """
    try:
        return pofile(file_path)
    except Exception as exception:
        raise FileNotFoundError(f'File "{file_path}" not found.') from exception


def _save_po(file_path: str, po_data: pofile) -> None:
    """
    Save a PO file without managing data structure and integrity and returns its content.
    :param file_path: Path to the PO file.
    :type file_path: str
    :param po_data: PO file object.
    :type po_data: pofile
    :return: None
    :raises FileNotFoundError: File not found.
    """
    try:
        po_data.save(file_path)
    except Exception as exception:
        raise FileNotFoundError(f'File "{file_path}" not found.') from exception


def _load_pot(file_path: str) -> POFile:
    """
    Load a POT file and return its content.

    :param file_path: Path to the PO file.
    :type file_path: str
    :return: PO file object
    :rtype: POFile
    :raises FileNotFoundError: File not found.
    """
    try:
        return pofile(file_path)
    except Exception as exception:
        raise FileNotFoundError(f'File "{file_path}" not found.') from exception


def _save_pot(file_path: str, pot_data: pofile) -> None:
    """
    Save a POT file.

    :param file_path: Path to the PO file.
    :type file_path: str
    :param pot_data: PO file object.
    :type pot_data: pofile
    :return: None
    :raises FileNotFoundError: File not found.
    """
    try:
        pot_data.save(file_path)
    except Exception as exception:
        raise FileNotFoundError(f'File "{file_path}" not found.') from exception


def _load_mo(file_path: str) -> MOFile:
    """
    Load a MO file without managing data structure and integrity and returns its content.
    :param file_path: Path to the MO file.
    :type file_path: str
    :return: MO file object
    :rtype: MOFile
    :raises FileNotFoundError: File not found.
    """
    try:
        with open(file_path, "rb") as mo_file:
            return MOFile(mo_file)
    except Exception as exception:
        raise FileNotFoundError(f'File "{file_path}" not found.') from exception


def _save_mo(file_path: str, mo_data: pofile) -> None:
    """
    Save a MO file without managing data structure and integrity and returns its content.
    :param file_path: Path to the MO file.
    :type file_path: str
    :param mo_data: MO file object.
    :type mo_data: pofile
    :return: None
    :raises FileNotFoundError: File not found.
    """
    try:
        mo_data.save_as_mofile(file_path)
    except Exception as exception:
        raise FileNotFoundError(f'File "{file_path}" not found.') from exception


def _create_empty_file(file_path: str) -> None:
    """
    Create an empty file.
    :param file_path: a path to a file.
    :type file_path: str
    :return: None
    :rtype: None
    :raises FileNotFoundError: File not found.
    """
    try:
        with open(file_path, "w", encoding="utf-8") as empty_file:
            empty_file.write("")
    except Exception as exception:
        raise FileNotFoundError(f'File "{file_path}" not found.') from exception


def _create_tar_gz(
    base_path: str, archive_name: str, directory_to_archive: str
) -> None:
    """
    Create an archive of a directory using tar.gz fonctions.
    :param base_path: directory to locate the archive.
    :type base_path: str
    :param archive_name: archive name
    :type archive_name: str
    :param directory_to_archive: directory to be archived.
    :type directory_to_archive: str
    :return: None
    ;rtype: None
    """
    tarfile_path = Path(base_path) / archive_name
    with tarfile.open(tarfile_path, "w:gz") as tar:
        tar.add(directory_to_archive, arcname=Path(directory_to_archive).name)


def _create_gzip(file_path: str) -> None:
    """
    Create a compressed file using gzip fonctions.
    :param file_path: a path to a file.
    :type file_path: str
    :return: None
    :rtype: None
    """
    gz_file = f"{file_path}.gz"
    with open(file_path, "rb") as file_in:
        with gzip.open(gz_file, "wb") as file_out:
            shutil.copyfileobj(file_in, file_out)


def _load_config_file(config_path: Path) -> dict:
    """
    Helper function to load the configuration file based on its extension.

    :param config_path: Path to the configuration file.
    :raises ValueError: If the file format is unsupported.
    :raises Exception: For errors during loading.
    :return: The configuration content as a dictionary.
    """
    [file_extension] = Path(config_path).suffixes

    try:
        with open(config_path, "r", encoding="utf-8") as file:
            if file_extension == ".yaml":
                return yaml.safe_load(file)
            elif file_extension == ".toml":
                return toml.load(file)
            elif file_extension == ".json":
                return json.load(file)
            else:
                raise ValueError(
                    f"Unsupported configuration file format: {file_extension}"
                )
    except Exception as e:
        raise Exception(f"Error loading configuration file: {config_path}. {e}")


def load_config(config_path: str = None) -> dict:
    """
    Load the configuration file (YAML, TOML, or JSON) from the application directories
    (not from the package i18n-tools) and return its contents as a dictionary.

    :param config_path: Optional path to the configuration file. If None, it searches
    for it in the root of the application.
    :raises FileNotFoundError: If no configuration file is found in the application directories.
    :raises ValueError: If the file format is unsupported.
    :raises Exception: For other errors during loading.
    """
    # Si le chemin de configuration est fourni, utiliser ce chemin
    if config_path:
        if not Path(config_path).exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        return _load_config_file(config_path)

    # Sinon, rechercher dans les répertoires applicatifs (racine et répertoires locaux)
    search_dirs = [
        Path.cwd(),  # Répertoire racine de l'application
        Path.cwd() / "locales",  # Sous-répertoire locales de l'application
    ]

    possible_files = ["i18n-tools.yaml", "i18n-tools.toml", "i18n-tools.json"]

    # Recherche dans les répertoires définis
    for directory in search_dirs:
        for file_name in possible_files:
            config_file_path = directory / file_name
            if config_file_path.exists():
                return _load_config_file(config_file_path)

    raise FileNotFoundError(
        "No configuration file found in the application directories (root or locales)."
    )


def save_config(file_path: str, data: dict) -> None:
    """
    Save configuration data to a file.

    Supports JSON, YAML, and TOML formats.

    :param file_path: Path to the configuration file.
    :param data: The dictionary containing configuration data.
    """

    ext = os.path.splitext(file_path)[-1].lower()
    with open(file_path, "w", encoding="utf-8") as cf:
        if ext == ".json":
            json.dump(data, cf, indent=4)
        elif ext in {".yaml", ".yml"}:
            yaml.safe_dump(data, cf, default_flow_style=False)
        elif ext == ".toml":
            toml.dump(data, cf)
        else:
            raise ValueError(f"Unsupported file format: {ext}")


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


def save_locale_po(file_path: str, po_data: pofile) -> None:
    """
    The public interface to _save_po
    :param file_path:
    :param po_data:
    :return:
    """
    _save_json(file_path, po_data)


def save_locale_pot(file_path: str, po_data: pofile) -> None:
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


def _non_traversal_path(
    root_path: str, module_list: List[str], members: List[tarfile.TarInfo]
) -> List[tarfile.TarInfo]:
    """
    Ensure the member paths are safe to be extracted by checking if they are within the expected module paths.

    :param root_path: The root path of the module path.
    :type root_path: str
    :param module_list: The list of modules to extract.
    :type module_list: List[str]
    :param members: The list of members to extract.
    :type members: List[tarfile.TarInfo]
    :return: The safe paths for extraction.
    :rtype: List[tarfile.TarInfo]
    """

    # Convert root_path to a Path object and resolve it to an absolute path
    root_path = Path(root_path).resolve()

    # Create a set of expected module paths by combining root_path with each module in module_list
    expected_module_paths = {root_path / module for module in module_list}

    # List to store the safe paths for extraction
    safe_paths = []

    # Iterate over each member in the tar archive
    for member in members:
        member_path = Path(member.name)

        # Resolve the member path to check for directory traversal
        resolved_path = (root_path / member_path).resolve()

        # Check if the resolved path is within the root path and within any of the expected module paths
        if resolved_path.is_relative_to(root_path):
            # Ensure the resolved path is within one of the expected module paths
            if any(
                resolved_path.is_relative_to(module) for module in expected_module_paths
            ):
                safe_paths.append(member)

    return safe_paths


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
