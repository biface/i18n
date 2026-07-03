"""
i18n-tools models sub-package
==============================

**License:**
This file is distributed under the terms of the `CeCILL-C Free Software License Agreement
<https://cecill.info/licences/Licence_CeCILL-C_V1-en.html>`_. By using, modifying, or
redistributing this file, you agree to comply with the terms of this license.

**Author(s):**
This module is authored and maintained as part of the i18n-tools package.

The ``models`` sub-package implements the four-level object hierarchy used
to represent translation data:

``Message`` -> ``Book`` -> ``Corpus`` -> ``Encyclopaedia``

- ``Message`` holds a single identifier's translations, stored as a
  ``messages[row][col]`` matrix (rows: plural forms, columns: alternatives).
- ``Book`` is the atomic persistence unit: one ``Book`` maps to one
  ``.i18t`` file for a given domain and language.
- ``Corpus`` aggregates every ``Book`` of a domain across all available
  languages, and exposes ``FallbackBook`` for transparent multi-language
  resolution.
- ``Encyclopaedia`` lazily aggregates every ``Corpus`` of a repository.

``Repository`` models the on-disk configuration and metadata (paths,
domains, languages, authors, translators) as a nested dictionary structure.
``Author``/``Authors`` and ``Translator``/``Translators`` manage the
``authors`` and ``translators`` sections of a ``Repository`` respectively.

Models in this sub-package hold no I/O logic of their own; persistence is
delegated to ``i18n_tools.loaders.loader``.

Notes
-----
This module makes no imports from application layers (``loaders``,
``core``, ``sync``, ``converter``) — see github decision type issues
 for the rationale.
"""

from .author import Author, Authors
from .corpus import Book, Corpus, Encyclopaedia, FallbackBook, Message
from .repository import Repository
from .translator import Translator, Translators

__all__ = [
    "Message",
    "Book",
    "Corpus",
    "FallbackBook",
    "Encyclopaedia",
    "Repository",
    "Author",
    "Authors",
    "Translator",
    "Translators",
]
