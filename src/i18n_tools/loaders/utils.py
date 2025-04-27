"""
Files management module
=======================

This module contains private utility functions to manage files. These functions are not meant to be used directly.
They are intended to be used by other functions in this module.

"""

import gzip
import json
import os
import shutil
import tarfile
from pathlib import Path
from typing import Any, Dict, List, Union

import toml
import yaml
from babel.messages.catalog import Catalog
from babel.messages.mofile import read_mo, write_mo
from babel.messages.pofile import read_po, write_po
from ndict_tools import NestedDictionary

# Generic empty files


def __check_config_extension(ext: str) -> bool:
    return ext.lstrip(".").lower() in ["json", "yaml", "yml", "toml"]


def __check_path(file_path: Union[Path, str]) -> Path:
    if isinstance(file_path, str):
        file_path = Path(file_path)
    return file_path


def _exist_path(path: Union[Path, str]) -> bool:
    path = __check_path(path)
    return path.exists()


def _is_absolute_path(path: Union[Path, str]) -> bool:
    path = __check_path(path)
    return path.is_absolute()


def _create_empty_file(file_path: Union[Path, str]) -> None:
    """
    Create an empty file.

    :param file_path: a path to a file.
    :type file_path: str
    :return: Nothing
    :rtype: None
    :raises FileNotFoundError: File not found.
    """

    file_path = __check_path(file_path)

    try:
        with open(file_path, "w", encoding="utf-8") as empty_file:
            empty_file.write("")
    except Exception as exception:
        raise FileNotFoundError(f'File "{file_path}" not found.') from exception


def _create_directory(file_path: Union[Path, str]) -> None:
    """
    Create a directory.

    :param file_path:
    :type file_path: str
    :return: nothing
    :rtype: None
    :raises FileExistsError: directory already exists.
    """
    file_path = __check_path(file_path)

    if not file_path.is_dir():
        file_path.mkdir(parents=True, exist_ok=True)
    else:
        raise FileExistsError(f'Directory "{file_path}" already exists.')


# JSON load and save files


def _create_empty_json(file_path: Union[Path, str]) -> None:
    """
    Create an empty JSON file without managing data structure and integrity and returns its content.

    :param file_path: JSON file path.
    :type file_path: str
    :return: Nothing
    :rtype: None
    :raises FileNotFoundError: File not found.
    """

    file_path = __check_path(file_path)

    try:
        with open(file_path, "w", encoding="utf-8") as json_file:
            json.dump({}, json_file, ensure_ascii=False, indent=4)
    except Exception as exception:
        raise FileNotFoundError(f'File "{file_path}" not found.') from exception


def _load_json(file_path: Union[Path, str]) -> Dict[str, Any]:
    """
    Load a JSON file without managing data structure and integrity and returns its content as a dictionary.

    :param file_path: Path to the JSON file.
    :type file_path: str
    :return: JSON Translation data content.
    :rtype: dict
    :raises FileNotFoundError: File not found.
    """

    file_path = __check_path(file_path)

    try:
        with open(file_path, "r", encoding="utf-8") as json_file:
            return json.load(json_file)
    except Exception as exception:
        raise FileNotFoundError(f'File "{file_path}" not found.') from exception


def _save_json(file_path: Union[Path, str], data: Dict[str, Any]) -> None:
    """
    Save a JSON file without managing data structure and integrity and returns its content.

    :param file_path: Path to the JSON file.
    :type file_path: str
    :param data: JSON Translation data content.
    :type data: dict
    :return: None
    :raises FileNotFoundError: File not found.
    """

    file_path = __check_path(file_path)

    try:
        with open(file_path, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)
    except Exception as exception:
        raise FileNotFoundError(f'File "{file_path}" not found.') from exception


def _load_yaml(file_path: Union[Path, str]) -> Dict[str, Any]:
    """
    Load a
    :param file_path:
    :return:
    """
    file_path = __check_path(file_path)

    try:
        with open(file_path, "r", encoding="utf-8") as yaml_file:
            return yaml.load(yaml_file, Loader=yaml.SafeLoader)
    except Exception as exception:
        raise FileNotFoundError(f'File "{file_path}" not found.') from exception


def _save_yaml(file_path: Union[Path, str], data: Dict[str, Any]) -> None:
    """
    Save a
    :param file_path:
    :param data:
    :return:
    """
    file_path = __check_path(file_path)

    try:
        with open(file_path, "w", encoding="utf-8") as yaml_file:
            yaml.dump(data, yaml_file, Dumper=yaml.SafeDumper)
    except Exception as exception:
        raise FileNotFoundError(f'File "{file_path}" not found.') from exception


