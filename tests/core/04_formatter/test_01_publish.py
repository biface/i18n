"""
Tests for publish() in i18n_tools/formatter/publish.py (DD-27, DD-40),
grouped by contract: segment selection, column fallback, address errors,
arguments and tokens.

Fixtures (local conftest.py): ``simple_message`` (one cell),
``step1_message`` to ``step4_message`` (2 segments x 2 declensions,
emptied step by step to reach each step of the fallback).
"""

import pytest

from i18n_tools.exceptions import (
    FormatterError,
    PluralIndexError,
    VariantIndexError,
)
from i18n_tools.formatter.plurals import PluralRule
from i18n_tools.formatter.publish import publish
from i18n_tools.models import Declension, Message


class TestSegmentSelection:
    def test_default_is_the_principal_singular(self, step1_message):
        assert publish(step1_message, count=1) == "1 item"

    @pytest.mark.parametrize(
        "variant, segment, expected",
        [
            (0, 0, "2 item"),
            (0, 1, "2 items"),
            (1, 0, "2 item (formal)"),
            (1, 1, "2 items (formal)"),
        ],
    )
    def test_explicit_segment(self, step1_message, variant, segment, expected):
        assert publish(step1_message, variant, segment, count=2) == expected

    def test_explicit_segment_without_plural_rule(self, step1_message):
        assert step1_message.plural_rule is None
        assert publish(step1_message, segment=1, count=2) == "2 items"

    def test_n_resolved_by_the_plural_rule(self, step1_message):
        step1_message.plural_rule = PluralRule("en", thresholds={3: 1})
        assert publish(step1_message, n=3, count=3) == "3 items"
        assert publish(step1_message, variant=1, n=3, count=3) == "3 items (formal)"

    def test_n_ignored_without_plural_rule(self, step1_message):
        assert publish(step1_message, n=99, count=2) == "2 item"

    def test_plural_rule_unused_without_n(self, step1_message):
        step1_message.plural_rule = PluralRule("en", thresholds={3: 1})
        assert publish(step1_message, count=1) == "1 item"

    def test_segment_used_only_by_a_variant(self):
        """A plural row filled only in a variant is a row of the message."""
        message = Message(
            id="files",
            principal=Declension("one file"),
            variants=[Declension("one doc", ("two docs",))],
        )
        message.plural_rule = PluralRule("en", thresholds={2: 1})
        assert publish(message, variant=1, n=2) == "two docs"


class TestColumnFallback:
    """DD-27's four-step column fallback, one step at a time."""

    def test_step1_exact_cell(self, step1_message):
        assert publish(step1_message, 1, 1, count=5) == "5 items (formal)"

    def test_step2_principal_same_segment(self, step2_message):
        assert publish(step2_message, 1, 1, count=5) == "5 items"

    def test_step3_singular_same_variant(self, step3_message):
        assert publish(step3_message, 1, 1, count=5) == "5 item (formal)"

    def test_step4_principal_singular(self, step4_message):
        assert publish(step4_message, 1, 1, count=5) == "5 item (singular main)"

    def test_same_ladder_through_the_plural_rule(self, step2_message):
        step2_message.plural_rule = PluralRule("en", thresholds={5: 1})
        assert publish(step2_message, variant=1, n=5, count=5) == "5 items"

    def test_empty_variant_singular_falls_to_the_principal(self, step3_message):
        step3_message.update_segment("", 0, 1)
        assert publish(step3_message, variant=1, count=1) == "1 item"

    def test_empty_principal_plural_falls_to_the_singular(self, step4_message):
        assert publish(step4_message, segment=1, count=5) == "5 item (singular main)"


class TestAddressErrors:
    @pytest.mark.parametrize("segment", [2, 9, -1])
    def test_explicit_segment_outside_the_matrix(self, step1_message, segment):
        with pytest.raises(PluralIndexError) as caught:
            publish(step1_message, segment=segment, count=1)
        error = caught.value
        assert (error.message_id, error.segment, error.segments) == (
            "cart",
            segment,
            2,
        )
        assert isinstance(error, FormatterError)

    def test_resolved_segment_outside_the_matrix(self, step1_message):
        step1_message.plural_rule = PluralRule("en", thresholds={9: 4})
        with pytest.raises(
            PluralIndexError, match="Segment 4 does not exist on message 'cart'"
        ) as caught:
            publish(step1_message, n=9, count=9)
        assert (caught.value.segment, caught.value.segments) == (4, 2)

    @pytest.mark.parametrize("variant", [2, 7, -1])
    def test_variant_outside_the_matrix(self, step1_message, variant):
        """Regression: an unknown variant fell back to the principal silently."""
        with pytest.raises(VariantIndexError) as caught:
            publish(step1_message, variant=variant, count=1)
        error = caught.value
        assert (error.message_id, error.variant, error.variants) == (
            "cart",
            variant,
            2,
        )
        assert isinstance(error, FormatterError)

    def test_variant_error_message(self):
        message = Message.from_matrix("files", [["one file"]])
        with pytest.raises(
            VariantIndexError,
            match=r"Variant 3 does not exist on message 'files' \(variants 0\.\.0\)",
        ):
            publish(message, variant=3)


class TestArguments:
    def test_segment_and_n_exclude_each_other(self, step1_message):
        step1_message.plural_rule = PluralRule("en", thresholds={3: 1})
        with pytest.raises(ValueError, match="segment or n, not both"):
            publish(step1_message, segment=1, n=3, count=3)

    @pytest.mark.parametrize(
        "kwargs, name",
        [
            ({"variant": "1"}, "variant must be an int"),
            ({"variant": True}, "variant must be an int"),
            ({"variant": None}, "variant must be an int"),
            ({"segment": 1.0}, "segment must be an int or None"),
            ({"segment": False}, "segment must be an int or None"),
            ({"n": "3"}, "n must be an int or None"),
        ],
        ids=[
            "variant-str",
            "variant-bool",
            "variant-none",
            "segment-float",
            "segment-bool",
            "n-str",
        ],
    )
    def test_wrong_types(self, step1_message, kwargs, name):
        with pytest.raises(TypeError, match=name):
            publish(step1_message, count=1, **kwargs)

    def test_message_must_be_a_message(self):
        with pytest.raises(TypeError, match="message must be a Message"):
            publish("cart")  # pyright: ignore[reportArgumentType]


class TestTokens:
    def test_tokens_are_substituted(self, simple_message):
        assert publish(simple_message, name="Ana") == "Hello Ana"

    def test_extra_tokens_are_ignored(self, simple_message):
        assert publish(simple_message, name="Ana", unused="x") == "Hello Ana"

    def test_text_without_tokens(self):
        message = Message("static", Declension("Static text"))
        assert publish(message) == "Static text"

    def test_missing_token(self, simple_message):
        with pytest.raises(
            FormatterError, match="Missing token 'name' for message 'greet'"
        ):
            publish(simple_message)

    def test_malformed_text(self, simple_message):
        simple_message.update_principal(singular="Hello {name")
        with pytest.raises(FormatterError, match="Error formatting message 'greet'"):
            publish(simple_message, name="Ana")
