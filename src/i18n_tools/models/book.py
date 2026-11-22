"""
Book and FallbackBook: the messages of one domain in one language.
"""

import re
from collections.abc import Mapping
from datetime import datetime
from typing import TYPE_CHECKING, Required, TypedDict, Unpack, cast

from ndict_tools import StrictNestedDictionary

from i18n_tools.__static__ import (
    I18N_TOOLS_TRANSLATION_FILE_EXT,
    TranslationFileFormat,
)
from i18n_tools._checks import ensure_type, is_type
from i18n_tools._compat import override
from i18n_tools._finding import Finding
from i18n_tools._json import JSONInput
from i18n_tools.converter import i18n_tools_format_to_message_dict
from i18n_tools.exceptions import MessageError
from i18n_tools.loaders.loader import (
    DEFAULT_VERSION,
    FORMAT_VERSION,
    GETTEXT_KEYS,
    RESERVED_KEYS,
    build_book_filename,
)
from i18n_tools.loaders.loader import load_book as _load_book
from i18n_tools.locale import normalize_language_tag
from i18n_tools.models.message import Message

if TYPE_CHECKING:
    from i18n_tools.formatter.plurals import PluralRule

_SEMVER = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")
# Root metadata keys that are computed, never set.
_COMPUTED_KEYS = frozenset({"format_version", "count", "statistics"})


class BookOptions(TypedDict, total=False):
    """
    Keyword contract of :class:`Book`.

    ``language`` and ``domain`` are required; ``file_format`` defaults to
    ``"json"``. Any other key is refused with a ``TypeError``. The gettext
    fields are set by :meth:`Book.set_gettext` and the version by
    :attr:`Book.version`.
    """

    language: Required[str]
    domain: Required[str]
    file_format: TranslationFileFormat | None


_BOOK_OPTIONS = BookOptions.__required_keys__ | BookOptions.__optional_keys__


def _revision_date() -> str:
    """The local date and time of now, as gettext writes it: ``2026-11-21 17:30+0100``."""
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M%z")


def _path_text(keys: list[str]) -> str:
    """A path of the root metadata, written from the root."""
    return "[" + ", ".join(f'"{key}"' for key in ["metadata", *keys]) + "]"


