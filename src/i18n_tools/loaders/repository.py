from pathlib import Path

from .utils import _load_config_file, _save_config_file


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