def _load_toml(file_path: Union[Path, str]) -> Dict[str, Any]:
    """
    Load a TOML file without managing data structure and returns its content.
    :param file_path:
    :return:
    """
    file_path = __check_path(file_path)

    try:
        with open(file_path, "r", encoding="utf-8") as toml_file:
            return toml.load(toml_file)
    except Exception as exception:
        raise FileNotFoundError(f'File "{file_path}" not found.') from exception


def _save_toml(file_path: Union[Path, str], data: Dict[str, Any]) -> None:
    """
    Save a TOML file without managing data structure and returns its content.
    :param file_path:
    :param data:
    :return:
    """
    file_path = __check_path(file_path)
    try:
        with open(file_path, "w", encoding="utf-8") as toml_file:
            toml.dump(data, toml_file)
    except Exception as exception:
        raise FileNotFoundError(f'File "{file_path}" not found.') from exception


# PO file handling with polib


def _load_text(file_path: Union[Path, str]) -> Catalog:
    """
    Load a catalog from a PO file using Babel.

    :param file_path: Path to the PO file.
    :type file_path: str
    :return: Catalog object containing the PO file data.
    :rtype: Catalog
    :raises FileNotFoundError: If the file is not found.
    """

    file_path = __check_path(file_path)

    try:
        with open(file_path, "r", encoding="utf-8") as po_file:
            return read_po(po_file)
    except FileNotFoundError:
        raise FileNotFoundError(f'File "{file_path}" not found.')


def _save_text(file_path: Union[Path, str], catalog: Catalog) -> None:
    """
    Save a Catalog object to a PO file using Babel.

    :param file_path: Path to the PO file.
    :type file_path: str
    :param catalog: Catalog object to be saved.
    :type catalog: Catalog
    :raises IOError: If there is an error writing the file.
    """

    file_path = __check_path(file_path)

    try:
        with open(file_path, "wb") as po_file:
            write_po(po_file, catalog, sort_output=True, include_previous=False)
    except Exception as exception:
        raise FileNotFoundError(f'File "{file_path}" not found.') from exception


# MO file handling with polib


def _load_machine(file_path: Union[Path, str]) -> Catalog:
    """
    Load a catalog from a MO file using Babel.

    :param file_path: Path to the MO file.
    :type file_path: str
    :return: Catalog object containing the MO file data.
    :rtype: Catalog
    :raises FileNotFoundError: If the file is not found.
    """

    file_path = __check_path(file_path)

    try:
        with open(file_path, "rb") as mo_file:
            return read_mo(mo_file)
    except FileNotFoundError:
        raise FileNotFoundError(f'File "{file_path}" not found.')


def _save_machine(file_path: Union[Path, str], catalog: Catalog) -> None:
    """
    Save a POFile object to a MO file.

    :param file_path: Path to the MO file.
    :type file_path: str
    :param catalog: POFile object to be saved.
    :type catalog: POFile
    :raises FileNotFoundError: If the file path is invalid.
    """

    file_path = __check_path(file_path)

    try:
        with open(file_path, "wb") as mo_file:
            write_mo(mo_file, catalog)
    except Exception as exception:
        raise FileNotFoundError(f'File "{file_path}" not found.') from exception


def _convert_catalog(file_path: Union[Path, str]) -> None:
    """
    Convert a PO catalog to a MO catalog using Babel.

    :param file_path: Path to the PO file.
    :type file_path: str
    :raises IOError: If there is an error writing the file.
    """

    file_path = __check_path(file_path)

    try:
        catalog = _load_text(file_path)
        mo_file_path = file_path.with_suffix(".mo")
        with open(mo_file_path, "wb") as mo_file:
            write_mo(mo_file, catalog)
    except Exception as exception:
        raise IOError(
            f'Error converting file "{file_path}" to MO format.'
        ) from exception


# Configuration file load and save


def _load_config_file(config_path: Union[Path, str]) -> dict:
    """
    Helper function to load the configuration file based on its extension.

    :param config_path: Path to the configuration file.
    :raises ValueError: If the file format is unsupported.
    :raises Exception: For errors during loading.
    :return: The configuration content as a dictionary.
    """

    config_path = __check_path(config_path)
    [file_extension] = config_path.suffixes

    try:
        if not __check_config_extension(file_extension):
            raise ValueError(f"Unsupported configuration file format: {file_extension}")
        else:
            with open(config_path, "r", encoding="utf-8") as file:
                if file_extension == ".yaml":
                    return yaml.safe_load(file)
                elif file_extension == ".toml":
                    return toml.load(file)
                elif file_extension == ".json":
                    return json.load(file)
    except Exception as e:
        raise Exception(f"Error loading configuration file: {config_path}. {e}")


