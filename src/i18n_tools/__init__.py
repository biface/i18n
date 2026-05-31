"""
i18n-tools main package
=======================

**License:**
This file is distributed under the terms of the `CeCILL-C Free Software License Agreement
<https://cecill.info/licences/Licence_CeCILL-C_V1-en.html>`_. By using, modifying, or
redistributing this file, you agree to comply with the terms of this license.

**Author(s):**
This module is authored and maintained as part of the i18n-tools package.

References
----------
- biface/i18n#48 : public API __init__.py (DD-21, DD-22, DD-23)
"""

from i18n_tools.__static__ import (
    I18N_TOOLS_CONFIG,
    I18N_TOOLS_LOCALE,
    I18N_TOOLS_MODULE_NAME,
    I18N_TOOLS_ROOT_NAME,
    I18N_TOOLS_TRANSLATION_FILE_EXT,
)

__version__ = "0.3.0"

__all__ = [
    # Models — exposed after __version__ is defined to avoid circular import
    # (corpus.py imports __version__ from this module)
    "Message",
    "Book",
    "Corpus",
    "FallbackBook",
    "Encyclopaedia",
    # Configuration
    "Repository",
    # Constants
    "I18N_TOOLS_CONFIG",
    "I18N_TOOLS_LOCALE",
    "I18N_TOOLS_MODULE_NAME",
    "I18N_TOOLS_ROOT_NAME",
    "I18N_TOOLS_TRANSLATION_FILE_EXT",
    # Version
    "__version__",
]

# Models imported after __version__ is defined to avoid circular import:
# corpus.py → from i18n_tools import __version__
# Refactoring deferred to v0.4.x (DD-19, biface/i18n#47)
from i18n_tools.models import (  # noqa: E402
    Book,
    Corpus,
    Encyclopaedia,
    FallbackBook,
    Message,
)
from i18n_tools.models.repository import Repository  # noqa: E402
