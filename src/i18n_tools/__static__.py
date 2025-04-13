import os
from pathlib import Path

I18N_TOOLS_LOCALE = "locales"
I18N_TOOLS_MESSAGES = "LC_MESSAGES"
I18N_TOOLS_BACKUP = "backup"
I18N_TOOLS_TEMPLATE = "templates"
I18N_TOOLS_CONFIG = "_i18n_tools"

I18N_TOOLS_ROOT = Path(__file__).resolve().parent
I18N_TOOLS_MODULE_NAME = os.path.basename(I18N_TOOLS_ROOT)
I18N_TOOLS_ROOT_NAME = os.path.dirname(I18N_TOOLS_ROOT)
I18N_TOOLS_CONFIG_DIR = str(
    Path(__file__).resolve().parent / I18N_TOOLS_LOCALE / I18N_TOOLS_CONFIG
)
I18N_TOOLS_CONFIG_FILE = "i18n_tools.yaml"
