"""
Book and FallbackBook: the messages of one domain in one language.
"""

from typing import TYPE_CHECKING, Any

from ndict_tools import StrictNestedDictionary

from i18n_tools.__static__ import (
    I18N_TOOLS_TRANSLATION_FILE_EXT,
    TranslationFileFormat,
)
from i18n_tools._checks import is_type
from i18n_tools._compat import override
from i18n_tools._counters import describe_differences
from i18n_tools._finding import Finding
from i18n_tools.converter import (
    i18n_tools_format_to_message_dict,
)
from i18n_tools.loaders.loader import build_book_filename
from i18n_tools.loaders.loader import load_book as _load_book
from i18n_tools.locale import normalize_language_tag
from i18n_tools.models.message import Message

if TYPE_CHECKING:
    from i18n_tools.formatter.plurals import PluralRule

# Root metadata keys of a .i18t file that are Book attributes, not metadata.
_ROOT_ATTRIBUTE_KEYS = frozenset({"language", "domain"})
# Root metadata keys derived from the messages, recomputed on load.
_ROOT_DERIVED_KEYS = frozenset({"statistics", "count"})


class Book:
    """
    Manage a book (collection) of internationalization Message objects for a single
    domain and a single language, using the i18n_tools format.

    Iteration

    - The class is iterable: iterating over a Book yields its Message instances
      in the natural dictionary order of self.messages (insertion order).

    Invariants

    - All messages in a Book share the same normalized language (BCP 47-like tag)
      and the same domain.

    Core attributes (moved out of metadata)

    - language (str): Normalized language tag of this book (e.g. "fr-FR").
    - domain (str): Functional or logical domain grouping the messages.
    - format (str): Serialization/storage format hint (e.g. "json").
    - messages (StrictNestedDictionary): Mapping of message.id -> Message.
    - metadata (StrictNestedDictionary): Additional data such as
      project_id_version, report_msgid_bugs_to, pot_creation_date, language_team,
      header_comment, statistics, and backward compatible counters.

    Notes

    - The keys "language", "domain" and "format" are NOT present in metadata
      anymore; they are stored as instance attributes.
    - Statistics are available under metadata["statistics"], with
      "total_messages" and "total_words".
    """

    filename: str
    plural_rule: "PluralRule | None"
    language: str | None
    domain: str | None
    messages: StrictNestedDictionary
    format: str | None
    metadata: StrictNestedDictionary

    def __init__(
        self, *args: Message | tuple[Message] | list[Message], **kwargs: Any
    ) -> None:
        """
        Initialize a Book.

        Positional arguments
        - args: Zero or more Message instances or iterables of Message.
          Any provided messages must have a metadata["language"] matching the
          book language; otherwise a ValueError is raised.

        Keyword arguments
        - language (str, required): Language for the book. The value is normalized
          using normalize_language_tag (e.g., "fr" -> "fr-FR"). If not provided,
          KeyError("No language specified") is raised.
        - domain (str, required): Domain for the book. If not provided,
          KeyError("No domain specified") is raised.
        - format (str, optional): Serialization/storage format hint. Default: "json".
        - project_id_version (str, optional): Default "i18n-tools 1.0".
        - report_msgid_bugs_to (str, optional): Default "bugs@example.com".
        - pot_creation_date (str, optional): Default empty string.
        - language_team (str, optional): Default empty string.
        - header_comment (str, optional): Default empty string.

        Behavior
        - Stores language, domain, and format as instance attributes (not in metadata).
        - Builds metadata as a StrictNestedDictionary with the keys above (except
          language/domain/format) and an initial statistics section:
          metadata["statistics"] = {"total_words": 0, "total_messages": 0}.
        - Loads any provided Message instances into the book if their
          metadata["language"] equals the normalized book language; otherwise
          raises ValueError.
        - Maintains backward compatibility counter metadata[["count", "messages"]]
          with the number of messages in the book.
        - Computes initial statistics (total_words, total_messages) from message
          contents.

        Raises
        - KeyError: if language or domain keyword is missing.
        - ValueError: if any provided Message has a language different than the
          book language.
        """
        # Required metadata -> set instance attributes directly
        self.filename = ""
        self.plural_rule = None
        language = kwargs.pop("language", None)
        if language is None:
            raise KeyError("No language specified")
        self.language = normalize_language_tag(language)

        domain = kwargs.pop("domain", None)
        if domain is None:
            raise KeyError("No domain specified")
        elif not isinstance(domain, str):
            raise TypeError("Book domain must be a string.")
        self.domain = domain

        # Initialize collections
        self.messages = StrictNestedDictionary()

        # Core metadata for naming and storage format
        self.format, self.filename = build_book_filename(
            self.domain, kwargs.pop("format", None)
        )

        # Build metadata dictionary (without language, domain, format)
        self.metadata = StrictNestedDictionary(
            project_id_version=kwargs.pop("project_id_version", "i18n-tools 1.0"),
            report_msgid_bugs_to=kwargs.pop("report_msgid_bugs_to", "bugs@example.com"),
            pot_creation_date=kwargs.pop("pot_creation_date", ""),
            language_team=kwargs.pop("language_team", ""),
            header_comment=kwargs.pop("header_comment", ""),
            statistics={"total_words": 0, "total_messages": 0},
        )

        # Load initial messages (if any)
        if len(args) > 0:
            for entity in args:
                if isinstance(entity, Message):
                    if entity.metadata["language"] == self.language:
                        self.messages[entity.id] = entity
                    else:
                        raise ValueError(
                            f"Language of message {entity.id} is not compatible with this book language"
                        )
                elif is_type(entity, (tuple, list)):
                    for message in entity:
                        if message.metadata["language"] == self.language:
                            self.messages[message.id] = message
                        else:
                            raise ValueError(
                                f"Language of message {message.id} is not compatible with this book language"
                            )
        # Keep a simple count for backward compatibility
        self.metadata[["count", "messages"]] = len(self.messages)
        # Compute statistics based on current messages
        self._compute_statistics()

    # --- Attribute management for language, domain, and format ---
    def __set_filename(self) -> None:
        """
        This private function is used to set or update filename, if one of these component changes.
        :return: nothing
        """
        if self.domain is not None and self.format is not None:
            self.filename = (
                self.domain + "." + self.format + "." + I18N_TOOLS_TRANSLATION_FILE_EXT
            )

    def get_language(self) -> str | None:
        """Return the normalized language tag of this book."""
        return self.language

    def add_language(self, lang: str) -> None:
        """Set the language if not already set; value is normalized."""
        if getattr(self, "language", None) is not None:
            raise ValueError("Language is already set for this book")
        self.language = normalize_language_tag(lang)

    def update_language(self, lang: str) -> None:
        """Update the book language after verifying every Message matches it."""
        # Ensure all messages in the book match the new language
        new_lang = normalize_language_tag(lang)
        for mid, msg in self.messages.items():
            if msg.metadata.get("language") != new_lang:
                raise ValueError(
                    f"Language of message ({mid} : '{msg.metadata.get('language')}') is not compatible with updated book language ('{new_lang}')"
                )
        self.language = new_lang

    def remove_language(self) -> None:
        """Unset the book language (may leave the book in an inconsistent state)."""
        self.language = None

    def get_domain(self) -> str | None:
        """Return the domain of this book."""
        return self.domain

    def add_domain(self, domain: str) -> None:
        """Set the domain if not already set."""
        if getattr(self, "domain", None) is not None:
            raise ValueError("Domain is already set for this book")
        self.domain = domain
        self.__set_filename()

    def update_domain(self, domain: str) -> None:
        """Update the book domain."""
        self.domain = domain
        self.__set_filename()

    def remove_domain(self) -> None:
        """Unset the book domain (may leave the book unusable until reset)."""
        self.domain = None

    def get_format(self) -> str | None:
        """Return the serialization/storage format hint."""
        return self.format

    def add_format(self, fmt: TranslationFileFormat) -> None:
        """Set the format if not already set."""
        if getattr(self, "format", None) is not None:
            raise ValueError("Format is already set for this book")
        if self.domain is None:
            raise ValueError("Domain must be set before setting the format")
        self.format, self.filename = build_book_filename(self.domain, fmt)

    def update_format(self, fmt: TranslationFileFormat) -> None:
        """Update the format hint."""
        if self.domain is None:
            raise ValueError("Domain must be set before updating the format")
        self.format, self.filename = build_book_filename(self.domain, fmt)

    def remove_format(self) -> None:
        """Unset the format hint."""
        self.format = None
        self.filename = ""

    def _compute_statistics(self) -> None:
        """
        Compute statistics from the messages contained in the book and store them in metadata.statistics.
        - total_messages: number of messages in the book
        - total_words: whitespace-separated words over every cell of every message matrix
        """

        total_words = sum(
            len(cell.split())
            for message in self.messages.values()
            for row in message.matrix
            for cell in row
        )

        self.metadata[["statistics", "total_messages"]] = len(self.messages)
        self.metadata[["statistics", "total_words"]] = total_words

    def set_metadata(self, key: str | list[str] | None, value: Any = None) -> None:
        """
        Add, update or delete a metadata entry.
        - If value is None, the metadata is reset/removed to its default for the given key.
        - If key is a string, it refers to a top-level key in self.metadata.
        - If key is a list, it refers to a nested path.
        """
        if key is None:
            raise KeyError("A metadata key or path must be provided")

        # Define defaults for keys we manage so we can restore them on delete
        default_meta = StrictNestedDictionary(
            project_id_version="i18n-tools 1.0",
            report_msgid_bugs_to="bugs@example.com",
            pot_creation_date="",
            language_team="",
            header_comment="",
            statistics={"total_words": 0, "total_messages": 0},
        )

        # Validate deletion or update
        if value is None:
            # delete/reset
            if isinstance(key, list):
                if key not in self.metadata.paths():
                    raise KeyError(
                        f"The path '{key}' is not a present key in the metadata dictionary"
                    )
                # If we know a default for that path, use it, otherwise remove by setting empty value
                self.metadata[key] = (
                    default_meta[key] if key in default_meta.paths() else None
                )
            elif is_type(key, str):
                if not self.metadata.is_key(key):
                    raise KeyError(
                        f"The key '{key}' is not a present key in the metadata dictionary"
                    )
                self.metadata[key] = (
                    default_meta[key] if key in default_meta.keys() else None
                )
            else:
                raise TypeError("key must be a str or a list of str")
        else:
            # add/update
            if isinstance(key, list):
                if key not in self.metadata.paths():
                    # allow creating nested metadata path only for 'statistics'
                    # otherwise require existing path
                    raise KeyError(
                        f"The path '{key}' is not a present key in the metadata dictionary"
                    )
                self.metadata[key] = value
            elif is_type(key, str):
                if not self.metadata.is_key(key):
                    # For top-level additions, we allow adding a new simple key
                    self.metadata.update({key: value})
                else:
                    self.metadata[key] = value
            else:
                raise TypeError("key must be a str or a list of str")

        # Keep backward compatibility counter and recompute statistics if messages count involved
        self.metadata[["count", "messages"]] = len(self.messages)

    def get(self, index: str) -> Message | None:
        """
        Get a message by id.
        :param index: id of the message
        :type index: str
        :return: a message or None
        :rtype: Message
        """
        return self.messages.get(index, None)

    def __iter__(self):
        """
        Iterate over Message instances contained in the book.
        Yields Message objects in insertion order of the underlying dictionary.
        """
        return iter(self.messages.values())

    def add(self, domain: str, messages: list[Message]) -> None:
        """
        Add messages to the book if language and domain are identical.
        :param messages: list of messages to add to the book
        :type messages: list[Message]
        :param domain: the domain of the messages
        :type domain: str
        :return: nothing
        :rtype: None
        :raises ValueError: If a message is not compatible with this book language and domain or already registered.
        """
        if self.domain != domain:
            raise ValueError(
                f"Domain of message '{domain}' is not compatible with this book domain '{self.domain}'"
            )

        for message in messages:
            if message.metadata["language"] != self.language:
                raise ValueError(
                    f"Language of message ({message.id} : '{message.metadata['language']}') is not compatible with this book language ('{self.language}')"
                )

            if message.id in self.messages.keys():
                raise ValueError(
                    f"Message with id ({message.id}) is already present in this book"
                )

            self.messages[message.id] = message
            self.metadata[["count", "messages"]] = len(self.messages)
        # refresh statistics after adding all messages
        self._compute_statistics()

    def remove(self, index: str) -> None:
        """
        Remove a message from the book if language and domain are identical.
        :param index: key index of message to remove
        :type index: str
        :return: nothing
        :rtype: None
        :raises KeyError: If key message is not in this book.
        """

        if index not in self.messages.keys():
            raise ValueError(f"Message identifier {index} is not in this book")
        else:
            del self.messages[index]
            self.metadata[["count", "messages"]] = len(self.messages)
            self._compute_statistics()

    def check(self) -> list[Finding]:
        """
        Check the integrity of the messages of this book.

        A ``"draft"`` message is reported with severity ``"info"``: an
        empty principal singular or content that differs from its recorded
        counters is expected while a translation is in progress. The same
        points on a ``"complete"`` message are integrity defects, reported
        with severity ``"error"``, as is a complete message without
        recorded counters. Nothing is raised.

        :return: The findings, in message order; empty if nothing is wrong.
        :rtype: list[Finding]
        """
        findings: list[Finding] = []
        messages: list[Message] = list(self.messages.values())
        for message in messages:
            severity = "error" if message.status == "complete" else "info"
            if message.principal.singular == "":
                findings.append(
                    Finding(severity, message.id, "the principal singular is empty")
                )
            if not message.has_divergence:
                continue
            recorded = message.recorded
            if recorded is None:
                findings.append(
                    Finding(severity, message.id, "complete without recorded counters")
                )
                continue
            differences = describe_differences(recorded, message.observed)
            findings.append(
                Finding(
                    severity,
                    message.id,
                    "content differs from the recorded counters: "
                    + "; ".join(differences),
                )
            )
        return findings

    def load(self, path_directory: str) -> None:
        """
        Load messages and root metadata from a .i18t file into this Book instance.

        The file is located at ``path_directory/self.filename``.
        Each message is assigned the book language before insertion.

        The root metadata of the file replaces the matching entries of
        ``self.metadata`` and adds the keys this Book does not know, so
        that a save after a load writes them back. ``language`` and
        ``domain`` are attributes of the Book, not metadata: they are not
        copied. ``statistics`` and ``count`` are derived from the messages
        and recomputed after loading.

        The file is checked against the language and domain of this Book
        (see ``loader.load_book()``).

        :param path_directory: Directory containing the .i18t file.
        :type path_directory: str
        :raises FileNotFoundError: If the file does not exist.
        :raises FormatError: If the file content has errors.
        """
        file_path = path_directory + "/" + self.filename
        content = _load_book(file_path, self.language, self.domain)
        for key, value in content["metadata"].items():
            if key in _ROOT_ATTRIBUTE_KEYS or key in _ROOT_DERIVED_KEYS:
                continue
            self.metadata[key] = value
        for msgid, entry in content["entries"].items():
            parts = i18n_tools_format_to_message_dict(entry)
            msg = Message.from_matrix(
                msgid, parts["matrix"], parts["context"], parts["metadata"]
            )
            if self.language is not None:
                msg.add_language(self.language)
            self.messages[msgid] = msg
        self.metadata[["count", "messages"]] = len(self.messages)
        self._compute_statistics()

    def save(self, path_directory: str) -> None:
        """
        Save the content of this Book to a .i18t file.

        The file is written at ``path_directory/self.filename``.
        Delegates all I/O to ``save_book()`` in ``loader.py``,
        following the same delegation pattern as ``load()``. The message
        count and the statistics are recomputed first, so that the file
        never carries stale derived values.

        :param path_directory: Directory where the .i18t file will be written.
        :type path_directory: str
        :raises FileNotFoundError: If ``path_directory`` does not exist.

        References
        ----------
        - biface/i18n#42 : strict separation models / loaders (DD-06)
        - biface/i18n#57 : Book.save() persistence (DD-06, DD-15, DD-16)
        """
        from i18n_tools.loaders.loader import save_book as _save_book

        self.metadata[["count", "messages"]] = len(self.messages)
        self._compute_statistics()
        file_path = path_directory + "/" + self.filename
        _save_book(self, file_path)


