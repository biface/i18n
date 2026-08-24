"""
i18n-tools formatter sub-package
=================================

**License:**
This file is distributed under the terms of the `CeCILL-C Free Software License Agreement
<https://cecill.info/licences/Licence_CeCILL-C_V1-en.html>`_. By using, modifying, or
redistributing this file, you agree to comply with the terms of this license.

**Author(s):**
This module is authored and maintained as part of the i18n-tools package.

The ``formatter`` sub-package owns message *publishing*: turning a
``Message``'s plural/alternative matrix and its ``plural_rule`` into a
single, variable-substituted string (DD-27, DD-40). It mirrors the
``models`` sub-package's layout, and leaves room for future
``Book``/``Corpus``-level formatting modules without another
restructuring.

- ``publish.py`` — ``publish()``: the DD-27 four-step column fallback,
  ``PluralRule`` resolution, variable substitution.
- ``plurals.py`` — ``PluralRule``: the DD-40 CLDR-baseline-plus-
  business-threshold-overlay plural resolution rule.

This sub-package imports from ``models`` (for type hints only); models
never import from ``formatter`` (DD-05/DD-06).
"""

from .plurals import PluralRule
from .publish import publish

__all__ = [
    "publish",
    "PluralRule",
]
