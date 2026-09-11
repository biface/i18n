"""
Test module for PluralRule in i18n_tools/formatter/plurals.py (DD-40)
"""

import pytest

from i18n_tools.exceptions import PluralRuleError
from i18n_tools.formatter.plurals import PluralRule


class TestPluralRuleConstruction:
    def test_valid_locale_no_thresholds(self):
        rule = PluralRule("en")
        assert rule.locale == "en"
        assert rule.thresholds == {}

    def test_valid_locale_with_thresholds(self):
        rule = PluralRule("fr", thresholds={0: 2, 1: 0})
        assert rule.thresholds == {0: 2, 1: 0}

    def test_invalid_locale_raises_plural_rule_error(self):
        with pytest.raises(PluralRuleError, match="Invalid locale"):
            PluralRule("not-a-real-locale-zz-xx")

    @pytest.mark.parametrize(
        "thresholds",
        [
            {"one": 1},  # non-int key
            {1: "one"},  # non-int value
            {1.5: 1},  # float key
        ],
    )
    def test_malformed_thresholds_raise_plural_rule_error(self, thresholds):
        with pytest.raises(PluralRuleError, match="thresholds must map int to int"):
            PluralRule("en", thresholds=thresholds)

    def test_thresholds_property_is_a_copy(self):
        rule = PluralRule("en", thresholds={5: 1})
        returned = rule.thresholds
        returned[99] = 42
        assert rule.thresholds == {5: 1}


class TestPluralRuleResolution:
    def test_threshold_takes_priority_over_cldr(self):
        # For English, CLDR would resolve n=7 to "other" (not row 1),
        # but the explicit threshold must win.
        rule = PluralRule("en", thresholds={7: 1})
        assert rule(7) == 1

    def test_no_matching_threshold_falls_back_to_cldr(self):
        rule = PluralRule("en", thresholds={7: 1})
        # n=3 has no threshold entry: resolved via CLDR ("other" -> index 5
        # in the canonical zero/one/two/few/many/other order).
        assert rule(3) == 5

    def test_returns_an_int_row_index_not_a_category_string(self):
        rule = PluralRule("en")
        result = rule(1)
        assert isinstance(result, int)

    def test_english_singular_resolves_to_one_index(self):
        # CLDR "one" sits at index 1 in the canonical category order.
        rule = PluralRule("en")
        assert rule(1) == 1

    def test_calling_is_deterministic(self):
        rule = PluralRule("en", thresholds={2: 3})
        assert rule(2) == rule(2) == 3
