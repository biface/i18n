"""
Static and global variables module
==================================

"""

import os
from pathlib import Path

I18N_TOOLS_LOCALE = "locales"
"""
This variable is used to store the name of the locale directory as the translation repository root in the project.
"""
I18N_TOOLS_MESSAGES = "LC_MESSAGES"
"""
This variable is used to store the name of the locale directory container of translation domains in the project.
"""
I18N_TOOLS_BACKUP = "backup"
"""
This variable is used to store the name of the backup directory in the project under the config directory.
"""
I18N_TOOLS_TEMPLATE = "templates"
"""
This variable is used to store the name of the template directory in the project under the config directory. This is
mainly used with i18n translation model.
"""
I18N_TOOLS_CONFIG = "_i18n_tools"
"""
This variable is used to store the name of the config directory in the project.
"""

I18N_TOOLS_ROOT = Path(__file__).resolve().parent
"""
This variable is used to store the absolute path of the root directory of the i18n-tools package.
"""
I18N_TOOLS_MODULE_NAME = os.path.basename(I18N_TOOLS_ROOT)
"""
This variable is used to store the name of the i18n-tools package.
"""
I18N_TOOLS_ROOT_NAME = os.path.dirname(I18N_TOOLS_ROOT)
"""
This variable is used to store the name of the parent directory of the i18n-tools package.
"""
I18N_TOOLS_CONFIG_DIR = str(
    Path(__file__).resolve().parent / I18N_TOOLS_LOCALE / I18N_TOOLS_CONFIG
)
"""
This variable is used to store the absolute path of the config directory in the project.
"""
I18N_TOOLS_CONFIG_FILE = "i18n_tools.yaml"
"""
This variable is used to define the name and format of the i18n_tools configuration file.
"""
