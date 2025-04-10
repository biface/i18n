from __future__ import annotations

import tarfile
from pathlib import Path

from .handler import build_path, create_directory
from .utils import _exist_path, _non_traversal_path


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


def build_config_repository(app_root: str) -> None:
    """

    :param app_root:
    :return:
    """
    # TODO : Move to repository.py
    config_path = build_path(app_root, "locales", "_18n_tools")
    if not _exist_path(config_path):
        create_directory(config_path)
