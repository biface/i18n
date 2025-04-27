"""
i18n-tools main package
=======================

**License:**
This file is distributed under the terms of the `CeCILL-C Free Software License Agreement
<https://cecill.info/licences/Licence_CeCILL-C_V1-en.html>`_. By using, modifying, or
redistributing this file, you agree to comply with the terms of this license.

**Author(s):**
This module is authored and maintained as part of the i18n-tools package.
"""

from i18n_tools.__static__ import (
    I18N_TOOLS_CONFIG,
    I18N_TOOLS_LOCALE,
    I18N_TOOLS_MODULE_NAME,
    I18N_TOOLS_ROOT_NAME,
)
from i18n_tools.loaders import (
    build_path,
    create_directory,
    file_exists,
)

__ALL__ = [
    I18N_TOOLS_MODULE_NAME,
    I18N_TOOLS_ROOT_NAME,
    build_path,
    file_exists,
    create_directory,
]

__version__ = "0.1.0"
