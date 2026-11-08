"""
Finding: one anomaly found by an integrity check.

Shared by the load check of the loaders and by ``Book.check()``. The
module imports nothing from the package, so that every layer may use it.

Private module: not part of the public API.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Finding:
    """
    One anomaly found by an integrity check.

    :ivar severity: ``"error"`` makes the content unusable or breaks an
        integrity obligation; ``"warning"`` reports a point the user has
        to look at, the content is still usable; ``"info"`` reports an
        expected state (a draft in progress), neither raised nor warned.
    :ivar where: Where the anomaly is: the root of a file or the
        identifier of a message.
    :ivar message: What is wrong, in plain words.
    """

    severity: Literal["error", "warning", "info"]
    where: str
    message: str
