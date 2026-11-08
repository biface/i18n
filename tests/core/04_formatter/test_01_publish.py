"""
Test module for publish() in i18n_tools/formatter/publish.py (DD-27, DD-40)
"""

import pytest

from i18n_tools.exceptions import FormatterError, PluralIndexError
from i18n_tools.formatter.plurals import PluralRule
from i18n_tools.formatter.publish import publish
from i18n_tools.models import Declension, Message


class TestPublishSimplePath:
    def test_default_text_is_returned(self, simple_message):
        assert publish(simple_message, name="Ana") == "Hello Ana"

    def test_missing_variable_raises_formatter_error(self, simple_message):
        with pytest.raises(FormatterError, match="Missing variable 'name'"):
            publish(simple_message)

    def test_alternative_without_plural_rule_uses_row0(self, step1_message):
        # No plural_rule set: plural_index always stays 0, regardless of
        # any n passed in — only the alternative (column) moves.
        assert publish(step1_message, alternative=1, count=2) == "2 item (formal)"

    def test_n_is_ignored_when_no_plural_rule(self, step1_message):
        assert publish(step1_message, n=99, count=2) == "2 item"


class TestPublishColumnFallback:
    """DD-27's four-step column fallback, isolated one step at a time."""

    def test_step1_exact_cell_is_used_when_present(self, step1_message):
        rule = PluralRule("en", thresholds={5: 1})
        step1_message.plural_rule = rule
        result = publish(step1_message, alternative=1, n=5, count=5)
        assert result == "5 items (formal)"

    def test_step2_falls_back_to_main_column_same_row(self, step2_message):
        rule = PluralRule("en", thresholds={5: 1})
        step2_message.plural_rule = rule
        # cell (1, 1) absent -> falls back to the principal plural (1, 0)
        result = publish(step2_message, alternative=1, n=5, count=5)
        assert result == "5 items"

    def test_step3_falls_back_to_singular_same_alternative(self, step3_message):
        rule = PluralRule("en", thresholds={5: 1})
        step3_message.plural_rule = rule
        # row 1 exists but both its cells are empty markers -> options[1]
        result = publish(step3_message, alternative=1, n=5, count=5)
        assert result == "5 item (formal)"

    def test_step4_falls_back_to_singular_main(self, step4_message):
        rule = PluralRule("en", thresholds={5: 1})
        step4_message.plural_rule = rule
        # everything empty except messages[0][0]
        result = publish(step4_message, alternative=1, n=5, count=5)
        assert result == "5 item (singular main)"


class TestPublishPluralRuleResolution:
    def test_plural_rule_resolves_row_automatically(self, step1_message):
        rule = PluralRule("en", thresholds={3: 1})
        step1_message.plural_rule = rule
        assert publish(step1_message, n=3, count=3) == "3 items"

    def test_no_n_keeps_row0_even_with_a_plural_rule_set(self, step1_message):
        step1_message.plural_rule = PluralRule("en", thresholds={3: 1})
        assert publish(step1_message, count=1) == "1 item"

    def test_resolved_row_missing_raises_plural_index_error(self, step1_message):
        # Threshold points at row 4, which does not exist on this message
        # (the principal has a single plural).
        step1_message.plural_rule = PluralRule("en", thresholds={9: 4})
        with pytest.raises(PluralIndexError, match="does not exist on message 'cart'"):
            publish(step1_message, n=9, count=9)


class TestPublishColumnFallbackWithoutPluralRule:
    """
    Same fallback ladder as above, but reached with plural_index staying
    at 0 (no plural_rule involved) — exercises the branches where steps
    2/3 are skipped entirely because plural_index/alternative is already 0.
    """

    def test_falls_through_to_default_when_alternative_empty(self, step3_message):
        # plural_index stays 0 (no rule set): step1 (row0,col1) is empty,
        # step2 doesn't apply (plural_index == 0), step3 (row0,col1) is
        # the same empty cell again -> step4, the principal singular.
        step3_message.update_segment("", 0, 1)
        assert publish(step3_message, alternative=1, count=1) == "1 item"

    def test_falls_through_to_default_when_row_empty_and_alternative_is_0(
        self, step4_message
    ):
        # plural_index resolved to 1, alternative left at 0: step1/step2
        # both hit the same empty row1/col0 cell, step3 doesn't apply
        # (alternative == 0) -> step4, the principal singular.
        step4_message.plural_rule = PluralRule("en", thresholds={5: 1})
        result = publish(step4_message, n=5, count=5)
        assert result == "5 item (singular main)"


class TestPublishVariableSubstitution:
    def test_extra_kwargs_are_ignored(self, simple_message):
        assert publish(simple_message, name="Ana", unused="x") == "Hello Ana"

    def test_malformed_placeholder_raises_formatter_error(self, simple_message):
        simple_message.update_principal(singular="Hello {name")  # unclosed brace
        with pytest.raises(FormatterError, match="Error formatting message 'greet'"):
            publish(simple_message, name="Ana")

    def test_no_placeholders_no_kwargs_needed(self):
        from i18n_tools import __version__
        from i18n_tools.models import Message as MessageModel

        message = MessageModel(
            id="static",
            principal=Declension("Static text"),
            metadata={
                "version": __version__,
                "language": "en",
                "location": [],
                "flags": [],
                "user_comments": [],
                "auto_comments": [],
            },
        )
        assert publish(message) == "Static text"


class TestPublishMatrixRows:
    def test_row_used_only_by_a_variant_exists(self):
        """A plural row filled only in a variant is a row of the message."""
        message = Message(
            id="files",
            principal=Declension("one file"),
            variants=[Declension("one doc", ("two docs",))],
        )
        message.plural_rule = PluralRule("en", thresholds={2: 1})
        assert publish(message, alternative=1, n=2) == "two docs"

    def test_alternative_outside_the_matrix_falls_back(self):
        message = Message.from_matrix("files", [["one file"]])
        assert publish(message, alternative=3) == "one file"
