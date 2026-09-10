"""
Low-level, private, and internal functions for loading and saving the
*settings file* — the TOML/YAML/JSON descriptor backing Config/Repository
(DD-18, DD-19, DD-20). Dispatch is by file extension.

Split out of loaders/utils.py (DD-41, #119): core `.i18t` usage
(Message/Book/Corpus/Encyclopaedia/formatter) never touches the settings
file and must not need `toml` — only reading or writing a `.toml`
settings file does. `toml` is therefore imported lazily, inside the
`.toml`-specific branch of each function, with a friendly
ModuleNotFoundError pointing at `pip install pyi18t-tools[api]` (same
pattern as api.py, config.py — DD-41, #118). Because `toml` is never
imported at module level here, importing this module — or importing
loaders/handler.py, which imports it — never requires `toml`.
`.yaml`/`.json` settings files remain fully usable without the `api`
extra.

Key Responsibilities:
    - Provide low-level functions for loading and saving the settings file.
    - Dispatch to the right serialisation format by file extension.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from .utils import __check_path


def __check_config_extension(ext: str) -> bool:
    return ext.lstrip(".").lower() in ["json", "yaml", "yml", "toml"]


def _load_toml(file_path: Path | str) -> dict[str, Any]:
    """
    Load a TOML file without managing data structure and returns its content.

    Requires the ``api`` extra (``toml``). Imported lazily so that core
    .i18t usage never pulls this dependency in (DD-41).

    :param file_path:
    :return:
    :raises ModuleNotFoundError: if the ``api`` extra is not installed.
    """
    try:
        import toml
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            "_load_toml() requires the 'api' extra — "
            "install with: pip install pyi18t-tools[api]"
        ) from e

    file_path = __check_path(file_path)

    with open(file_path, "r", encoding="utf-8") as toml_file:
        return toml.load(toml_file)


def _save_toml(file_path: Path | str, data: dict[str, Any]) -> None:
    """
    Save a TOML file without managing data structure and returns its content.

    Requires the ``api`` extra (``toml``). Imported lazily so that core
    .i18t usage never pulls this dependency in (DD-41).

    :param file_path:
    :param data:
    :return:
    :raises ModuleNotFoundError: if the ``api`` extra is not installed.
    """
    try:
        import toml
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            "_save_toml() requires the 'api' extra — "
            "install with: pip install pyi18t-tools[api]"
        ) from e

    file_path = __check_path(file_path)
    with open(file_path, "w", encoding="utf-8") as toml_file:
        toml.dump(data, toml_file)


def _load_config_file(config_path: Path | str) -> dict[str, Any]:
    """
    Helper function to load the configuration file based on its extension.

    The ``.toml`` branch requires the ``api`` extra (``toml``), imported
    lazily — ``.yaml``/``.json`` settings files need no extra (DD-41).

    :param config_path: Path to the configuration file.
    :raises ValueError: If the file format is unsupported.
    :raises FileNotFoundError: If the file does not exist.
    :raises ModuleNotFoundError: if reading a '.toml' file without the ``api`` extra.
    :return: The configuration content as a dictionary.
    """

    config_path = __check_path(config_path)
    [file_extension] = config_path.suffixes

    if not __check_config_extension(file_extension):
        raise ValueError(f"Unsupported configuration file format: {file_extension}")

    with open(config_path, "r", encoding="utf-8") as file:
        if file_extension in {".yaml", ".yml"}:
            return yaml.safe_load(file)
        elif file_extension == ".toml":
            try:
                import toml
            except ModuleNotFoundError as e:
                raise ModuleNotFoundError(
                    "_load_config_file(): reading a '.toml' settings file "
                    "requires the 'api' extra — "
                    "install with: pip install pyi18t-tools[api]"
                ) from e
            return toml.load(file)
        elif file_extension == ".json":
            return json.load(file)
    return (
        {}
    )  # unreachable if __check_config_extension passed, but satisfies type checker


def _save_config_file(config_path: Path | str, data: dict[str, Any]) -> None:
    """
    Helper function to save the configuration file based on its extension.

    The ``.toml`` branch requires the ``api`` extra (``toml``), imported
    lazily — ``.yaml``/``.json`` settings files need no extra (DD-41).

    :param config_path: Path to the configuration file.
    :raises ValueError: If the file format is unsupported.
    :raises ModuleNotFoundError: if writing a '.toml' file without the ``api`` extra.
    :return: None
    """

    config_path = __check_path(config_path)
    [file_extension] = config_path.suffixes

    if not __check_config_extension(file_extension):
        raise ValueError(f"Unsupported configuration file format: {file_extension}")

    with open(config_path, "w", encoding="utf-8") as cf:
        if file_extension == ".json":
            json.dump(data, cf, indent=4)
        elif file_extension in {".yaml", ".yml"}:
            yaml.safe_dump(data, cf, default_flow_style=False)
        elif file_extension == ".toml":
            try:
                import toml
            except ModuleNotFoundError as e:
                raise ModuleNotFoundError(
                    "_save_config_file(): writing a '.toml' settings file "
                    "requires the 'api' extra — "
                    "install with: pip install pyi18t-tools[api]"
                ) from e
            toml.dump(data, cf)
