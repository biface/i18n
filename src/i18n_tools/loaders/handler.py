from pathlib import Path
from typing import Union, Dict, Any
from babel.messages.catalog import Catalog
from .utils import (
    _exist_path,
    _build_path,
    _create_empty_file,
    _create_empty_json,
    _load_json,
    _save_json,
    _load_yaml,
    _save_yaml,
    _load_toml,
    _save_toml,
    _load_text,
    _save_text,
    _convert_catalog,
    _remove_file
)

def build_path(base_path: str, *sub_dirs: str) -> str:
    """
    Constructs, cleans, and validates a path by combining a base path with one or more subdirectories.

    This function ensures that the constructed path does not contain any elements
    that could corrupt the path, such as '..'. It also verifies that the path exists.

    :param base_path: The starting path.
    :type base_path: Union[Path, str]
    :param sub_dirs: One or more subdirectory names to append to the base path.
    :type sub_dirs: str
    :return: The combined, cleaned, and validated path as a string.
    :rtype: str
    :raises IOError: If the constructed path is invalid or does not exist.
    """
    # Construct the initial path
    constructed_path = _build_path(base_path, *sub_dirs)

    # Remove any '..' or other invalid elements
    cleaned_path = Path(*[part for part in constructed_path.parts if part != '..'])

    # Check if the cleaned path exists
    if not cleaned_path.exists():
        print(cleaned_path)
        raise IOError(f"The path '{cleaned_path}' does not exist.")

    return str(cleaned_path)


def file_exists(file_path: str) -> bool:
    """
    Checks if a file exists at the given path.

    This function verifies the existence of a file at the specified path.

    :param file_path: The path to the file.
    :type file_path: str
    :return: True if the file exists, False otherwise.
    :rtype: bool
    """
    return _exist_path(file_path)


def create_directory(path: str) -> None:
    """
    Creates a directory at the specified path.

    This function ensures that the directory and any necessary parent directories
    are created. If the directory already exists, no action is taken.

    :param path: The path to the directory to be created.
    :type path: str
    """
    Path(path).mkdir(parents=True, exist_ok=True)


def build_config_repository(app_root: str) -> None:
    """

    :param app_root:
    :return:
    """
    config_path = build_path(app_root, "locales", "_18n_tools")
    if not _exist_path(config_path):
        create_directory(config_path)

# Create operations

def create_template(base_path: str, module: str, domain: str) -> None:
    """
    Creates an empty template file for a given domain in the specified module.

    This function generates an empty template file (.pot) in the appropriate
    directory structure for the specified module and domain.

    :param base_path: The base path of the repository.
    :type base_path: str
    :param module: The module path.
    :type module: str
    :param domain: The domain name.
    :type domain: str
    """
    template_dir = Path(base_path) / module / "locales/templates"
    template_dir.mkdir(parents=True, exist_ok=True)
    template_file = template_dir / f"{domain}.pot"
    _create_empty_file(str(template_file))

def create_catalog(base_path: str, module: str, language: str, domain: str) -> None:
    """
    Creates an empty translation catalog for a given language and domain in the specified module.

    This function generates an empty translation catalog (.po) in the appropriate
    directory structure for the specified module, language, and domain.

    :param base_path: The base path of the repository.
    :type base_path: str
    :param module: The module path.
    :type module: str
    :param language: The language code.
    :type language: str
    :param domain: The domain name.
    :type domain: str
    """
    lang_dir = Path(base_path) / module / f"locales/{language}"
    lang_dir.mkdir(parents=True, exist_ok=True)
    catalog_file = lang_dir / f"{domain}.po"
    _save_text(str(catalog_file), Catalog())

def create_dictionary(base_path: str, module: str, language: str, domain: str) -> None:
    """
    Creates an empty translation dictionary for a given language and domain in the specified module.

    This function generates an empty translation dictionary (.json) in the appropriate
    directory structure for the specified module, language, and domain.

    :param base_path: The base path of the repository.
    :type base_path: str
    :param module: The module path.
    :type module: str
    :param language: The language code.
    :type language: str
    :param domain: The domain name.
    :type domain: str
    """
    lang_dir = Path(base_path) / module / f"locales/{language}"
    lang_dir.mkdir(parents=True, exist_ok=True)
    dictionary_file = lang_dir / f"{domain}.json"
    _create_empty_json(str(dictionary_file))

# Read operations

def fetch_template(base_path: str, module: str, domain: str) -> str:
    """
    Fetches the content of a template file.

    This function reads and returns the content of the specified template file.

    :param base_path: The base path of the repository.
    :type base_path: str
    :param module: The module path.
    :type module: str
    :param domain: The domain name.
    :type domain: str
    :return: The content of the template file.
    :rtype: str
    """
    template_file = Path(base_path) / module / f"locales/templates/{domain}.pot"
    if template_file.exists():
        with open(template_file, "r", encoding="utf-8") as file:
            return file.read()
    return ""

