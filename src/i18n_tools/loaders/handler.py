from pathlib import Path
from typing import Any, Dict, List, Union

from babel import __version__ as babel_version
from babel.core import Locale
from babel.messages.catalog import Catalog, Message
from ndict_tools import NestedDictionary

import i18n_tools
from i18n_tools.__static__ import (
    I18N_TOOLS_CONFIG,
    I18N_TOOLS_LOCALE,
    I18N_TOOLS_MESSAGES,
    I18N_TOOLS_TEMPLATE,
)

from .utils import (
    _build_path,
    _check_domains,
    _convert_catalog,
    _create_directory,
    _create_empty_json,
    _exist_path,
    _load_config_file,
    _load_json,
    _load_text,
    _remove_file,
    _save_config_file,
    _save_json,
    _save_text,
)


def check_json_integrity(data: Dict[str, Any]) -> bool:
    """
    Check the integrity of the JSON locale data.

    :param data: The JSON locale data.
    :type data: dict
    :return: True if the data is valid, False otherwise.
    :rtype: bool
    """

    for key, value in data.items():
        if key != ".i18n_tools":
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
    cleaned_path = Path(*[part for part in constructed_path.parts if part != ".."])

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
    _create_directory(path)


# Create operations


def create_template(repository: NestedDictionary, module: str, domain: str) -> None:
    """
    Creates an empty template file for a given domain in the specified module.

    This function generates an empty template file (.pot) in the appropriate
    directory structure for the specified module and domain.

    :param repository: The data structure representing the translation repository.
    :type repository: NestedDictionary
    :param module: The module path.
    :type module: str
    :param domain: The domain name.
    :type domain: str
    """
    try:
        _check_domains(repository, module, [domain])
        path = build_path(
            repository[["paths", "repository"]],
            module,
            I18N_TOOLS_LOCALE,
            I18N_TOOLS_TEMPLATE,
        )
        catalog = Catalog(
            project=repository[["details", "name"]],
            version=repository[["details", "version"]],
            copyright_holder=f"i18n-tools ({i18n_tools.__version__}) builder",
            msgid_bugs_address=repository[["details", "report-bugs-to"]],
            fuzzy=(
                True if repository[["details", "flags", "fuzzy"]] == "True" else False
            ),
        )
        catalog.header_comment = f"""
# This POT file is generated for PROJECT project.
# By ORGANIZATION and is dedicated to {domain} domain
# of translations in {module} module of PROJECT project.
#
# The aim of this project is described as :
# {repository[["details", "description"]]}
#
# It will be used as a template for translation of {domain} domain
# in specific language.
#
# This file is distributed under the same license as the PROJECT
# project.
"""
        catalog.domain = domain
        catalog.mime_headers = [
            (
                "Project-Id-Version",
                f"{repository[['details','name']]} {repository[['details','version']]}",
            ),
            ("Report-Msgid-Bugs-To", repository[["details", "report-bugs-to"]]),
            ("POT-Creation-Date", repository[["details", "creation_date"]]),
            ("PO-Revision-Date", "YEAR-MO-DA HO:MI+ZONE"),
            ("Last-Translator", ""),
            ("Language-Team", repository[["details", "language_team"]]),
            ("Language", ""),
            ("MIME-Version", "1.0"),
            (
                "Content-Type",
                f"{repository[['details','content_type']]}; charset=utf-8",
            ),
            ("Content-Transfer-Encoding", "8bit"),
            (
                "Generated-By",
                f"i18n-tools ({i18n_tools.__version__}) using Babel ({babel_version})",
            ),
        ]

        template_file = path + f"/{domain}.pot"
        if not _exist_path(template_file):
            _save_text(template_file, catalog)
        else:
            raise FileExistsError(
                f"The path '{template_file}' already exists. You cannot overwrite it."
            )

    except Exception as e:
        raise e


def create_catalog(
    repository: NestedDictionary, module: str, language: str, domain: str
) -> None:
    """
    Creates an empty translation catalog for a given language and domain in the specified module.

    This function generates an empty translation catalog (.po) in the appropriate
    directory structure for the specified module, language, and domain.

    :param repository: The data structure representing the translation repository.
    :type repository: NestedDictionary
    :param module: The module path.
    :type module: str
    :param language: The language code.
    :type language: str
    :param domain: The domain name.
    :type domain: str
    """

    try:
        _check_domains(repository, module, [domain])
        path = build_path(
            repository[["paths", "repository"]],
            module,
            I18N_TOOLS_LOCALE,
            language,
            I18N_TOOLS_MESSAGES,
        )
        catalog = fetch_template(repository, module, domain)
        catalog_path = path + f"/{domain}.po"
        catalog.locale = Locale.parse(language, sep="-")
        catalog.domain = domain
        if not _exist_path(catalog_path):
            _save_text(catalog_path, catalog)
            _convert_catalog(catalog_path)
        else:
            raise FileExistsError(
                f"The path '{catalog_path}' already exists. You cannot overwrite it"
            )
    except Exception as e:
        raise e


