"""
Static and global variables module
==================================

"""
from typing_extensions import Unpack

import os
from pathlib import Path
from typing import Literal


I18N_TRANSLATION_FORMAT = {"json", "yaml"}
"""
This format defines the set of standard storage files for translations
"""
TranslationFileFormat = Literal["json", "yaml"]
"""
This format defines a generic type for standard storage files for translations
"""
I18N_TOOLS_EXT_SET = ("i18t", "itl")
"""
This variable stores dedicated translation file extensions for i18n-tools
"""
I18N_TOOLS_TRANSLATION_FILE_EXT = "i18n"
"""
This variable is used to store the default 4 letters translation file extension. Since the file format could be
either JSON or YAML, translation file will be _domain.[json|yaml].i18n_
"""
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
