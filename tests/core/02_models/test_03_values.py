"""
Tests for the value types: Declension and Location (models.message),
ContentCounters (_counters) and Finding (_finding).
"""

import pytest

from i18n_tools import ContentCounters as PublicContentCounters
from i18n_tools import Declension as PublicDeclension
from i18n_tools import Location as PublicLocation
from i18n_tools._counters import (
    count_content,
    counters_from_entry,
    counters_to_entry,
    describe_differences,
)
from i18n_tools._finding import Finding
from i18n_tools.models import ContentCounters, Declension, Location


class TestDeclension:
    def test_defaults(self):
        declension = Declension()
        assert declension.singular == ""
        assert declension.plurals == ()
        assert declension.segments == ("",)

    def test_segments_singular_first(self):
        declension = Declension("one file", ("two files", "{n} files"))
        assert declension.segments == ("one file", "two files", "{n} files")

    def test_frozen(self):
        declension = Declension("one", ("two",))
        with pytest.raises(AttributeError):
            declension.singular = "uno"  # pyright: ignore[reportAttributeAccessIssue]
        with pytest.raises(AttributeError):
            declension.plurals = ("dos",)  # pyright: ignore[reportAttributeAccessIssue]

    def test_hashable(self):
        assert hash(Declension("a", ("b",))) == hash(Declension("a", ("b",)))
        assert len({Declension("a", ("b",)), Declension("a", ("b",))}) == 1

    def test_equality_by_content(self):
        assert Declension("a", ("b",)) == Declension("a", ("b",))
        assert Declension("a", ("b",)) != Declension("a", ("c",))

    def test_from_segments(self):
        assert Declension.from_segments(["a", "b", "c"]) == Declension("a", ("b", "c"))
        assert Declension.from_segments(("a",)) == Declension("a", ())

    def test_from_segments_copies_input(self):
        segments = ["a", "b"]
        declension = Declension.from_segments(segments)
        segments.append("c")
        assert declension.plurals == ("b",)

    def test_from_segments_empty(self):
        with pytest.raises(ValueError):
            Declension.from_segments([])

    @pytest.mark.parametrize(
        "args",
        [(1, ()), ("a", "b"), ("a", ("b", 2)), ("a", None), ("a", ["b"])],
        ids=[
            "singular-int",
            "plurals-str",
            "plural-int",
            "plurals-none",
            "plurals-list",
        ],
    )
    def test_type_errors(self, args):
        with pytest.raises(TypeError):
            Declension(*args)

    @pytest.mark.parametrize(
        "segments", ["abc", None, {"a"}], ids=["str", "none", "set"]
    )
    def test_from_segments_type_error(self, segments):
        with pytest.raises(TypeError):
            Declension.from_segments(segments)  # pyright: ignore[reportArgumentType]

    def test_from_segments_plural_type_error(self):
        with pytest.raises(TypeError):
            Declension.from_segments(["a", 2])  # pyright: ignore[reportArgumentType]

    def test_public_export(self):
        assert PublicDeclension is Declension


class TestLocation:
    def test_whole_message(self):
        location = Location("app.py", 12)
        assert (location.variant, location.segment) == (None, None)

    def test_coordinates(self):
        location = Location("app.py", 12, variant=1, segment=0)
        assert (location.variant, location.segment) == (1, 0)

    def test_frozen(self):
        location = Location("app.py", 12)
        with pytest.raises(AttributeError):
            location.line = 13  # pyright: ignore[reportAttributeAccessIssue]

    def test_hashable(self):
        assert len({Location("a.py", 1), Location("a.py", 1)}) == 1

    @pytest.mark.parametrize(
        "args, kwargs",
        [
            ((3, 1), {}),
            (("a.py", "1"), {}),
            (("a.py", True), {}),
            (("a.py", 1), {"variant": "0"}),
            (("a.py", 1), {"segment": False}),
        ],
        ids=["file-int", "line-str", "line-bool", "variant-str", "segment-bool"],
    )
    def test_type_errors(self, args, kwargs):
        with pytest.raises(TypeError):
            Location(*args, **kwargs)

    @pytest.mark.parametrize(
        "args, kwargs",
        [
            (("", 1), {}),
            (("a.py", 0), {}),
            (("a.py", 1), {"variant": -1}),
            (("a.py", 1), {"segment": -1}),
        ],
        ids=["file-empty", "line-zero", "variant-negative", "segment-negative"],
    )
    def test_value_errors(self, args, kwargs):
        with pytest.raises(ValueError):
            Location(*args, **kwargs)

    def test_public_export(self):
        assert PublicLocation is Location


