"""
Exceptions Module
=================

Project-specific exception hierarchy for i18n-tools (DD-24).

All exceptions inherit from ``I18nToolsError``, which allows callers
to catch any package error with a single ``except I18nToolsError`` clause,
or to target a specific subclass for fine-grained handling.

``I18nToolsWarning`` reports a point the user has to look at without
stopping the operation; ``warnings.simplefilter("error",
I18nToolsWarning)`` turns it into an exception.

**License:**
This file is distributed under the terms of the CeCILL-C Free Software
License Agreement. By using, modifying, or redistributing this file,
you agree to comply with the terms of this license.
"""


class I18nToolsError(Exception):
    """Base class for all i18n-tools exceptions."""


class FormatError(I18nToolsError):
    """Raised when a .i18t file has an invalid or unexpected structure."""


class MessageError(I18nToolsError):
    """Raised when an operation on a Message object fails."""


class MessageNotFoundError(MessageError):
    """Raised when a message identifier cannot be found in any Book of the fallback chain."""


class BookError(I18nToolsError):
    """Raised when an operation on a Book object fails."""


class RepositoryError(I18nToolsError):
    """Raised when a configuration or repository operation fails."""


class LoaderError(I18nToolsError):
    """Raised when a file I/O operation in the loaders layer fails."""


class ConversionError(I18nToolsError):
    """Raised when a format conversion (e.g. Babel Catalog ↔ Book) fails."""


class LocaleError(I18nToolsError):
    """Raised when an IETF language tag is invalid or cannot be normalised."""


class FormatterError(I18nToolsError):
    """Raised when formatting/publishing a Message fails."""


class PluralIndexError(FormatterError):
    """
    Raised when a segment (plural row) does not exist on the Message.

    The segment was either given explicitly or resolved by the Message's
    ``PluralRule``. The fields let a caller handle the error without
    reading its text.

    :param message_id: Identifier of the message.
    :type message_id: str
    :param segment: The requested segment.
    :type segment: int
    :param segments: Number of segments of the message.
    :type segments: int
    """

    message_id: str
    segment: int
    segments: int

    def __init__(self, message_id: str, segment: int, segments: int) -> None:
        self.message_id = message_id
        self.segment = segment
        self.segments = segments
        super().__init__(
            f"Segment {segment} does not exist on message '{message_id}' "
            + f"(segments 0..{segments - 1})"
        )


class VariantIndexError(FormatterError):
    """
    Raised when a variant (column) does not exist on the Message.

    :param message_id: Identifier of the message.
    :type message_id: str
    :param variant: The requested variant.
    :type variant: int
    :param variants: Number of declensions of the message, principal
        included.
    :type variants: int
    """

    message_id: str
    variant: int
    variants: int

    def __init__(self, message_id: str, variant: int, variants: int) -> None:
        self.message_id = message_id
        self.variant = variant
        self.variants = variants
        super().__init__(
            f"Variant {variant} does not exist on message '{message_id}' "
            + f"(variants 0..{variants - 1})"
        )


class PluralRuleError(FormatterError):
    """Raised when a PluralRule configuration is invalid (e.g. malformed thresholds)."""


class I18nToolsWarning(UserWarning):
    """Warned when data is usable but has a point the user has to look at."""
