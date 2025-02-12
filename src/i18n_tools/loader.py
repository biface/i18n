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

import json
import os
from pathlib import Path
from typing import Any, Dict
from polib import pofile, mofile, POEntry

import toml
import yaml


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


# TODO : A low level _load_json_file, _load_po_file and _load_pot_file. Idem _save_... and see just to create a file.

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
        with open(file_path, 'r', encoding='utf-8') as json_file:
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
        with open(file_path, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)
    except Exception as exception:
        raise FileNotFoundError(f'File "{file_path}" not found.') from exception


def _load_po(file_path: str) -> pofile:
    """
    Load a PO file without managing data structure and integrity and returns its content.
    :param file_path: Path to the PO file.
    :type file_path: str
    :return: PO file object
    :rtype: pofile
    :raises FileNotFoundError: File not found.
    """
    try:
        return pofile(file_path)
    except Exception as exception:
        raise FileNotFoundError(f'File "{file_path}" not found.') from exception


def _save_po(file_path: str, po_data:pofile) -> None:
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

def _load_pot(file_path: str) -> pofile:
    """
    Load a POT file and return its content.

    :param file_path: Path to the PO file.
    :type file_path: str
    :return: PO file object
    :rtype: pofile
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

def _load_mo(file_path: str) -> mofile:
    """
    Load a MO file without managing data structure and integrity and returns its content.
    :param file_path: Path to the MO file.
    :type file_path: str
    :return: MO file object
    :rtype: mofile
    :raises FileNotFoundError: File not found.
    """
    try:
        return mofile(file_path)
    except Exception as exception:
        raise FileNotFoundError(f'File "{file_path}" not found.') from exception

def _save_mo(file_path: str, mo_data:pofile) -> None:
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

# TODO : A specialized function for json in locale and one for agregate json locales and gzip it.

# TODO : A backup file which tgz the repository

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