class Book:
    """
    The messages of one domain in one language: the content of one
    ``.i18t`` file.

    :attr:`metadata` holds the keys of the root metadata of the file:
    ``format_version`` (the version of the format read, ``"1.0.0"`` for a
    new Book), ``version``, ``language``, ``domain``, ``gettext`` and
    ``rules``. The properties of the same names read these keys. ``count``
    and ``statistics`` are computed when the file is written.

    The class is iterable: iterating over a Book yields its Message
    instances in insertion order. :attr:`messages` maps each identifier to
    its message. The Book is the master of these keys: :meth:`add` holds a
    message under its ``id``, :meth:`rename` changes the key and the
    ``id`` together, and the file takes the key as the ``id`` of the entry.

    :ivar file_format: Storage encoding of the file (``"json"``).
    :ivar filename: Name of the file, ``<domain>.<file_format>.i18t``.
    :ivar messages: Identifier to Message.
    :ivar metadata: The root metadata.
    :ivar plural_rule: Rule of the Book, or None.
    """

    filename: str
    plural_rule: "PluralRule | None"
    messages: StrictNestedDictionary
    file_format: TranslationFileFormat | None
    metadata: StrictNestedDictionary

    def __init__(
        self,
        *args: Message | tuple[Message] | list[Message],
        **kwargs: Unpack[BookOptions],
    ) -> None:
        """
        Create a Book.

        :param args: Messages, or lists or tuples of messages, added as
            :meth:`add` adds them.
        :type args: Message | tuple[Message] | list[Message]
        :param kwargs: ``language`` and ``domain`` (required), and
            ``file_format``.
        :type kwargs: BookOptions
        :raises TypeError: If a keyword is not one of the options,
            ``language`` or ``domain`` is not a string, or an argument is
            not a message.
        :raises KeyError: If ``language`` or ``domain`` is missing.
        :raises ValueError: If an identifier is reserved or given twice.
        """
        unknown = sorted(set(kwargs) - _BOOK_OPTIONS)
        if unknown:
            raise TypeError(f"Unknown Book option(s): {', '.join(unknown)}")

        self.filename = ""
        self.plural_rule = None
        language = cast(object, kwargs.get("language"))
        if language is None:
            raise KeyError("No language specified")
        elif not isinstance(language, str):
            raise TypeError("Book language must be a string.")

        domain = cast(object, kwargs.get("domain"))
        if domain is None:
            raise KeyError("No domain specified")
        elif not isinstance(domain, str):
            raise TypeError("Book domain must be a string.")

        self.messages = StrictNestedDictionary()
        self.metadata = StrictNestedDictionary(
            {
                "format_version": FORMAT_VERSION,
                "version": DEFAULT_VERSION,
                "language": normalize_language_tag(language),
                "domain": domain,
                "gettext": dict.fromkeys(GETTEXT_KEYS, ""),
                "rules": {},
            }
        )
        self.file_format, self.filename = build_book_filename(
            domain, kwargs.get("file_format")
        )

        for entity in args:
            if is_type(entity, (tuple, list)):
                for message in cast("tuple[Message] | list[Message]", entity):
                    self.add(message)
            else:
                self.add(cast(Message, entity))

    # --- Keys of the root metadata -------------------------------------------

    @property
    def language(self) -> str | None:
        """
        Normalized language tag of the Book, ``metadata["language"]``.

        :return: The language, or None once removed.
        :rtype: str | None
        """
        return cast("str | None", self.metadata["language"])

    @language.setter
    def language(self, value: str | None) -> None:
        self.metadata["language"] = (
            None if value is None else normalize_language_tag(value)
        )

    @property
    def domain(self) -> str | None:
        """
        Domain of the Book, ``metadata["domain"]``.

        :return: The domain, or None once removed.
        :rtype: str | None
        """
        return cast("str | None", self.metadata["domain"])

    @domain.setter
    def domain(self, value: str | None) -> None:
        self.metadata["domain"] = value

    @property
    def format_version(self) -> str:
        """
        Version of the format read, ``metadata["format_version"]``;
        ``"1.0.0"`` for a new Book. A writer always writes ``"1.0.0"``.

        :return: The format version.
        :rtype: str
        """
        return cast(str, self.metadata["format_version"])

    @property
    def version(self) -> str:
        """
        Version of the translation, ``metadata["version"]``: a strict
        semantic version, ``"0.0.1"`` for a new Book.

        :return: The version.
        :rtype: str
        """
        return cast(str, self.metadata["version"])

    @version.setter
    def version(self, value: str) -> None:
        if not is_type(value, str):
            raise TypeError(f"Book version must be a str, got {type(value)}")
        if _SEMVER.fullmatch(value) is None:
            raise ValueError(
                f"Book version '{value}' is not a strict semantic version "
                + "(MAJOR.MINOR.PATCH)"
            )
        self.metadata["version"] = value

    def set_version(self, version: str) -> None:
        """
        Set the version of the translation.

        :param version: A strict semantic version (``"1.2.0"``).
        :type version: str
        :raises TypeError: If ``version`` is not a string.
        :raises ValueError: If ``version`` is not a strict semantic version.
        """
        self.version = version

    def set_gettext(self, **fields: str) -> None:
        """
        Set fields of the ``gettext`` mapping.

        :param fields: Values of ``project_id_version``,
            ``report_msgid_bugs_to``, ``pot_creation_date``,
            ``po_revision_date``, ``last_translator``, ``language_team``
            or ``header_comment``.
        :type fields: str
        :raises TypeError: If a key is not one of the seven, or a value is
            not a string.
        """
        unknown = sorted(set(fields) - set(GETTEXT_KEYS))
        if unknown:
            raise TypeError(f"Unknown gettext key(s): {', '.join(unknown)}")
        for key, value in fields.items():
            if not is_type(value, str):
                raise TypeError(f"gettext {key} must be a str, got {type(value)}")
            self.metadata[["gettext", key]] = value

    def set_metadata(
        self, key: str | list[str] | None, value: JSONInput = None
    ) -> None:
        """
        Set, or reset to its default with ``value=None``, a key of the root
        metadata.

        ``version``, ``language`` and ``domain`` go through their property;
        a path ``["gettext", <field>]`` sets one gettext field; ``rules``
        and any path inside it are written as given, the content of
        ``rules`` being open. ``format_version``, ``count`` and
        ``statistics`` cannot be set.

        :param key: A key, or a path from the root metadata.
        :type key: str | list[str] | None
        :param value: The value; None resets the default.
        :type value: JSONInput
        :raises KeyError: If the key or the path is not one of the root
            metadata, or cannot be set.
        :raises TypeError: If ``key`` is neither a string nor a list of
            strings, or a value has the wrong type.
        :raises ValueError: If a value is refused by its property.
        """
        if key is None:
            raise KeyError("A metadata key or path must be provided")
        if is_type(key, str):
            keys = [cast(str, key)]
        elif is_type(key, list) and all(is_type(item, str) for item in key):
            keys = list(cast("list[str]", key))
        else:
            raise TypeError("key must be a str or a list of str")
        if len(keys) == 0:
            raise KeyError("A metadata key or path must be provided")
        head = keys[0]
        if head in _COMPUTED_KEYS:
            raise KeyError(f"{_path_text(keys)} cannot be set")
        if head == "gettext" and len(keys) == 2 and keys[1] in GETTEXT_KEYS:
            self.set_gettext(**{keys[1]: "" if value is None else cast(str, value)})
        elif head == "rules":
            if len(keys) == 1:
                rules = {} if value is None else value
                if not is_type(rules, Mapping):
                    raise TypeError(f"Book rules must be a mapping, got {type(rules)}")
                self.metadata["rules"] = StrictNestedDictionary(
                    dict(cast("Mapping[str, JSONInput]", rules)),
                    default_setup=dict(self.metadata.default_setup),
                )
            elif value is None:
                if keys not in self.metadata.paths():
                    raise KeyError(
                        f"{_path_text(keys)} is not a key of the Book metadata"
                    )
                del self.metadata[keys]
            else:
                self.metadata[keys] = value
        elif len(keys) == 1 and head == "version":
            self.version = DEFAULT_VERSION if value is None else cast(str, value)
        elif len(keys) == 1 and head in ("language", "domain"):
            setattr(self, head, value)
        else:
            raise KeyError(f"{_path_text(keys)} is not a key of the Book metadata")

    # --- Attribute management for language, domain, and file format ---
    def __set_filename(self) -> None:
        """
        Set or update the file name when the domain or the format changes.
        """
        if self.domain is not None and self.file_format is not None:
            self.filename = (
                self.domain
                + "."
                + self.file_format
                + "."
                + I18N_TOOLS_TRANSLATION_FILE_EXT
            )

    def get_language(self) -> str | None:
        """Return the normalized language tag of this book."""
        return self.language

    def add_language(self, lang: str) -> None:
        """Set the language if not already set; value is normalized."""
        if self.language is not None:
            raise ValueError("Language is already set for this book")
        self.language = lang

    def update_language(self, lang: str) -> None:
        """Update the book language; the value is normalized."""
        self.language = lang

    def remove_language(self) -> None:
        """Unset the book language (may leave the book in an inconsistent state)."""
        self.language = None

    def get_domain(self) -> str | None:
        """Return the domain of this book."""
        return self.domain

    def add_domain(self, domain: str) -> None:
        """Set the domain if not already set."""
        if self.domain is not None:
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

    def get_file_format(self) -> TranslationFileFormat | None:
        """Return the storage file format of this book."""
        return self.file_format

    def add_file_format(self, fmt: TranslationFileFormat) -> None:
        """Set the file format if not already set."""
        if getattr(self, "file_format", None) is not None:
            raise ValueError("File format is already set for this book")
        if self.domain is None:
            raise ValueError("Domain must be set before setting the file format")
        self.file_format, self.filename = build_book_filename(self.domain, fmt)

    def update_file_format(self, fmt: TranslationFileFormat) -> None:
        """Update the file format."""
        if self.domain is None:
            raise ValueError("Domain must be set before updating the file format")
        self.file_format, self.filename = build_book_filename(self.domain, fmt)

    def remove_file_format(self) -> None:
        """Unset the file format."""
        self.file_format = None
        self.filename = ""

    # --- Messages ------------------------------------------------------------

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

    @staticmethod
    def _check_key(identifier: str) -> None:
        """Refuse a root key of a file that cannot be an identifier."""
        if identifier == "metadata" or identifier in RESERVED_KEYS:
            raise ValueError(
                f"'{identifier}' is reserved and cannot be a message identifier"
            )

    def add(self, message: Message) -> None:
        """
        Hold a message under its identifier, ``message.id``.

        :param message: The message to add.
        :type message: Message
        :raises TypeError: If ``message`` is not a Message.
        :raises ValueError: If the identifier is reserved (``metadata``,
            ``.pyi18t_tools``, ``.i18n_tools``) or already in the Book.
        """
        ensure_type(
            message, Message, f"Book.add() takes a Message, got {type(message)}"
        )
        identifier = message.id
        self._check_key(identifier)
        if identifier in self.messages.keys():
            raise ValueError(
                f"Message with id ({identifier}) is already present in this book"
            )
        self.messages[identifier] = message

    def rename(self, old: str, new: str) -> None:
        """
        Change the identifier of a message: its key in the Book and its
        ``id`` together. The message keeps its place in the Book.

        :param old: The current identifier.
        :type old: str
        :param new: The new identifier, as ``Message.id`` accepts it.
        :type new: str
        :raises KeyError: If ``old`` is not in the Book.
        :raises TypeError: If ``new`` is neither a str nor an int.
        :raises ValueError: If ``new`` is empty, reserved or already in the
            Book.
        """
        if old not in self.messages.keys():
            raise KeyError(f"Message identifier '{old}' is not in this book")
        message: Message = self.messages[old]
        previous = message.id
        message.id = new
        identifier = message.id
        try:
            self._check_key(identifier)
            if identifier != old and identifier in self.messages.keys():
                raise ValueError(
                    f"Message with id ({identifier}) is already present in this book"
                )
        except ValueError:
            message.id = previous
            raise
        held: list[tuple[str, Message]] = [
            (identifier if key == old else str(key), value)
            for key, value in self.messages.items()
        ]
        self.messages.clear()
        for key, value in held:
            self.messages[key] = value

    def remove(self, index: str) -> None:
        """
        Remove a message from the book.
        :param index: key index of message to remove
        :type index: str
        :raises ValueError: If key message is not in this book.
        """
        if index not in self.messages.keys():
            raise ValueError(f"Message identifier {index} is not in this book")
        del self.messages[index]

    def check(self) -> list[Finding]:
        """
        Check the integrity of the messages of this book.

        A ``"draft"`` message is reported with severity ``"info"``: an
        empty principal singular or content that differs from its record
        is expected while a translation is in progress. The same points on
        a ``"complete"`` message are integrity defects, reported with
        severity ``"error"``, as is a complete message without a record.
        Nothing is raised.

        :return: The findings, in message order; empty if nothing is wrong.
        :rtype: list[Finding]
        """
        findings: list[Finding] = []
        for key, message in self.messages.items():
            identifier = str(key)
            severity = "error" if message.status == "complete" else "info"
            if message.principal.singular == "":
                findings.append(
                    Finding(severity, identifier, "the principal singular is empty")
                )
            if not message.has_divergence:
                continue
            recorded = message.recorded
            if recorded is None:
                findings.append(
                    Finding(severity, identifier, "complete without recorded counters")
                )
                continue
            differences = recorded.differences(message.observed)
            findings.append(
                Finding(
                    severity,
                    identifier,
                    "content differs from the recorded counters: "
                    + "; ".join(differences),
                )
            )
        return findings

    def load(self, path_directory: str) -> None:
        """
        Load the root metadata and the messages of a .i18t file into this Book.

        The file is ``path_directory/self.filename``. It is checked against
        the language and the domain of this Book by the rules of the format
        (``loader.load_book()``). The root metadata of the file replaces
        that of the Book; each entry becomes a message held under its key,
        with its status and its record as read.

        :param path_directory: Directory containing the .i18t file.
        :type path_directory: str
        :raises FileNotFoundError: If the file does not exist.
        :raises FormatError: If the file content has errors.
        """
        file_path = path_directory + "/" + self.filename
        content = _load_book(file_path, self.language, self.domain)
        for key, value in content["metadata"].items():
            self.metadata[key] = (
                StrictNestedDictionary(
                    value, default_setup=dict(self.metadata.default_setup)
                )
                if isinstance(value, dict)
                else value
            )
        for identifier, entry in content["entries"].items():
            parts = i18n_tools_format_to_message_dict(entry)
            message = Message(identifier, parts["singular"], **parts["options"])
            message.metadata["status"] = parts["status"]
            for key, value in parts["record"].items():
                message.metadata[key] = StrictNestedDictionary(
                    cast("dict[str, object]", value),
                    default_setup=dict(message.metadata.default_setup),
                )
            self.messages[identifier] = message

    def save(self, path_directory: str) -> None:
        """
        Save the content of this Book to a .i18t file.

        The file is ``path_directory/self.filename``, written by
        ``loader.save_book()`` in format 1.0.0. ``po_revision_date`` takes
        the date and time of the write. A complete message that diverges
        from its record, or has none, is never written over the last sound
        state: the save is refused before anything is written. Once the
        file is written, each draft records its content
        (``Message.record()``): saving a draft is a validation point.

        :param path_directory: Directory where the .i18t file will be written.
        :type path_directory: str
        :raises MessageError: If a complete message diverges.
        :raises FileNotFoundError: If ``path_directory`` does not exist.
        """
        from i18n_tools.loaders.loader import save_book as _save_book

        messages: list[Message] = list(self.messages.values())
        diverging = [
            message.id
            for message in messages
            if message.status == "complete" and message.has_divergence
        ]
        if diverging:
            raise MessageError(
                f"Book '{self.domain}' not saved: complete message(s) "
                + f"{', '.join(diverging)} diverge from their recorded counters"
            )
        self.metadata[["gettext", "po_revision_date"]] = _revision_date()
        file_path = path_directory + "/" + self.filename
        _save_book(self, file_path)
        for message in messages:
            if message.status == "draft":
                message.record()


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
