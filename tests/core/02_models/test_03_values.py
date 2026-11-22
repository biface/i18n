"""
Tests for the value types: Declension (models.message), the record of a
message and ContentCounters (_counters), and Finding (_finding).
"""

import copy

import pytest
from ndict_tools import StrictNestedDictionary

from i18n_tools import ContentCounters as PublicContentCounters
from i18n_tools import Declension as PublicDeclension
from i18n_tools._counters import (
    check_format_string,
    observe,
    read_fields,
    record_defects,
    record_differences,
)
from i18n_tools._finding import Finding
from i18n_tools.models import ContentCounters, Declension


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


RECORD = {
    "count": {
        "declensions": 2,
        "alternatives": 1,
        "singulars": 2,
        "plurals": 2,
        "segments": {"principal": 2, "alternatives": [2]},
        "tokens": {
            "principal": [["name"], ["n"]],
            "alternatives": [[["name", "repository"], []]],
        },
    },
    "fill_mask": {"principal": [True, True], "alternatives": [[True, False]]},
}
CONTENT = (
    ["File {name} is missing.", "{n} files are missing."],
    [["File {name} is missing from {repository}.", ""]],
)


class TestContentCounters:
    def test_view_with_the_paths_of_the_file(self):
        counters = ContentCounters(RECORD)
        assert counters[["count", "segments", "principal"]] == 2
        assert (counters.declensions, counters.alternatives) == (2, 1)
        assert (counters.singulars, counters.plurals) == (2, 2)
        assert counters.segments.to_dict() == {"principal": 2, "alternatives": [2]}
        assert counters.tokens[["principal"]] == [["name"], ["n"]]
        assert counters.fill_mask.to_dict() == RECORD["fill_mask"]

    def test_holds_the_nodes_it_is_built_on(self):
        metadata = StrictNestedDictionary(copy.deepcopy(RECORD))
        counters = ContentCounters(
            {"count": metadata["count"], "fill_mask": metadata["fill_mask"]}
        )
        assert counters["count"] is metadata["count"]
        metadata[["count", "plurals"]] = 3
        assert counters.plurals == 3

    def test_equality_by_content_and_settings(self):
        setup = {"indent": 2}
        assert ContentCounters(RECORD, default_setup=setup) == ContentCounters(
            copy.deepcopy(RECORD), default_setup=setup
        )
        changed = copy.deepcopy(RECORD)
        changed["fill_mask"]["alternatives"][0][1] = True
        assert ContentCounters(RECORD) != ContentCounters(changed)

    def test_empty_record_for_copies(self):
        assert len(ContentCounters()) == 0

    @pytest.mark.parametrize(
        "record", [[1, 2], {"count": {}}, "record"], ids=["list", "no-mask", "str"]
    )
    def test_refused(self, record):
        with pytest.raises(
            TypeError, match="ContentCounters needs the count and fill_mask mappings"
        ):
            ContentCounters(record)

    def test_defects_and_differences(self):
        counters = ContentCounters(RECORD)
        assert counters.defects() == []
        lost = copy.deepcopy(RECORD)
        lost["fill_mask"]["principal"][1] = False
        assert counters.differences(ContentCounters(lost)) == ["text (0, 1) lost"]

    def test_exported(self):
        assert PublicContentCounters is ContentCounters


class TestObserve:
    def test_record_of_a_content(self):
        assert observe(*CONTENT) == RECORD

    def test_whitespace_is_not_filled_and_tokens_are_named_fields(self):
        record = observe(["{n:d} {n!r} {{lit}} {user.name}", " \n"], [])
        assert record["fill_mask"] == {"principal": [True, False], "alternatives": []}
        assert record["count"]["tokens"]["principal"] == [["n", "user.name"], []]

    @pytest.mark.parametrize(
        "text, names, positional",
        [
            ("{} and {0}", [], ["", "0"]),
            ("{b} {a} {b}", ["a", "b"], []),
            ("{0.attr} {items[0]}", ["items[0]"], ["0.attr"]),
        ],
        ids=["positional", "distinct-sorted", "attribute-index"],
    )
    def test_read_fields(self, text, names, positional):
        assert read_fields(text) == (names, positional)

    def test_check_format_string(self):
        assert check_format_string("Disk {percent} %") is None
        assert (
            check_format_string("Disk {") == "Single '{' encountered in format string"
        )


