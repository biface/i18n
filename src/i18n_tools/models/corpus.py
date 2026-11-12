"""
Corpus: the Books of one domain across languages.
"""

from typing import TYPE_CHECKING

from i18n_tools._cells import resolve_cell
from i18n_tools._checks import ensure_type
from i18n_tools._compat import override
from i18n_tools._finding import Finding
from i18n_tools.locale import normalize_language_tag
from i18n_tools.models.book import Book, FallbackBook
from i18n_tools.models.message import Message, extract_tokens

if TYPE_CHECKING:
    from i18n_tools.models.repository import Repository


class Corpus:
    """
    Container of Books for a single domain across all loaded languages.

    ``Corpus`` holds one real ``Book`` per available language.  Its central
    entry point is ``get_book(lang)``, which returns a ``FallbackBook`` — a
    transparent proxy that resolves each message individually through the
    fallback chain (DD-09).

    The fallback chain for a requested language ``lang`` is built inline
    (v0.3.x, no ``fallback.py`` yet) using the IETF parent tag extracted via
    ``langcodes``.  The full ``fallback.py`` module (DD-29) will replace this
    inline resolution in v1.0.0.

    Cross-language operations
    -------------------------
    - ``coverage()``  — coverage rate per language (0.0–1.0)
    - ``missing(lang)`` — identifiers absent in ``lang`` but present elsewhere
    - ``languages``   — list of loaded languages
    - ``check()``     — structure and token names of each message across
      languages

    References
    ----------
    - biface/i18n#43 : Corpus design (DD-09, DD-09b)
    - biface/i18n#20 : MessageNotFoundError (DD-24)
    """

    def __init__(self, domain: str) -> None:
        """
        Initialise an empty Corpus for the given domain.

        :param domain: The translation domain this Corpus covers.
        :type domain: str
        :raises TypeError: If ``domain`` is not a string.

        References
        ----------
        - biface/i18n#43 : Corpus design (DD-09)
        """
        ensure_type(domain, str, f"Corpus domain must be a string, got {type(domain)}")
        self._domain: str = domain
        self._books: dict[str, "Book"] = {}  # language -> Book

    # --- Book management ---

    def add_book(self, book: "Book") -> None:
        """
        Register a real Book in this Corpus.

        :param book: A fully populated Book whose domain matches this Corpus.
        :type book: Book
        :raises TypeError: If ``book`` is not a Book instance.
        :raises ValueError: If the Book domain does not match the Corpus domain,
            or if a Book for that language is already registered.

        References
        ----------
        - biface/i18n#43 : Corpus design (DD-09)
        """
        ensure_type(book, Book, f"Expected a Book instance, got {type(book)}")
        if book.domain != self._domain:
            raise ValueError(
                f"Book domain '{book.domain}' does not match Corpus domain '{self._domain}'"
            )
        if book.language in self._books:
            raise ValueError(
                f"A Book for language '{book.language}' is already registered in this Corpus"
            )
        if book.language is None:
            raise ValueError("Book has no language set — cannot register in Corpus")
        self._books[book.language] = book

    def get_real_book(self, lang: str) -> "Book":
        """
        Return the actual registered Book for a language — no fallback
        resolution, unlike ``get_book()``, which always returns a
        ``FallbackBook`` proxy. Useful for callers that need the concrete
        Book itself (e.g. saving it back to disk), rather than the
        resolved-content view.

        :param lang: Exact language tag to look up.
        :type lang: str
        :return: The Book registered for that exact language.
        :rtype: Book
        :raises KeyError: If no Book is registered for that exact
            language — no fallback chain is consulted.
        """
        return self._books[lang]

    def get_book(
        self, lang: str, repository: "Repository | None" = None
    ) -> FallbackBook:
        """
        Return a FallbackBook for ``lang`` built from a fallback chain.

        Two resolution modes:

        - ``repository`` supplied: the chain comes from
          ``fallback.resolve(lang, repository)`` — the requested
          language, its IETF parent, variants declared under that
          parent in ``repository.hierarchy``, and the repository's
          global fallback and its own variants — filtered to the
          languages actually loaded in this Corpus.
        - ``repository`` omitted: the inline heuristic chain (unchanged
          from prior versions), for a Corpus used standalone without a
          Repository at hand:

          1. The requested language, if loaded.
          2. The IETF parent tag (e.g. ``fr`` for ``fr-CH``), if
             different and loaded.
          3. Any other loaded language whose IETF parent matches
             (siblings).
          4. All remaining loaded languages, in insertion order.

        If the resulting chain is empty, ``MessageNotFoundError`` is
        raised.

        :param lang: Requested language tag (e.g. ``"fr-CH"``).
        :type lang: str
        :param repository: Optional Repository to resolve the chain
            against ``fallback.resolve()`` instead of the inline
            heuristic.
        :type repository: Repository | None
        :return: A FallbackBook wrapping the resolved chain.
        :rtype: FallbackBook
        :raises MessageNotFoundError: If no loaded Book matches the chain.
        """
        from i18n_tools.exceptions import MessageNotFoundError

        normalized = normalize_language_tag(lang)
        chain: list["Book"] = []
        seen: set[str] = set()

        def _add(language: str) -> None:
            if language not in seen and language in self._books:
                chain.append(self._books[language])
                seen.add(language)

        if repository is not None:
            from i18n_tools.fallback import resolve

            for tag in resolve(normalized, repository):
                _add(tag)
        else:
            # 1. Requested language
            _add(normalized)

            # 2. IETF parent (e.g. "fr" for "fr-CH" or "fr-FR")
            parent = normalized.rsplit("-", 1)[0] if "-" in normalized else None
            if parent:
                _add(parent)

            # 3. Siblings — other loaded languages sharing the same parent
            for loaded_lang in self._books:
                loaded_parent = (
                    loaded_lang.rsplit("-", 1)[0] if "-" in loaded_lang else loaded_lang
                )
                if loaded_parent == parent or loaded_lang == parent:
                    _add(loaded_lang)

            # 4. All remaining loaded languages
            for loaded_lang in self._books:
                _add(loaded_lang)

        if not chain:
            raise MessageNotFoundError(
                f"No Book available in Corpus '{self._domain}' for language '{lang}'"
            )

        return FallbackBook(chain, normalized)

    # --- Cross-language operations ---

    @property
    def domain(self) -> str:
        """The domain this Corpus covers."""
        return self._domain

    @property
    def languages(self) -> list[str]:
        """List of loaded language tags, in insertion order."""
        return list(self._books.keys())

    def coverage(self) -> dict[str, float]:
        """
        Compute the coverage rate of each loaded language.

        The reference set is the union of all message identifiers across all
        loaded Books.  Coverage for a language is the fraction of reference
        identifiers present in its Book.

        :return: Mapping of language tag to coverage rate (0.0–1.0).
            Returns an empty dict if no Books are loaded.
        :rtype: dict[str, float]

        References
        ----------
        - biface/i18n#43 : Corpus cross-language operations (DD-09)
        """
        if not self._books:
            return {}
        all_ids: set[str] = set()
        for book in self._books.values():
            all_ids.update(book.messages.keys())
        total = len(all_ids)
        if total == 0:
            return {lang: 1.0 for lang in self._books}
        return {
            lang: len(set(book.messages.keys()) & all_ids) / total
            for lang, book in self._books.items()
        }

    def missing(self, lang: str) -> list[str]:
        """
        Return identifiers present in other Books but absent in ``lang``.

        :param lang: Language tag to check.
        :type lang: str
        :return: Sorted list of missing message identifiers.
        :rtype: list[str]
        :raises ValueError: If ``lang`` is not loaded in this Corpus.

        References
        ----------
        - biface/i18n#43 : Corpus cross-language operations (DD-09)
        """
        normalized = normalize_language_tag(lang)
        if normalized not in self._books:
            raise ValueError(
                f"Language '{normalized}' is not loaded in Corpus '{self._domain}'"
            )
        all_ids: set[str] = set()
        for book in self._books.values():
            all_ids.update(book.messages.keys())
        present = set(self._books[normalized].messages.keys())
        return sorted(all_ids - present)

    def check(self) -> list[Finding]:
        """
        Check that each message has the same structure and the same token
        names in every language.

        The fallback chain resolves a whole message: a language holding
        the identifier answers with its own message, a language without
        it answers with the message of another language. Comparing the
        messages resolved for every language therefore amounts to
        comparing the messages of the same identifier held by the books.
        Only ``"complete"`` messages are compared: a ``"draft"`` takes
        part in the fallback chain but carries no integrity obligation.

        Two complete messages of the same identifier must have the same
        number of declensions and of segments. When they do, each cell
        ``(variant, segment)`` must carry the same set of token names in
        both. The text of a cell is read after the column fallback, so
        an absent text is compared through the text that replaces it at
        publication. Token order and repetitions are not compared.

        Each mismatch is reported with severity ``"error"`` and the
        identifier of the message. Nothing is raised and the books are
        not modified.

        :return: The findings, by identifier; empty if nothing is wrong.
        :rtype: list[Finding]
        """
        findings: list[Finding] = []
        identifiers: set[str] = set()
        for book in self._books.values():
            identifiers.update(str(key) for key in book.messages.keys())
        for msg_id in sorted(identifiers):
            complete: list[tuple[str, Message]] = []
            for language, book in self._books.items():
                message = book.get(msg_id)
                if message is not None and message.status == "complete":
                    complete.append((language, message))
            if len(complete) < 2:
                continue
            findings.extend(_compare_messages(msg_id, complete))
        return findings

    @override
    def __repr__(self) -> str:
        return f"Corpus(domain='{self._domain}', languages={self.languages})"


