"""
Exceptions Module
=================

Project-specific exception hierarchy for i18n-tools (DD-24).

All exceptions inherit from ``I18nToolsError``, which allows callers
to catch any package error with a single ``except I18nToolsError`` clause,
or to target a specific subclass for fine-grained handling.

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
