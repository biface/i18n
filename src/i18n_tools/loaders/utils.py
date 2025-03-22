import gzip
import json
import shutil
import tarfile
from pathlib import Path
from typing import Any, Dict, List

import toml
import yaml
from babel.messages.catalog import Catalog
from babel.messages.mofile import read_mo, write_mo
from babel.messages.pofile import read_po, write_po
from polib import POFile, pofile

# Generic empty files


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


# JSON load and save files


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


# PO file handling with polib


def _load_text(file_path: str) -> POFile:
    """
    Load a PO file using polib and return a POFile object.

    :param file_path: Path to the PO file.
    :type file_path: str
    :return: POFile object containing the PO file data.
    :rtype: POFile
    :raises FileNotFoundError: If the file is not found.
    """
    try:
        return pofile(file_path)
    except Exception as exception:
        raise FileNotFoundError(f'File "{file_path}" not found.') from exception


def _save_text(file_path: str, po_data: POFile) -> None:
    """
    Save a POFile object to a PO file.

    :param file_path: Path to the PO file.
    :type file_path: str
    :param po_data: POFile object to be saved.
    :type po_data: POFile
    :raises FileNotFoundError: If the file path is invalid.
    """
    try:
        po_data.save(file_path)
    except Exception as exception:
        raise FileNotFoundError(f'File "{file_path}" not found.') from exception


# MO file handling with polib


def _load_machine(file_path: str) -> POFile:
    """
    Load a MO file using polib and return a POFile object.

    :param file_path: Path to the MO file.
    :type file_path: str
    :return: POFile object containing the MO file data.
    :rtype: POFile
    :raises FileNotFoundError: If the file is not found.
    """
    try:
        return pofile(file_path)
    except Exception as exception:
        raise FileNotFoundError(f'File "{file_path}" not found.') from exception


def _save_machine(file_path: str, po_data: POFile) -> None:
    """
    Save a POFile object to a MO file.

    :param file_path: Path to the MO file.
    :type file_path: str
    :param po_data: POFile object to be saved.
    :type po_data: POFile
    :raises FileNotFoundError: If the file path is invalid.
    """
    try:
        po_data.save(file_path)
    except Exception as exception:
        raise FileNotFoundError(f'File "{file_path}" not found.') from exception


# Catalog handling with Babel


def _load_catalog(file_path: str) -> Catalog:
    """
    Load a catalog from a PO file using Babel.

    :param file_path: Path to the PO file.
    :type file_path: str
    :return: Catalog object containing the PO file data.
    :rtype: Catalog
    :raises FileNotFoundError: If the file is not found.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as po_file:
            return read_po(po_file)
    except FileNotFoundError:
        raise FileNotFoundError(f'File "{file_path}" not found.')


def _save_catalog(file_path: str, catalog: Catalog) -> None:
    """
    Save a Catalog object to a PO file using Babel.

    :param file_path: Path to the PO file.
    :type file_path: str
    :param catalog: Catalog object to be saved.
    :type catalog: Catalog
    :raises IOError: If there is an error writing the file.
    """
    try:
        with open(file_path, "wb") as po_file:
            write_po(po_file, catalog)
    except Exception as exception:
        raise IOError(exception)


def _convert_catalog(file_path: str) -> None:
    """
    Convert a PO catalog to a MO catalog using Babel.

    :param file_path: Path to the PO file.
    :type file_path: str
    :raises IOError: If there is an error writing the file.
    """
    try:
        catalog = _load_catalog(file_path)
        with open(file_path, "wb") as mo_file:
            write_mo(mo_file, catalog)
    except Exception as exception:
        raise IOError(exception)


def _import_catalog(file_path: str) -> Catalog:
    """
    Load a catalog from a MO file using Babel.

    :param file_path: Path to the MO file.
    :type file_path: str
    :return: Catalog object containing the MO file data.
    :rtype: Catalog
    :raises FileNotFoundError: If the file is not found.
    """
    try:
        with open(file_path, "rb") as mo_file:
            return read_mo(mo_file)
    except FileNotFoundError:
        raise FileNotFoundError(f'File "{file_path}" not found.')


# Configuration file load and save


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


def _save_config_file(config_path: Path, data: dict) -> None:
    """
    Helper function to load the configuration file based on its extension.

    :param config_path: Path to the configuration file.
    :raises ValueError: If the file format is unsupported.
    :raises Exception: For errors during loading.
    :return: The configuration content as a dictionary.
    """
    [file_extension] = Path(config_path).suffixes

    try:
        with open(config_path, "w", encoding="utf-8") as cf:
            if file_extension == ".json":
                json.dump(data, cf, indent=4)
            elif file_extension in {".yaml", ".yml"}:
                yaml.safe_dump(data, cf, default_flow_style=False)
            elif file_extension == ".toml":
                toml.dump(data, cf)
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
    except ValueError as uff:
        raise uff
    except Exception as e:
        raise Exception(f"Error saving configuration file: {config_path}. {e}")


# Utility functions


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