class FallbackBook:
    """
    Transparent proxy over an ordered list of Books implementing the fallback chain.

    ``FallbackBook`` is never instantiated directly by the user — it is constructed
    by ``Corpus.get_book()`` from the chain of available Books that match the
    requested language (DD-09b).

    For each ``get_message()`` call the chain is walked in order; the first Book
    that contains the requested identifier wins.  If no Book in the chain holds
    the identifier, ``MessageNotFoundError`` is raised.

    The column fallback (DD-27) is orthogonal: it operates inside a single
    ``Message`` object and is handled by ``formatter.publish()``.

    References
    ----------
    - biface/i18n#43 : Corpus / FallbackBook proxy design (DD-09, DD-09b)
    - biface/i18n#20 : MessageNotFoundError (DD-24)
    """

    def __init__(self, chain: list["Book"], language: str) -> None:
        """
        Initialise the FallbackBook from an ordered list of real Books.

        :param chain: Ordered list of Books to consult, from most specific to
            least specific language.  Must not be empty.
        :type chain: List[Book]
        :param language: The requested language tag (first in the chain).
        :type language: str
        :raises ValueError: If ``chain`` is empty.
        """
        if not chain:
            raise ValueError("FallbackBook chain must contain at least one Book")
        self._chain: list["Book"] = chain
        self._language: str = language

    # --- Core message access ---

    def get_message(self, msg_id: str) -> Message:
        """
        Return the first Message matching ``msg_id`` found in the fallback chain.

        :param msg_id: Identifier of the message to retrieve.
        :type msg_id: str
        :return: The first matching Message.
        :rtype: Message
        :raises MessageNotFoundError: If no Book in the chain contains ``msg_id``.

        References
        ----------
        - biface/i18n#43 : FallbackBook chain resolution (DD-09b)
        - biface/i18n#20 : MessageNotFoundError (DD-24)
        """
        from i18n_tools.exceptions import MessageNotFoundError

        for book in self._chain:
            msg = book.get(msg_id)
            if msg is not None:
                return msg
        raise MessageNotFoundError(
            f"Message '{msg_id}' not found in fallback chain {[b.language for b in self._chain]}"
        )

    # --- Book-compatible interface ---

    @property
    def language(self) -> str:
        """The requested language — first language in the fallback chain."""
        return self._language

    @property
    def domain(self) -> str | None:
        """Domain of the first Book in the chain."""
        return self._chain[0].domain

    def __iter__(self):
        """Iterate over Message instances of the first Book in the chain."""
        return iter(self._chain[0])

    def __len__(self) -> int:
        """Number of messages in the first Book of the chain."""
        return len(self._chain[0].messages)

    def __contains__(self, msg_id: str) -> bool:
        """Return True if ``msg_id`` exists in any Book of the chain."""
        return any(book.get(msg_id) is not None for book in self._chain)

    @override
    def __repr__(self) -> str:
        langs = [b.language for b in self._chain]
        return f"FallbackBook(language='{self._language}', chain={langs})"
