"""
Runtime type guards for the public entry points.

The library is used through typed object methods and procedures, but also
from untyped code (scripts, payloads read from files, a future REST layer).
Public entry points therefore check their arguments at runtime even when
the annotations already state the type.

A plain ``isinstance()`` on a parameter whose annotation already guarantees
the type is reported by the type checker as unnecessary, and the branch
that raises as unreachable. These helpers take the value as ``object``, so
the check stays meaningful to the checker while the annotations keep the
precise contract.

Private module: not part of the public API.
"""

from __future__ import annotations


def is_type(value: object, expected: type | tuple[type, ...]) -> bool:
    """Return ``isinstance(value, expected)`` for a runtime guard."""
    return isinstance(value, expected)


def ensure_type(
    value: object,
    expected: type | tuple[type, ...],
    message: str,
    error: type[Exception] = TypeError,
) -> None:
    """Raise ``error(message)`` unless ``value`` is an instance of ``expected``."""
    if not is_type(value, expected):
        raise error(message)
