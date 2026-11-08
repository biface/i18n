"""
Tests for the Declension and Location value types of models.message.
"""

import pytest

from i18n_tools import Declension as PublicDeclension
from i18n_tools import Location as PublicLocation
from i18n_tools.models import Declension, Location


class TestDeclension:
    def test_defaults(self):
        declension = Declension()
        assert declension.singular == ""
        assert declension.plurals == []
        assert declension.segments == [""]

    def test_segments_singular_first(self):
        declension = Declension("one file", ["two files", "{n} files"])
        assert declension.segments == ["one file", "two files", "{n} files"]

    def test_segments_is_a_copy(self):
        declension = Declension("one", ["two"])
        declension.segments.append("three")
        assert declension.plurals == ["two"]

    def test_default_plurals_not_shared(self):
        first, second = Declension(), Declension()
        first.plurals.append("x")
        assert second.plurals == []

    def test_equality_by_content(self):
        assert Declension("a", ["b"]) == Declension("a", ["b"])
        assert Declension("a", ["b"]) != Declension("a", ["c"])

    def test_from_segments(self):
        assert Declension.from_segments(["a", "b", "c"]) == Declension("a", ["b", "c"])
        assert Declension.from_segments(["a"]) == Declension("a", [])

    def test_from_segments_copies_input(self):
        segments = ["a", "b"]
        declension = Declension.from_segments(segments)
        segments.append("c")
        assert declension.plurals == ["b"]

    def test_from_segments_empty(self):
        with pytest.raises(ValueError):
            Declension.from_segments([])

    @pytest.mark.parametrize(
        "args",
        [(1, []), ("a", "b"), ("a", ["b", 2]), ("a", None)],
        ids=["singular-int", "plurals-str", "plural-int", "plurals-none"],
    )
    def test_type_errors(self, args):
        with pytest.raises(TypeError):
            Declension(*args)

    def test_from_segments_type_error(self):
        with pytest.raises(TypeError):
            Declension.from_segments("abc")  # pyright: ignore[reportArgumentType]

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