def create_dictionary(
    repository: NestedDictionary, module: str, language: str, domain: str
) -> None:
    """
    Creates an empty translation dictionary for a given language and domain in the specified module.

    This function generates an empty translation dictionary (.json) in the appropriate
    directory structure for the specified module, language, and domain.

    :param repository: The data structure representing the translation repository.
    :type repository: NestedDictionary
    :param module: The module path.
    :type module: str
    :param language: The language code.
    :type language: str
    :param domain: The domain name.
    :type domain: str
    """
    try:
        _check_domains(repository, module, [domain])
        path = build_path(
            repository[["paths", "repository"]],
            module,
            I18N_TOOLS_LOCALE,
            language,
            I18N_TOOLS_MESSAGES,
        )
        dictionary_path = path + f"/{domain}.json"
        if not _exist_path(dictionary_path):
            _save_json(
                dictionary_path, {}
            )
        else:
            raise FileExistsError(
                f"The path '{dictionary_path}' already exists. You cannot overwrite it"
            )
    except Exception as e:
        raise e


# Read operations


def fetch_template(repository: NestedDictionary, module: str, domain: str) -> Catalog:
    """
    Fetches the content of a template file.

    This function reads and returns the content of the specified template file.

    :param repository: The data structure representing the translation repository.
    :type repository: NestedDictionary
    :param module: The module path.
    :type module: str
    :param domain: The domain name.
    :type domain: str
    :return: The content of the template file.
    :rtype: str
    """

    try:
        _check_domains(repository, module, [domain])
        path = build_path(
            repository[["paths", "repository"]],
            module,
            I18N_TOOLS_LOCALE,
            I18N_TOOLS_TEMPLATE,
        )
        template_file = path + f"/{domain}.pot"
        catalog = _load_text(template_file)
        catalog.domain = domain
        catalog.copyright_holder = "i18n-tools builder"
    except Exception as e:
        raise e

    return catalog


def fetch_catalog(
    repository: NestedDictionary, module: str, language: str, domain: str
) -> Catalog:
    """
    Fetches the translation catalog for a given language and domain.

    This function reads and returns the translation catalog from the specified .po file.

    :param repository: The data structure representing the translation repository.
    :type repository: NestedDictionary
    :param module: The module path.
    :type module: str
    :param language: The language code.
    :type language: str
    :param domain: The domain name.
    :type domain: str
    :return: The translation catalog.
    :rtype: Catalog
    """
    try:
        _check_domains(repository, module, [domain])
        path = build_path(
            repository[["paths", "repository"]],
            module,
            I18N_TOOLS_LOCALE,
            language,
            I18N_TOOLS_MESSAGES,
        )
        catalog_path = path + f"/{domain}.po"
        catalog = _load_text(catalog_path)
        catalog.domain = domain
        catalog.copyright_holder = "i18n-tools builder"
    except Exception as e:
        raise e

    return catalog


def fetch_dictionary(
    repository: NestedDictionary, module: str, language: str, domain: str
) -> Dict[str, Any]:
    """
    Fetches the translation dictionary for a given language and domain.

    This function reads and returns the translation dictionary from the specified .json file.

    :param repository: The data structure representing the translation repository.
    :type repository: NestedDictionary
    :param module: The module path.
    :type module: str
    :param language: The language code.
    :type language: str
    :param domain: The domain name.
    :type domain: str
    :return: The translation dictionary.
    :rtype: Dict[str, Any]
    """

    try:
        _check_domains(repository, module, [domain])
        path = build_path(
            repository[["paths", "repository"]],
            module,
            I18N_TOOLS_LOCALE,
            language,
            I18N_TOOLS_MESSAGES,
        )
        dictionary_path = path + f"/{domain}.json"
        dictionary = _load_json(dictionary_path)
    except Exception as e:
        raise e

    return dictionary


# Update operations


def update_catalog(
    repository: NestedDictionary,
    module: str,
    language: str,
    domain: str,
    data: Dict[any, Dict[str, str]],
) -> None:
    """
    Updates the translation catalog for a given language and domain.

    This function saves the provided translation catalog to the specified .po file
    and updates the corresponding .mo file.

    :param repository: The data structure representing the translation repository.
    :type repository: NestedDictionary
    :param module: The module path.
    :type module: str
    :param language: The language code.
    :type language: str
    :param domain: The domain name.
    :type domain: str
    :param data: An adapted translation dictionary.
    :type data: Dict[str, Dict[str, str]]
    """

    #TODO: Must update template file as well

    try:
        _check_domains(repository, module, [domain])
        path = build_path(
            repository[["paths", "repository"]],
            module,
            I18N_TOOLS_LOCALE,
            language,
            I18N_TOOLS_MESSAGES,
        )
        catalog_path = path + f"/{domain}.po"
        catalog = _load_text(catalog_path)

        for key, value in data.items():
            if isinstance(value, dict):
                # Handle pluralizable messages
                string_value = value.get("string", "")

                # If the key is a tuple/list (pluralizable) and the string is not,
                # convert the string to a tuple with appropriate number of elements
                if isinstance(key, (tuple, list)) and not isinstance(
                    string_value, (tuple, list)
                ):
                    # For pluralizable messages, string should be a tuple/list
                    # with the same number of elements as the key
                    if string_value:
                        # If we have a string, use it as the first element (singular form)
                        # and add empty strings for the plural forms
                        string_value = tuple([string_value] + [""] * (len(key) - 1))
                    else:
                        # If we don't have a string, create a tuple with empty strings
                        string_value = tuple([""] * len(key))

                message = catalog.add(
                    id=key,
                    string=string_value,
                    locations=value.get("locations", ()),
                    previous_id=value.get("previous_id", ""),
                    flags=["python-format"],
                )

            else:
                raise ValueError(f"{value} is not a dictionary")

        _save_text(catalog_path, catalog)
        _convert_catalog(catalog_path)

    except Exception as e:
        raise e


