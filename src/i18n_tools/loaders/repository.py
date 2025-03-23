import tarfile
from pathlib import Path

from .utils import _load_config_file, _non_traversal_path, _save_config_file


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

    _save_config_file(file_path, data)


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