def _save_config_file(config_path: Union[Path, str], data: dict) -> None:
    """
    Helper function to load the configuration file based on its extension.

    :param config_path: Path to the configuration file.
    :raises ValueError: If the file format is unsupported.
    :raises Exception: For errors during loading.
    :return: The configuration content as a dictionary.
    """

    config_path = __check_path(config_path)
    [file_extension] = config_path.suffixes

    try:
        if not __check_config_extension(file_extension):
            raise ValueError(f"Unsupported configuration file format: {file_extension}")
        else:
            with open(config_path, "w", encoding="utf-8") as cf:
                if file_extension == ".json":
                    json.dump(data, cf, indent=4)
                elif file_extension in {".yaml", ".yml"}:
                    yaml.safe_dump(data, cf, default_flow_style=False)
                elif file_extension == ".toml":
                    toml.dump(data, cf)
    except ValueError as uff:
        raise uff
    except Exception as e:
        raise Exception(f"Error saving configuration file: {config_path}. {e}")


# Utility functions


def _build_path(base_path: Union[Path, str], *sub_dirs: str) -> Path:
    """
    Constructs a path by combining a base path with one or more subdirectories.

    This function takes a base path and appends one or more subdirectory names to it,
    resolving the final path as an absolute path.

    :param base_path: The starting path.
    :type base_path: Union[Path, str]
    :param sub_dirs: One or more subdirectory names to append to the base path.
    :type sub_dirs: str
    :return: The combined path as a Path object.
    :rtype: Path
    """
    if isinstance(base_path, str):
        base_path = Path(base_path)

    for sub_dir in sub_dirs:
        base_path /= sub_dir
    return base_path.resolve()


def _create_tar_gz(
    base_path: Union[Path, str],
    archive_name: str,
    directory_to_archive: Union[Path, str],
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
    base_path = __check_path(base_path)
    directory_to_archive = __check_path(directory_to_archive)
    tarfile_path = base_path / archive_name

    with tarfile.open(tarfile_path, "w:gz") as tar:
        tar.add(directory_to_archive, arcname=directory_to_archive.name)


def _create_gzip(file_path: Union[Path, str]) -> None:
    """
    Create a compressed file using gzip fonctions.
    :param file_path: a path to a file.
    :type file_path: str
    :return: Nothing
    :rtype: None
    """
    file_path = __check_path(file_path)
    gz_file = file_path.with_suffix(file_path.suffix + ".gz")
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


def _remove_file(file_path: Union[Path, str]) -> None:
    """

    :param file_path:
    :return:
    """
    file_path = __check_path(file_path)

    if file_path.exists():
        os.remove(file_path)
    else:
        raise FileNotFoundError(f'File "{file_path}" not found.')


# Other module specific and private tools


def _check_module(repository: NestedDictionary, module_list: List[str]) -> bool:
    """
    This function verify that a module or a list of modules are defined in the repository.
    :param repository: data representing the translation repository.
    :type repository: NestedDictionary
    :param module_list: The list of modules to verify.
    :type module_list: List[str]
    :return: True (if not raised)
    :rtype: bool
    :raises: ValueError
    """
    for module in module_list:
        if module not in repository[["paths", "modules"]]:
            raise ValueError(
                f'Module "{module}" not found in repository : "{repository[["paths", "modules"]]}".'
            )

    return True


def _check_domains(
    repository: NestedDictionary, module: str, domain_list: List[str]
) -> bool:
    """
    This function verify that a domain or a list of domains are defined in the repository.
    :param repository: data representing the translation repository.
    :type repository: NestedDictionary
    :param module: The module containing domains.
    :type module: str
    :param domain_list: The list of domains to verify.
    :type domain_list: List[str]
    :return: True
    :rtype: bool
    :raises: ValueError
    """
    try:
        _check_module(repository, [module])
        for domain in domain_list:
            if domain not in repository[["domains", module]]:
                raise ValueError(
                    f"Domain {domain} not found in repository : {repository[['domains', module]]}"
                )
    except ValueError as e:
        raise e

    return True
