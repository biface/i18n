"""
loaders
=======

The `loaders` module provides essential file handling operations for the
i18n-tools package. It is designed to manage the loading, saving, and
manipulation of various file formats used in internationalization (i18n)
projects.

**Key Features:**
    - Load and save configuration files in JSON, YAML, and TOML formats.
    - Handle `.po`, `.pot`, and `.mo` files for translation projects, including
      reading and writing operations.
    - Create and manage compressed archives (tar.gz and gzip) for module
      directories.
    - Ensure safe file extraction paths to prevent directory traversal attacks.
    - Provide utility functions for common file operations such as creating
      directories and checking file existence.

**License:**
This file is distributed under the `CeCILL-C Free Software License Agreement
<https://cecill.info/licences/Licence_CeCILL-C_V1-en.html>`_. By using or
modifying this file, you agree to abide by the terms of this license.

**Author(s):**
This module is authored and maintained as part of the i18n-tools package.
"""

from __future__ import annotations

from .configuration import load_config, save_config
from .handler import build_path, create_directory, file_exists
from .repository import (
    create_module_archive,
    restore_module_from_archive,
)

__all__ = [build_path, file_exists, create_directory, load_config, save_config]
