import os
from pathlib import Path

from i18n_tools.loaders import (
    build_path,
    create_directory,
    file_exists,
)

I18N_TOOLS_ROOT = Path(__file__).resolve().parent
I18N_TOOLS_MODULE_NAME = os.path.basename(I18N_TOOLS_ROOT)
I18N_TOOLS_ROOT_NAME = os.path.dirname(I18N_TOOLS_ROOT)
I18N_TOOLS_CONFIG_DIR = str(Path(__file__).resolve().parent / "locales/_i18n_tools/")
I18N_TOOLS_CONFIG_FILE = "i18n_tools.yaml"

__ALL__ = [
    I18N_TOOLS_MODULE_NAME,
    I18N_TOOLS_ROOT_NAME,
    build_path,
    file_exists,
    create_directory,
]
