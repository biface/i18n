"""
Core Module
============

This module is the high-level orchestrator for i18n-tools: the single
entry point that ties together ``Repository`` (paths, module/domain/
language configuration), the loaders layer (file I/O), and the content
model (``Message``/``Book``/``Corpus``/``Encyclopaedia``).

It is the only module outside ``loaders/`` allowed to import
``loaders.*`` directly — models never do (DD-06), and callers of this
package are not meant to reach into ``loaders.*`` themselves (DD-22).

Key Responsibilities:
    - Resolve the on-disk directory for a given (module, domain, language)
      triple, following the repository's directory layout.
    - Load and save individual Books by delegating to the existing,
      already-functional ``Book.load()``/``Book.save()`` methods — this
      module does not duplicate their I/O, it only supplies the path
      they need.

Note: this module currently covers Book-level load/save only.
Corpus-level (all languages for a domain) and repository-wide
synchronization are a separate, later increment — not yet implemented
here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .loaders.handler import build_path
from .locale import normalize_language_tag
from .models.corpus import Book

if TYPE_CHECKING:
    from ndict_tools import StrictNestedDictionary


def _book_directory(
    repository: "StrictNestedDictionary", module: str, lang: str
) -> str:
    """
    Resolve the on-disk directory holding a Book's translation file.

    Reuses the same building blocks (``build_path`` and the
    ``I18N_TOOLS_LOCALE``/``I18N_TOOLS_MESSAGES`` constants) already used
    internally by ``loaders.handler.build_translation_lang_files`` for the
    gettext-oriented (po/pot) paths — this helper only needs the
    directory itself, since ``Book.load()``/``Book.save()`` append their
    own filename.

    :param repository: Repository whose ``paths.repository`` root anchors
        the layout.
    :type repository: StrictNestedDictionary
    :param module: Module identifier (e.g. ``"src/app"``).
    :type module: str
    :param lang: Language tag for the Book (e.g. ``"fr-CH"``).
    :type lang: str
    :return: Absolute directory path, e.g.
        ``"<root>/src/app/locales/fr-CH/LC_MESSAGES"``.
    :rtype: str
    :raises IOError: If the resulting directory does not exist —
        typically because the repository has not been synchronized yet.
    """
    from .__static__ import I18N_TOOLS_LOCALE, I18N_TOOLS_MESSAGES

    repository_path = repository[["paths", "repository"]]
    normalized_lang = normalize_language_tag(lang)
    return build_path(
        repository_path, module, I18N_TOOLS_LOCALE, normalized_lang, I18N_TOOLS_MESSAGES
    )


def load_book(
    repository: "StrictNestedDictionary", module: str, domain: str, lang: str
) -> Book:
    """
    Load a Book for a given module/domain/language from the repository.

    Builds an empty ``Book`` for ``domain``/``lang``, resolves its
    directory from ``repository``/``module``, and delegates the actual
    file read to ``Book.load()``.

    :param repository: Repository providing the ``paths.repository`` root.
    :type repository: StrictNestedDictionary
    :param module: Module identifier (e.g. ``"src/app"``).
    :type module: str
    :param domain: Translation domain name.
    :type domain: str
    :param lang: Language tag to load (e.g. ``"fr-CH"``).
    :type lang: str
    :return: The populated Book.
    :rtype: Book
    :raises IOError: If the module/language directory does not exist.
    :raises FileNotFoundError: If the domain's ``.i18t`` file does not
        exist in that directory.
    :raises ValueError: If the file fails the integrity check.
    """
    book = Book(language=lang, domain=domain)
    path_directory = _book_directory(repository, module, lang)
    book.load(path_directory)
    return book


def save_book(book: Book, repository: "StrictNestedDictionary", module: str) -> None:
    """
    Save a Book back to its module's location in the repository.

    Resolves the target directory from ``repository``/``module`` and
    ``book.language``, and delegates the actual file write to
    ``Book.save()``. ``module`` is required explicitly rather than read
    off ``book`` — ``Book`` only knows its own ``language``/``domain``,
    never its module; module is only ever meaningful at this
    orchestration layer and at ``Encyclopaedia``, which is keyed by
    ``(module, domain)``.

    :param book: The Book to persist.
    :type book: Book
    :param repository: Repository providing the ``paths.repository`` root.
    :type repository: StrictNestedDictionary
    :param module: Module identifier under which to save this Book.
    :type module: str
    :raises IOError: If the module/language directory does not exist —
        typically because the repository has not been synchronized yet.
    """
    path_directory = _book_directory(repository, module, book.language)
    book.save(path_directory)