class TestContentCounters:
    def test_fields(self):
        counters = ContentCounters(2, 1, ((True, False),))
        assert counters.declensions == 2
        assert counters.segments == 1
        assert counters.filled == ((True, False),)

    def test_exported(self):
        assert PublicContentCounters is ContentCounters

    def test_frozen_and_hashable(self):
        counters = ContentCounters(1, 1, ((True,),))
        with pytest.raises(AttributeError):
            counters.segments = 2  # pyright: ignore[reportAttributeAccessIssue]
        assert hash(counters) == hash(ContentCounters(1, 1, ((True,),)))

    @pytest.mark.parametrize(
        "args",
        [
            (True, 1, ((True,),)),
            (1, "1", ((True,),)),
            (1, 1, [(True,)]),
            (1, 1, ([True],)),
            (1, 1, ((1,),)),
        ],
        ids=["declensions-bool", "segments-str", "mask-list", "row-list", "cell-int"],
    )
    def test_wrong_types(self, args):
        with pytest.raises(TypeError):
            _ = ContentCounters(*args)

    @pytest.mark.parametrize(
        "args",
        [
            (0, 1, ((),)),
            (1, 0, ()),
            (1, 2, ((True,),)),
            (2, 1, ((True,),)),
        ],
        ids=["no-declension", "no-segment", "rows", "cells"],
    )
    def test_inconsistent_values(self, args):
        with pytest.raises(ValueError):
            _ = ContentCounters(*args)


class TestCountContent:
    def test_padding_and_empty_texts_are_not_filled(self):
        counters = count_content([["Fichier", "Document"], ["Fichiers", ""]])
        assert counters == ContentCounters(
            declensions=2, segments=2, filled=((True, True), (True, False))
        )

    @pytest.mark.parametrize("matrix", [[], [[]]], ids=["no-row", "empty-row"])
    def test_empty_matrix(self, matrix):
        with pytest.raises(ValueError):
            _ = count_content(matrix)


class TestDescribeDifferences:
    def test_equal(self):
        counters = count_content([["a", "b"]])
        assert describe_differences(counters, counters) == []

    def test_lost_and_added_texts(self):
        recorded = count_content([["a", "b"], ["as", ""]])
        observed = count_content([["a", ""], ["as", "bs"]])
        assert describe_differences(recorded, observed) == [
            "text (1, 0) lost",
            "text (1, 1) added",
        ]

    def test_structure(self):
        recorded = count_content([["a", "b"], ["as", "bs"]])
        observed = count_content([["a"]])
        assert describe_differences(recorded, observed) == [
            "declensions: recorded 2, observed 1",
            "segments: recorded 2, observed 1",
            "text (1, 0) lost",
            "text (0, 1) lost",
            "text (1, 1) lost",
        ]


class TestEntryMapping:
    def test_to_entry(self):
        counters = count_content([["a", "b"], ["as", ""]])
        assert counters_to_entry(counters) == {
            "singular_count": 2,
            "segment_count": 2,
            "fill_mask": [[True, True], [True, False]],
        }

    def test_round_trip(self):
        counters = count_content([["a", ""], ["", "bs"], ["ass", "bss"]])
        assert counters_from_entry(counters_to_entry(counters)) == counters

    @pytest.mark.parametrize(
        "metadata",
        [
            {"singular_count": 1, "segment_count": 1},
            {"singular_count": True, "segment_count": 1, "fill_mask": [[True]]},
            {"singular_count": 1, "segment_count": "1", "fill_mask": [[True]]},
            {"singular_count": 1, "segment_count": 1, "fill_mask": [True]},
            {"singular_count": 1, "segment_count": 1, "fill_mask": [[1]]},
            {"singular_count": 2, "segment_count": 1, "fill_mask": [[True]]},
            {"singular_count": 1, "segment_count": 1, "fill_mask": "x"},
        ],
        ids=[
            "missing-mask",
            "bool-count",
            "str-count",
            "row-not-list",
            "cell-not-bool",
            "shape",
            "mask-not-list",
        ],
    )
    def test_from_entry_malformed(self, metadata):
        assert counters_from_entry(metadata) is None


class TestFinding:
    def test_language_defaults_to_none(self):
        assert Finding("error", "10001", "a defect").language is None

    def test_language_takes_part_in_equality(self):
        finding = Finding("error", "10001", "a defect", language="fr-FR")
        assert finding.language == "fr-FR"
        assert finding != Finding("error", "10001", "a defect")
        assert finding == Finding("error", "10001", "a defect", "fr-FR")
