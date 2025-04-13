from __future__ import annotations

import tarfile

from ndict_tools import NestedDictionary

from i18n_tools.__static__ import (
    I18N_TOOLS_BACKUP,
    I18N_TOOLS_CONFIG,
    I18N_TOOLS_LOCALE,
)

from .handler import build_path, create_directory
from .utils import _exist_path, _non_traversal_path


def create_module_archive(
    repository: NestedDictionary, module: str, archive_name: str
) -> None:
    """
    Create a tar.gz archive of a module's contents, including all subdirectories and files,
    by identifying the top-level module from the given module/package path.

    :param repository: The data representing the repository..
    :type repository: NestedDictionary
    :param module: The module or module/package path (e.g., "mod-1/pkg-1").
    :type module: str
    :param archive_name: The name of the archive file.
    :type archive_name: str
    :return: None
    :rtype: None
    """
    # TODO: Implement repository data.

    # Identify the top-level module from the given module path
    # This is done by splitting the module path and taking the first part
    # For example, if module is "mod-1/pkg-1", top_level_module will be "mod-1"
    top_level_module = module.split("/")[0]

    # Build the path to backup directory as <
    archive_path = build_path(repository[["paths", "repository"]], top_level_module)

    # Construct the full path to the top-level module
    # This is the directory that will be archived
    backup_path = build_path(
        repository[["paths", "repository"]],
        top_level_module,
        I18N_TOOLS_LOCALE,
        I18N_TOOLS_CONFIG,
        I18N_TOOLS_BACKUP,
    )

    # Construct the path for the archive file
    # The archive will be created in the root_path directory with the given archive_name
    archive = backup_path + f"/{archive_name}.tar.gz"

    # Open the archive file in write mode with gzip compression
    with tarfile.open(archive, "w:gz") as tar:
        # Add the top-level module to the archive
        # The arcname parameter ensures that the directory structure is preserved in the archive
        # This means the archive will contain the top-level module directory and all its contents
        tar.add(archive_path, arcname=top_level_module)


def restore_module_from_archive(
    repository: NestedDictionary, module: str, archive_name: str
) -> None:
    """
    Restore a module's contents from a tar.gz archive.

    :param repository: The data representing the repository.
    :type repository: NestedDictionary
    :param module: The module or sub-module path (e.g., "mod-1/pkg-1").
    :type module: str
    :param archive_name: The name of the archive file.
    :type archive_name: str
    """

    # Split the module path to get the top-level module
    module_parts = module.split("/")
    top_level_module = module_parts[0]

    # Construct the path for the archive file
    archive_path = (
        build_path(
            repository[["paths", "repository"]],
            top_level_module,
            I18N_TOOLS_LOCALE,
            I18N_TOOLS_CONFIG,
            I18N_TOOLS_BACKUP,
        )
        + f"/{archive_name}.tar.gz"
    )

    # Check if the archive file exists
    if _exist_path(archive_path):
        # Open the archive file in read mode with gzip compression
        with tarfile.open(archive_path, "r:gz") as tar:
            # Extract all members that are safe to extract
            tar.extractall(
                path=repository[["paths", "repository"]],
                members=_non_traversal_path(
                    repository[["paths", "repository"]],
                    [top_level_module],
                    tar.getmembers(),
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
    # TODO : implement repository data

    config_path = build_path(app_root, "locales", "_18n_tools")
    if not _exist_path(config_path):
        create_directory(config_path)