class TestRecordDefects:
    def test_well_formed(self):
        assert record_defects(RECORD) == []

    @pytest.mark.parametrize(
        "change, defect",
        [
            (
                lambda r: r["count"].update(singulars=3),
                '["metadata", "count", "singulars"] is 3, ["metadata", "count", '
                + '"declensions"] is 2, 1 + ["metadata", "count", "alternatives"] is 2',
            ),
            (
                lambda r: r["count"].update(alternatives=2),
                '["metadata", "count", "singulars"] is 2, ["metadata", "count", '
                + '"declensions"] is 2, 1 + ["metadata", "count", "alternatives"] is 3',
            ),
            (
                lambda r: r["count"]["segments"]["alternatives"].append(2),
                '["metadata", "count", "tokens"] does not have the shape given by '
                + '["metadata", "count", "segments"]',
            ),
            (
                lambda r: r["count"]["segments"].update(alternatives=[3]),
                '["metadata", "count", "tokens"] does not have the shape given by '
                + '["metadata", "count", "segments"]',
            ),
            (
                lambda r: r["count"].pop("tokens"),
                '["metadata", "count", "tokens"] is missing',
            ),
            (
                lambda r: r["count"].update(plurals=True),
                '["metadata", "count", "plurals"] is not an integer >= 0',
            ),
            (
                lambda r: r.pop("fill_mask"),
                '["metadata", "fill_mask"] is missing',
            ),
            (
                lambda r: r["fill_mask"].update(principal=[True, 1]),
                '["metadata", "fill_mask", "principal"] is not a list of booleans',
            ),
        ],
        ids=[
            "singulars",
            "alternatives",
            "segments-values",
            "rule-1",
            "tokens-missing",
            "bool-count",
            "no-mask",
            "mask-not-bool",
        ],
    )
    def test_defect(self, change, defect):
        record = copy.deepcopy(RECORD)
        change(record)
        assert defect in record_defects(record)

    def test_well_formed_record_against_rule_1(self):
        record = observe(["a", "b"], [["c", "d"]])
        record["count"]["segments"]["alternatives"] = [3]
        record["count"]["tokens"]["alternatives"] = [[[], [], []]]
        record["fill_mask"]["alternatives"] = [[True, True, False]]
        record["count"]["plurals"] = 3
        assert record_defects(record) == [
            '["metadata", "count", "segments", "alternatives", 0] is 3, '
            + '["metadata", "count", "segments", "principal"] is 2'
        ]


class TestRecordDifferences:
    def test_equal(self):
        assert record_differences(RECORD, observe(*CONTENT)) == []

    def test_lost_added_and_tokens(self):
        observed = observe(
            ["File {path} is missing.", ""],
            [["File {name} is missing from {repository}.", "{n} files"]],
        )
        assert record_differences(RECORD, observed) == [
            "text (0, 1) lost",
            "tokens of text (0, 0): recorded [name], observed [path]",
            "tokens of text (0, 1): recorded [n], observed []",
            "text (1, 1) added",
            "tokens of text (1, 1): recorded [], observed [n]",
        ]

    def test_declensions_first(self):
        assert record_differences(RECORD, observe(["a", "b"], [])) == [
            "declensions: recorded 2, observed 1"
        ]

    def test_segments_of_a_declension(self):
        observed = observe(["a", "b", "c"], [["d", "e", "f"]])
        assert record_differences(RECORD, observed)[:2] == [
            "segments of declension 0: recorded 2, observed 3",
            "segments of declension 1: recorded 2, observed 3",
        ]


class TestFinding:
    def test_language_defaults_to_none(self):
        assert Finding("error", "10001", "a defect").language is None

    def test_language_takes_part_in_equality(self):
        finding = Finding("error", "10001", "a defect", language="fr-FR")
        assert finding.language == "fr-FR"
        assert finding != Finding("error", "10001", "a defect")
        assert finding == Finding("error", "10001", "a defect", "fr-FR")
