"""
Cell resolution: the DD-27 column fallback of a message matrix.

One definition shared by ``formatter.publish()``, which substitutes the
tokens of the resolved text, and by the cross-language check of
``Corpus``, which compares the tokens of the same resolved text. The
module imports nothing from the package, so that every layer may use
it.

Private module: not part of the public API.
"""

from __future__ import annotations


def resolve_cell(matrix: list[list[str]], segment: int, variant: int) -> str:
    """
    Return the text of the cell ``(segment, variant)`` after the DD-27
    four-step column fallback:

        1. ``(segment, variant)``
        2. -> ``(segment, 0)``
        3. -> ``(0, variant)``
        4. -> ``(0, 0)``

    ``""`` marks an absent text (DD-02) and moves to the next step. The
    address must be valid: the caller checks it.

    :param matrix: Message matrix, rows = segments, columns = variants.
    :type matrix: list[list[str]]
    :param segment: Row of the cell, 0 for the singular.
    :type segment: int
    :param variant: Column of the cell, 0 for the principal.
    :type variant: int
    :return: The resolved text; ``""`` only if the principal singular
        is empty.
    :rtype: str
    """
    for row, column in ((segment, variant), (segment, 0), (0, variant)):
        text = matrix[row][column]
        if text:
            return text
    return matrix[0][0]
