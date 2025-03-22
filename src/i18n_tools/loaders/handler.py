from pathlib import Path
from typing import Union


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


def file_exists(file_path: Union[Path, str]) -> bool:
    """
    Checks if a file exists.
    :param file_path: a path to a file.
    :type file_path: str
    :return: True if the file exists.
    :rtype: bool
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)
    return file_path.exists()


def create_directory(path: str) -> None:
    """
    Create a directory from a path.
    :param path: a path to a directory.
    :type path: str
    :return: None
    :rtype: None
    """
    Path(path).mkdir(parents=True, exist_ok=True)