def fetch_catalog(base_path: str, module: str, language: str, domain: str) -> Catalog:
    """
    Fetches the translation catalog for a given language and domain.

    This function reads and returns the translation catalog from the specified .po file.

    :param base_path: The base path of the repository.
    :type base_path: str
    :param module: The module path.
    :type module: str
    :param language: The language code.
    :type language: str
    :param domain: The domain name.
    :type domain: str
    :return: The translation catalog.
    :rtype: Catalog
    """
    catalog_file = Path(base_path) / module / f"locales/{language}/{domain}.po"
    return _load_text(str(catalog_file)) if catalog_file.exists() else Catalog()

def fetch_dictionary(base_path: str, module: str, language: str, domain: str) -> Dict[str, Any]:
    """
    Fetches the translation dictionary for a given language and domain.

    This function reads and returns the translation dictionary from the specified .json file.

    :param base_path: The base path of the repository.
    :type base_path: str
    :param module: The module path.
    :type module: str
    :param language: The language code.
    :type language: str
    :param domain: The domain name.
    :type domain: str
    :return: The translation dictionary.
    :rtype: Dict[str, Any]
    """
    dictionary_file = Path(base_path) / module / f"locales/{language}/{domain}.json"
    return _load_json(str(dictionary_file)) if dictionary_file.exists() else {}

# Update operations

def update_catalog(base_path: str, module: str, language: str, domain: str, catalog: Catalog) -> None:
    """
    Updates the translation catalog for a given language and domain.

    This function saves the provided translation catalog to the specified .po file
    and updates the corresponding .mo file.

    :param base_path: The base path of the repository.
    :type base_path: str
    :param module: The module path.
    :type module: str
    :param language: The language code.
    :type language: str
    :param domain: The domain name.
    :type domain: str
    :param catalog: The new translation catalog.
    :type catalog: Catalog
    """
    catalog_file = Path(base_path) / module / f"locales/{language}/{domain}.po"
    _save_text(str(catalog_file), catalog)
    _convert_catalog(str(catalog_file))  # Update the .mo file

def update_dictionary(base_path: str, module: str, language: str, domain: str, data: Dict[str, Any]) -> None:
    """
    Updates the translation dictionary for a given language and domain.

    This function saves the provided translation dictionary to the specified .json file.

    :param base_path: The base path of the repository.
    :type base_path: str
    :param module: The module path.
    :type module: str
    :param language: The language code.
    :type language: str
    :param domain: The domain name.
    :type domain: str
    :param data: The new translation dictionary.
    :type data: Dict[str, Any]
    """
    dictionary_file = Path(base_path) / module / f"locales/{language}/{domain}.json"
    _save_json(str(dictionary_file), data)

# Delete operations

def remove_template(base_path: str, module: str, domain: str) -> None:
    """
    Removes a template file for a given domain in the specified module.

    This function deletes the specified template file if it exists.

    :param base_path: The base path of the repository.
    :type base_path: str
    :param module: The module path.
    :type module: str
    :param domain: The domain name.
    :type domain: str
    :raises FileNotFoundError: If the template file does not exist.
    """
    template_file = build_path(base_path, module, "locales/templates", f"{domain}.pot")
    try:
        _remove_file(template_file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Template file not found: {template_file}")

def remove_catalog(base_path: str, module: str, language: str, domain: str) -> None:
    """
    Removes a translation catalog and its corresponding machine file for a given language and domain in the specified module.

    This function deletes the specified .po and .mo files if they exist.

    :param base_path: The base path of the repository.
    :type base_path: str
    :param module: The module path.
    :type module: str
    :param language: The language code.
    :type language: str
    :param domain: The domain name.
    :type domain: str
    :raises FileNotFoundError: If the catalog or machine file does not exist.
    """
    catalog_file = build_path(base_path, module, f"locales/{language}", f"{domain}.po")
    try:
        _remove_file(catalog_file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Catalog file not found: {catalog_file}")

    machine_file = build_path(base_path, module, f"locales/{language}", f"{domain}.mo")
    try:
        _remove_file(machine_file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Machine file not found: {machine_file}")

def remove_dictionary(base_path: str, module: str, language: str, domain: str) -> None:
    """
    Removes a translation dictionary for a given language and domain in the specified module.

    This function deletes the specified .json file if it exists.

    :param base_path: The base path of the repository.
    :type base_path: str
    :param module: The module path.
    :type module: str
    :param language: The language code.
    :type language: str
    :param domain: The domain name.
    :type domain: str
    :raises FileNotFoundError: If the dictionary file does not exist.
    """
    dictionary_file = build_path(base_path, module, f"locales/{language}", f"{domain}.json")
    try:
        _remove_file(dictionary_file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Dictionary file not found: {dictionary_file}")
