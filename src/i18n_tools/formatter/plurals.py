"""
Plurals Module
==============

Implements ``PluralRule`` (DD-40): a project-owned plural resolution
rule. It uses a CLDR rule for a given locale (via Babel) as its
baseline, and layers an explicit overlay of business-defined numeric
thresholds on top, for plural forms CLDR does not distinguish (e.g.
"1 / 2 / several").

Unlike ``babel.plural.PluralRule``, which resolves a count to a CLDR
category string (``"zero"``, ``"one"``, ``"two"``, ``"few"``,
``"many"``, ``"other"``), this class always resolves to an integer
plural *row index* — consistent with DD-03's free, CLDR-unconstrained
plural rows. ``formatter.publish()`` (DD-27) consumes that index
directly, with no knowledge of CLDR categories.

Key Responsibilities:
    - Resolve an integer count to a plural row index.
    - Give business thresholds (exact match on the count) priority over
      the CLDR-derived category.
    - Fail loudly, at construction time, on a malformed threshold
      overlay (``PluralRuleError``).
"""

from __future__ import annotations

from babel.core import Locale, UnknownLocaleError

from ..exceptions import PluralRuleError

# Canonical CLDR category order (DD-40): used to resolve a CLDR category
# to a row index when no business threshold matches for a given count.
_CLDR_CATEGORY_ORDER = ("zero", "one", "two", "few", "many", "other")


class PluralRule:
    """
    A CLDR baseline (via Babel), for a given locale, with an explicit
    overlay of business-defined thresholds that take priority.

    Calling an instance with an integer count returns a plural row
    index (``int``), never a CLDR category string.
    """

    def __init__(
        self, locale: str, thresholds: dict[int, int] | None = None
    ) -> None:
        """
        :param locale: IETF language tag identifying the CLDR plural
            rule to use as the baseline (e.g. ``"fr"``, ``"pl"``).
        :type locale: str
        :param thresholds: Optional mapping of an exact count to the
            plural row index it must resolve to, taking priority over
            the CLDR-derived category. Defaults to no overlay.
        :type thresholds: dict[int, int] | None
        :raises PluralRuleError: If ``locale`` cannot be parsed by
            Babel, or ``thresholds`` maps anything other than ``int``
            to ``int``.
        """
        try:
            self._locale = Locale.parse(locale)
        except (UnknownLocaleError, ValueError) as e:
            raise PluralRuleError(
                f"Invalid locale for PluralRule: {locale!r}"
            ) from e

        if thresholds is not None:
            for key, value in thresholds.items():
                if not isinstance(key, int) or not isinstance(value, int):
                    raise PluralRuleError(
                        f"PluralRule thresholds must map int to int, "
                        f"got {key!r}: {value!r}"
                    )

        self._thresholds: dict[int, int] = dict(thresholds) if thresholds else {}

    def __call__(self, n: int) -> int:
        """
        Resolve ``n`` to a plural row index.

        Business thresholds (exact match on ``n``) take priority. When
        none matches, the CLDR category for ``n`` is resolved to a row
        index via the canonical category order.

        :param n: The count driving plural resolution.
        :type n: int
        :return: The resolved plural row index.
        :rtype: int
        """
        if n in self._thresholds:
            return self._thresholds[n]

        category = self._locale.plural_form(n)
        return _CLDR_CATEGORY_ORDER.index(category)

    @property
    def locale(self) -> str:
        """The IETF language tag this rule's CLDR baseline was built from."""
        return str(self._locale)

    @property
    def thresholds(self) -> dict[int, int]:
        """The business threshold overlay, as a copy (read-only view)."""
        return dict(self._thresholds)
