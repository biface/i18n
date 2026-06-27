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
    __version__,
)

__all__ = [
    # Models
    "Message",
    "Book",
    "Corpus",
    "FallbackBook",
    "Encyclopaedia",
    # Configuration
    "Repository",
    "Config",
    # Constants
    "I18N_TOOLS_CONFIG",
    "I18N_TOOLS_LOCALE",
    "I18N_TOOLS_MODULE_NAME",
    "I18N_TOOLS_ROOT_NAME",
    "I18N_TOOLS_TRANSLATION_FILE_EXT",
    # Version
    "__version__",
]

from i18n_tools.config import Config  # noqa: E402

# Models, Repository, and Config can now be imported in any order: __version__
# and the other shared constants live in __static__.py, which internal modules
# (corpus.py, loaders/handler.py, loaders/repository.py) import directly,
# without going through this file. The former import-order constraint
# (biface/i18n#47, DD-19) no longer applies.
from i18n_tools.models import (  # noqa: E402
    Book,
    Corpus,
    Encyclopaedia,
    FallbackBook,
    Message,
)
from i18n_tools.models.repository import Repository  # noqa: E402
