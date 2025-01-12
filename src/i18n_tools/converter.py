"""
converter.py
============

This module provides functions to manipulate and convert internationalization
(i18n) data between different formats. It includes utilities for generating
headers for `.pot` files, converting data between `i18n` and `i18next` formats,
and creating deterministic message IDs.

**Key Features:**

    - Convert PO files to i18next JSON format and vice versa.
    - Generate deterministic message IDs using weights and base values.
    - Create metadata headers for `.pot` files, including author and team
      information.

**License:**
This file is distributed under the `CeCILL-C Free Software License Agreement
<https://cecill.info/licences/Licence_CeCILL-C_V1-en.html>`_. By using or
modifying this file, you agree to abide by the terms of this license.

**Author(s):**
This module is authored and maintained as part of the i18n-tools package.

"""
