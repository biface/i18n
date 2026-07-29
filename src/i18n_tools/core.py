"""
Core Module
============

This module is the high-level orchestrator for i18n-tools: the single
entry point that ties together ``Repository`` (paths, module/domain/
language configuration), the loaders/sync layers (file I/O and
per-format synchronization policy), and the content model
(``Message``/``Book``/``Corpus``/``Encyclopaedia``).

It is the only module outside ``loaders/`` allowed to import
``loaders.*`` directly — models never do (DD-06), and callers of this
package are not meant to reach into ``loaders.*`` themselves (DD-22).

Coexistence principle: the object model (``Message``/``Book``/
``Corpus``/``Encyclopaedia``) does not deprecate the procedural,
dict-based access already provided by ``loader.py``/``sync.py``. Both
surfaces are kept deliberately available side by side — this module
adds an object-oriented view on top, it does not replace the
functional one. Code in ``loader.py``/``sync.py`` that looks redundant
once the object model is in place must not be removed on that basis
alone; retiring it is a separate, explicit decision.

Key Responsibilities:
    - Resolve the on-disk directory for a given (module, domain, language)
      triple, following the repository's directory layout.
    - Load and save individual Books by delegating to the existing,
      already-functional ``Book.load()``/``Book.save()`` methods — this
      module does not duplicate their I/O, it only supplies the path
      they need.
    - Load and save a full Corpus (every configured language for one
      module/domain), by repeating the Book-level operation across
      ``repository.source`` and every language declared in
      ``repository.hierarchy``.
    - Translate a ``Repository`` into the raw parameters
      ``sync.check_repository()`` already expects, so callers only ever
      deal with ``Repository`` objects at this layer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .loaders.handler import build_path
from .locale import get_all_languages, normalize_language_tag
from .models.corpus import Book, Corpus
from .sync import check_repository

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


def _corpus_languages(repository: "StrictNestedDictionary") -> set[str]:
    """
    Compute the full set of languages a Corpus for this repository should
    hold — ``repository.source`` plus every language declared in
    ``repository.hierarchy`` (both the parent/fallback keys themselves,
    e.g. ``"fr"``, and their variants, e.g. ``"fr-FR"``, ``"fr-BE"``).

    This must always match the set ``sync.check_repository()`` creates
    files for (see ``core.synchronize()`` below) — both go through
    ``locale.get_all_languages()`` for exactly this reason.

    :param repository: Repository declaring ``source``/``hierarchy``.
    :type repository: StrictNestedDictionary
    :return: Set of language tags.
    :rtype: set[str]
    """
    languages = get_all_languages(repository.hierarchy)
    if repository.source:
        languages.add(repository.source)
    return languages


def load_corpus(
    repository: "StrictNestedDictionary", module: str, domain: str
) -> Corpus:
    """
    Load a full Corpus — every configured language — for a module/domain.

    Builds an empty ``Corpus`` for ``domain``, then calls ``load_book()``
    for each language in ``repository.source`` plus every language
    declared in ``repository.hierarchy``, registering each result via
    ``Corpus.add_book()``.

    Languages are read from the repository's declared configuration, not
    from a filesystem scan — a language must have been synchronized
    first (see ``synchronize()``) for its file to exist.

    Note: this does not consult ``fallback.resolve()`` — each language is
    loaded independently. Wiring language-fallback resolution into
    Corpus-level loading is a separate, later decision.

    :param repository: Repository providing paths and declared languages.
    :type repository: StrictNestedDictionary
    :param module: Module identifier (e.g. ``"src/app"``).
    :type module: str
    :param domain: Translation domain name.
    :type domain: str
    :return: A Corpus with one Book per configured language.
    :rtype: Corpus
    :raises IOError: If a module/language directory does not exist.
    :raises FileNotFoundError: If a domain's ``.i18t`` file does not
        exist in one of those directories.
    :raises ValueError: If a file fails the integrity check.
    """
    corpus = Corpus(domain=domain)
    for lang in _corpus_languages(repository):
        book = load_book(repository, module, domain, lang)
        corpus.add_book(book)
    return corpus


def save_corpus(
    corpus: Corpus, repository: "StrictNestedDictionary", module: str
) -> None:
    """
    Save every Book currently registered in a Corpus back to disk.

    Iterates ``corpus.languages`` and calls ``save_book()`` for each
    registered Book (via ``Corpus.get_real_book()`` — the concrete Book,
    not a ``FallbackBook`` proxy). ``module`` is required explicitly for
    the same reason as in ``save_book()``: neither ``Book`` nor
    ``Corpus`` carry a module — only ``Encyclopaedia`` and this
    orchestration layer do.

    :param corpus: The Corpus whose Books should be persisted.
    :type corpus: Corpus
    :param repository: Repository providing the ``paths.repository`` root.
    :type repository: StrictNestedDictionary
    :param module: Module identifier under which to save these Books.
    :type module: str
    :raises IOError: If a module/language directory does not exist —
        typically because the repository has not been synchronized yet.
    """
    for lang in corpus.languages:
        book = corpus.get_real_book(lang)
        save_book(book, repository, module)


def synchronize(repository: "StrictNestedDictionary") -> None:
    """
    Ensure the repository's on-disk directory structure exists.

    Translates ``repository`` into the raw ``tld``/``domains``/
    ``languages`` parameters ``sync.check_repository()`` already expects,
    so callers of ``core.py`` only ever need to work with ``Repository``
    objects. Delegates entirely to ``check_repository()`` — this
    function adds no logic of its own beyond that translation.

    Only covers the native ``.i18t`` format, per ``sync.py``'s own scope
    (its per-format synchronization policy also covers ``.po``, and will
    cover i18next in future — this function's ``.i18t``-only scope will
    grow alongside ``sync.py``, not by duplicating logic here).

    :param repository: Repository declaring paths, domains, and
        languages.
    :type repository: StrictNestedDictionary
    """
    check_repository(
        repository[["paths", "repository"]],
        dict(repository.domains),
        {
            "source": repository.source,
            "hierarchy": dict(repository.hierarchy),
        },
    )
