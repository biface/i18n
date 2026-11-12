"""
Type aliases for data parsed from or written to JSON, YAML and TOML files.

The library reads ``.i18t`` books, locale files and settings files whose
content is only known to be JSON-like until it has been checked. These
aliases name that content precisely instead of ``Any``.

``JSONValue``
    What a reader returns: concrete ``dict`` and ``list`` containers, as
    built by ``json.load()`` or ``yaml.safe_load()``.

``JSONInput``
    What a writer accepts: read-only ``Mapping`` and ``Sequence``
    containers. ``dict`` and ``list`` are invariant, so a
    ``dict[str, list[int]]`` is not a ``dict[str, JSONValue]``; it is a
    ``Mapping[str, JSONInput]``.

Both aliases are recursive ``TypeAliasType`` objects, so that they keep
their name at runtime (in the rendered signatures, for instance).

Private module: not part of the public API.
"""

from collections.abc import Mapping, Sequence

from i18n_tools._compat import TypeAliasType

JSONValue = TypeAliasType(
    "JSONValue",
    str | int | float | bool | None | list["JSONValue"] | dict[str, "JSONValue"],
)
JSONInput = TypeAliasType(
    "JSONInput",
    str | int | float | bool | None | Sequence["JSONInput"] | Mapping[str, "JSONInput"],
)

__all__ = ["JSONInput", "JSONValue"]