def update_dictionary(
    repository: NestedDictionary,
    module: str,
    language: str,
    domain: str,
    data: Dict[str, Any],
) -> None:
    """
    Updates the translation dictionary for a given language and domain.

    This function saves the provided translation dictionary to the specified .json file.

    :param repository: The data structure representing the translation repository.
    :type repository: NestedDictionary
    :param module: The module path.
    :type module: str
    :param language: The language code.
    :type language: str
    :param domain: The domain name.
    :type domain: str
    :param data: The new translation dictionary.
    :type data: Dict[str, Any]
    """

    try:
        _check_domains(repository, module, [domain])
        path = build_path(
            repository[["paths", "repository"]],
            module,
            I18N_TOOLS_LOCALE,
            language,
            I18N_TOOLS_MESSAGES,
        )
        dictionary_path = path + f"/{domain}.json"
        dictionary = _load_json(dictionary_path)

        if not check_json_integrity(data):
            raise ValueError(
                f"The dictionary {data} is not compatible with i18n-tools translations"
            )

        for key, item in data.items():
            dictionary[key] = item

        _save_json(dictionary_path, dictionary)

    except Exception as e:
        raise e


# Delete operations


def remove_template(repository: NestedDictionary, module: str, domain: str) -> None:
    """
    Removes a template file for a given domain in the specified module.

    This function deletes the specified template file if it exists.

    :param repository: The data structure representing the translation repository.
    :type repository: NestedDictionary
    :param module: The module path.
    :type module: str
    :param domain: The domain name.
    :type domain: str
    :raises FileNotFoundError: If the template file does not exist.
    """

    try:
        _check_domains(repository, module, [domain])
        path = build_path(
            repository[["paths", "repository"]],
            module,
            I18N_TOOLS_LOCALE,
            I18N_TOOLS_TEMPLATE,
        )
        template_path = path + f"/{domain}.pot"
        _remove_file(template_path)
    except Exception as e:
        raise e


def remove_catalog(
    repository: NestedDictionary, module: str, language: str, domain: str
) -> None:
    """
    Removes a translation catalog and its corresponding machine file for a given language and domain in the specified module.

    This function deletes the specified .po and .mo files if they exist.

    :param repository: The data structure representing the translation repository.
    :type repository: NestedDictionary
    :param module: The module path.
    :type module: str
    :param language: The language code.
    :type language: str
    :param domain: The domain name.
    :type domain: str
    :raises FileNotFoundError: If the catalog or machine file does not exist.
    """

    try:
        path = build_path(
            repository[["paths", "repository"]],
            module,
            I18N_TOOLS_LOCALE,
            language,
            I18N_TOOLS_MESSAGES,
        )
        catalog_path = path + f"/{domain}.po"
        machine_path = path + f"/{domain}.mo"
        _remove_file(catalog_path)
        _remove_file(machine_path)
    except Exception as e:
        raise e


def remove_dictionary(
    repository: NestedDictionary, module: str, language: str, domain: str
) -> None:
    """
    Removes a translation dictionary for a given language and domain in the specified module.

    This function deletes the specified .json file if it exists.

    :param repository: The data structure representing the translation repository.
    :type repository: NestedDictionary
    :param module: The module path.
    :type module: str
    :param language: The language code.
    :type language: str
    :param domain: The domain name.
    :type domain: str
    :raises FileNotFoundError: If the dictionary file does not exist.
    """
    try:
        _check_domains(repository, module, [domain])
        path = build_path(
            repository[["paths", "repository"]],
            module,
            I18N_TOOLS_LOCALE,
            language,
            I18N_TOOLS_MESSAGES,
        )
        dictionary_path = path + f"/{domain}.json"
        _remove_file(dictionary_path)
    except Exception as e:
        raise e


# Managing configuration files


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
        if not _exist_path(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        return _load_config_file(config_path)

    # Sinon, rechercher dans les répertoires applicatifs (racine et répertoires locaux)
    search_dirs = [
        Path.cwd(),  # Répertoire racine de l'application
        Path.cwd() / I18N_TOOLS_LOCALE,  # Sous-répertoire locales de l'application
        Path.cwd()
        / I18N_TOOLS_LOCALE
        / I18N_TOOLS_CONFIG,  # Sous-répertoire configuration
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

    _save_config_file(file_path, data)
