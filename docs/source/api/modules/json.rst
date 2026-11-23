JSON types (internal)
=====================

Type aliases for the data read from or written to JSON, YAML and TOML
files: ``.i18t`` Books, locale files and settings files, whose content is
only known to be JSON-like until it has been checked. Internal module:
not part of the public API.

.. py:module:: i18n_tools._json

.. py:type:: JSONValue
   :canonical: str | int | float | bool | None | list[JSONValue] | dict[str, JSONValue]

   What a reader returns: ``dict`` and ``list`` containers, as built by
   ``json.load()`` or ``yaml.safe_load()``.

.. py:type:: JSONInput
   :canonical: str | int | float | bool | None | Sequence[JSONInput] | Mapping[str, JSONInput]

   What a writer accepts: read-only ``Mapping`` and ``Sequence``
   containers. ``dict`` and ``list`` are invariant, so a
   ``dict[str, list[int]]`` is not a ``dict[str, JSONValue]``; it is a
   ``Mapping[str, JSONInput]``.