def _compare_messages(
    msg_id: str, messages: list[tuple[str, Message]]
) -> list[Finding]:
    """
    Compare the structure, then the token names, of the complete messages
    of one identifier.

    :param msg_id: Identifier shared by the messages.
    :type msg_id: str
    :param messages: ``(language, message)`` pairs, at least two.
    :type messages: list[tuple[str, Message]]
    :return: One finding for a structure mismatch, or one finding per
        cell whose token names differ.
    :rtype: list[Finding]
    """
    shapes = {
        language: (message.observed.declensions, message.observed.segments)
        for language, message in messages
    }
    if len(set(shapes.values())) > 1:
        described = ", ".join(
            f"{language} {declensions}x{segments}"
            for language, (declensions, segments) in shapes.items()
        )
        return [
            Finding(
                "error",
                msg_id,
                "structure differs across languages (declensions x segments): "
                + described,
            )
        ]
    declensions, segments = next(iter(shapes.values()))
    matrices = [(language, message.matrix) for language, message in messages]
    findings: list[Finding] = []
    for segment in range(segments):
        for variant in range(declensions):
            tokens = {
                language: frozenset(
                    extract_tokens(resolve_cell(matrix, segment, variant))
                )
                for language, matrix in matrices
            }
            if len(set(tokens.values())) == 1:
                continue
            described = ", ".join(
                f"{language} {sorted(names)}" for language, names in tokens.items()
            )
            findings.append(
                Finding(
                    "error",
                    msg_id,
                    f"tokens of cell (variant {variant}, segment {segment}) "
                    + f"differ across languages: {described}",
                )
            )
    return findings
