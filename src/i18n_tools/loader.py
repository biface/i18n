import os
import json
import yaml
import toml
from typing import Union, Optional
from pathlib import Path

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

def load_config(file_path: str) -> Optional[dict]:
    """
    Load configuration data from a file.

    Supports JSON, YAML, and TOML formats.

    :param file_path: Path to the configuration file.
    :return: A dictionary containing the configuration data, or None if the file does not exist.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Configuration file not found: {file_path}")

    ext = os.path.splitext(file_path)[-1].lower()
    with open(file_path, 'r', encoding='utf-8') as f:
        if ext == '.json':
            return json.load(f)
        elif ext in {'.yaml', '.yml'}:
            return yaml.safe_load(f)
        elif ext == '.toml':
            return toml.load(f)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

def save_config(file_path: str, data: dict) -> None:
    """
    Save configuration data to a file.

    Supports JSON, YAML, and TOML formats.

    :param file_path: Path to the configuration file.
    :param data: The dictionary containing configuration data.
    """
    ext = os.path.splitext(file_path)[-1].lower()
    with open(file_path, 'w', encoding='utf-8') as f:
        if ext == '.json':
            json.dump(data, f, indent=4)
        elif ext in {'.yaml', '.yml'}:
            yaml.safe_dump(data, f, default_flow_style=False)
        elif ext == '.toml':
            toml.dump(data, f)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
