Exceptions
==========

.. py:module:: i18n_tools.exceptions

Every exception of the package derives from :exc:`I18nToolsError`: one
``except I18nToolsError`` clause catches any of them, and a subclass
targets one kind of failure.

.. mermaid::

    flowchart TD
        base["I18nToolsError"]
        base --> FormatError
        base --> MessageError
        MessageError --> MessageNotFoundError
        base --> BookError
        base --> RepositoryError
        base --> LoaderError
        base --> ConversionError
        base --> LocaleError
        base --> FormatterError
        FormatterError --> PluralIndexError
        FormatterError --> VariantIndexError
        FormatterError --> PluralRuleError

:exc:`PluralIndexError` and :exc:`VariantIndexError` carry the message
identifier and the requested index as fields, so that a caller can handle
them without reading their text.

:class:`I18nToolsWarning` reports a point to look at without stopping
the operation, for instance a warning found while loading a file.
``warnings.simplefilter("error", I18nToolsWarning)`` turns it into an
exception.

.. todo::

   - Which operation raises which exception.
   - Built-in exceptions raised by the argument checks (TypeError,
     ValueError) and their place next to this hierarchy.

Base class
----------

.. autoexception:: I18nToolsError

Files and messages
------------------

.. autoexception:: FormatError
.. autoexception:: MessageError
.. autoexception:: MessageNotFoundError
.. autoexception:: BookError

Repository, files and conversions
---------------------------------

.. autoexception:: RepositoryError
.. autoexception:: LoaderError
.. autoexception:: ConversionError
.. autoexception:: LocaleError

Formatting
----------

.. autoexception:: FormatterError
.. autoexception:: PluralIndexError
.. autoexception:: VariantIndexError
.. autoexception:: PluralRuleError

Warning
-------

.. autoclass:: I18nToolsWarning
