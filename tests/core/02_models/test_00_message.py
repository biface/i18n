"""
Tests for the Message class of models.message, grouped by contract:
construction, reading, principal, variants, segments, reordering, tokens,
comparisons, completion status, lock, argument guards and metadata.

Fixtures (local conftest.py): ``fr_message`` (3 declensions x 3 segments),
``en_message``, ``draft_message`` (declensions of 3, 1 and 4 segments),
``single_message`` (principal singular only) and ``empty_message``.
"""

import copy
import re

import pytest
from ndict_tools import StrictNestedDictionary

from i18n_tools.exceptions import MessageError
from i18n_tools.models import ContentCounters, Declension, Message
from i18n_tools.models.message import extract_tokens

EMPTY_METADATA = {
    "id": "3000",
    "context": "",
    "locations": [],
    "flags": [],
    "user_comments": [],
    "auto_comments": [],
    "status": "draft",
    "rules": {},
}

DRAFT_MATRIX = [
    ["Une fleur", "Une {flower}", "Une {flower} rare"],
    ["Des fleurs", "", "Des {flower} rares"],
    ["Deux fleurs", "", "Deux {flower} rares"],
    ["", "", "Plusieurs {flower} rares"],
]

LOCATION = {"file": "app.py", "line": 12, "declension": None, "segment": None}


def _copy(message: Message) -> Message:
    """An equal draft message sharing no mutable metadata value with ``message``."""
    return Message(
        message.id,
        message.principal.singular,
        plurals=list(message.principal.plurals),
        alternatives=[list(variant.segments) for variant in message.variants],
        context=message.context,
        locations=copy.deepcopy(message.locations),
        flags=list(message.flags),
        user_comments=list(message.user_comments),
        auto_comments=list(message.auto_comments),
        rules=message.rules.to_dict(),
    )


class TestConstruction:
    def test_defaults(self):
        message = Message("3000")
        assert message.id == "3000"
        assert message.get_id() == "3000"
        assert message.principal == Declension()
        assert message.variants == ()
        assert message.context == ""
        assert message.plural_rule is None
        assert message.metadata.to_dict() == EMPTY_METADATA

    @pytest.mark.parametrize(
        "plurals, alternatives",
        [
            (["ps"], [["a"], ["b", "bs"]]),
            (("ps",), (("a",), ("b", "bs"))),
        ],
        ids=["lists", "tuples"],
    )
    def test_texts(self, plurals, alternatives):
        message = Message("3000", "p", plurals=plurals, alternatives=alternatives)
        assert message.principal == Declension("p", ("ps",))
        assert message.variants == (Declension("a"), Declension("b", ("bs",)))

    def test_alternatives_are_copied(self):
        alternatives = [["a"]]
        message = Message("3000", "p", alternatives=alternatives)
        alternatives.append(["b"])
        assert message.variants == (Declension("a"),)

    def test_metadata_options(self):
        message = Message(
            "3000",
            context="menu",
            locations=[LOCATION],
            flags=["python-format"],
            user_comments=["by hand"],
            auto_comments=["extracted"],
            rules={"thresholds": {"2": 1}},
        )
        assert message.metadata.to_dict() == {
            **EMPTY_METADATA,
            "context": "menu",
            "locations": [LOCATION],
            "flags": ["python-format"],
            "user_comments": ["by hand"],
            "auto_comments": ["extracted"],
            "rules": {"thresholds": {"2": 1}},
        }
        assert list(message.metadata) == list(EMPTY_METADATA)

    def test_int_identifier_converted(self):
        assert Message(3000).id == "3000"

    @pytest.mark.parametrize("key", ["status", "count", "fill_mask"])
    def test_guarded_keys_are_not_options(self, key):
        with pytest.raises(
            TypeError, match=f"'{key}' is not a Message option: it is set by"
        ):
            _ = Message("3000", **{key: "complete"})

    def test_unknown_options(self):
        with pytest.raises(
            TypeError, match="Unknown Message option\\(s\\): language, version"
        ):
            _ = Message("3000", version="0.10.0", language="fr")

    @pytest.mark.parametrize(
        "args, kwargs, expected",
        [
            ((True,), {}, "Message identifier must be a str or an int"),
            ((3.0,), {}, "Message identifier must be a str or an int"),
            (("3000", 1), {}, "Message singular must be a string"),
            (("3000",), {"plurals": "ps"}, "Message plurals must be a list or a tuple"),
            (("3000",), {"alternatives": "a"}, "Message alternatives must be"),
            (("3000",), {"context": None}, "Message context must be a str"),
            (("3000",), {"rules": []}, "Message rules must be a mapping"),
            (
                ("3000",),
                {"flags": "python-format"},
                "Message flags must be a list of str",
            ),
            (("3000",), {"user_comments": [1]}, "Message user_comments must be a list"),
            (("3000",), {"locations": [["a.py", 1]]}, "A location is a mapping"),
        ],
    )
    def test_wrong_types(self, args, kwargs, expected):
        with pytest.raises(TypeError, match=expected):
            _ = Message(*args, **kwargs)

    @pytest.mark.parametrize(
        "args, kwargs, expected",
        [
            (("",), {}, "Message identifier must not be empty"),
            (("3000",), {"flags": [""]}, "A flag must not be empty"),
            (("3000",), {"flags": ["a", "a"]}, "Flag\\(s\\) given more than once: a"),
            (
                ("3000",),
                {"locations": [{**LOCATION, "line": 0}]},
                "Location line must be >= 1",
            ),
            (
                ("3000",),
                {"alternatives": [[]]},
                "A declension has at least one segment",
            ),
            (
                ("3000", "Disk {"),
                {},
                re.escape(
                    "text (0, 0) is not a valid format string: Single '{' encountered"
                ),
            ),
            (
                ("3000", "p"),
                {"alternatives": [["a", "{n"]]},
                re.escape("text (1, 1) is not a valid format string"),
            ),
        ],
    )
    def test_refused_values(self, args, kwargs, expected):
        with pytest.raises(ValueError, match=expected):
            _ = Message(*args, **kwargs)


class TestFromMatrix:
    def test_columns_become_declensions(self):
        message = Message.from_matrix("2000", DRAFT_MATRIX)
        assert message.principal == Declension(
            "Une fleur", ("Des fleurs", "Deux fleurs", "")
        )
        assert message.variants == (
            Declension("Une {flower}", ("", "", "")),
            Declension(
                "Une {flower} rare",
                (
                    "Des {flower} rares",
                    "Deux {flower} rares",
                    "Plusieurs {flower} rares",
                ),
            ),
        )

    def test_round_trip_keeps_empty_cells(self):
        matrix = [["", "Doc"], ["Files", ""]]
        assert Message.from_matrix("2000", matrix).matrix == matrix

    def test_metadata_options(self):
        message = Message.from_matrix(
            "2000", [["Save"]], context="toolbar", flags=["python-format"]
        )
        assert message.context == "toolbar"
        assert message.flags == ["python-format"]

    def test_texts_come_from_the_matrix(self):
        with pytest.raises(TypeError, match="Unknown Message option\\(s\\): plurals"):
            _ = Message.from_matrix("2000", [["Save"]], plurals=["Saves"])

    @pytest.mark.parametrize(
        "matrix",
        [[], [[]], [["a", "b"], ["c"]]],
        ids=["no-row", "empty-row", "not-rectangular"],
    )
    def test_malformed_matrix(self, matrix):
        with pytest.raises(ValueError):
            _ = Message.from_matrix("2000", matrix)

    @pytest.mark.parametrize(
        "identifier, matrix",
        [
            (True, [["a"]]),
            ("2000", "a"),
            ("2000", [("a",)]),
            ("2000", [["a", 1]]),
        ],
        ids=["id", "matrix", "row", "cell"],
    )
    def test_wrong_types(self, identifier, matrix):
        with pytest.raises(TypeError):
            _ = Message.from_matrix(identifier, matrix)


class TestReading:
    def test_principal_and_variants_are_read_only(self, fr_message):
        with pytest.raises(AttributeError):
            fr_message.principal = Declension(
                "x"
            )  # pyright: ignore[reportAttributeAccessIssue]
        with pytest.raises(AttributeError):
            fr_message.variants = ()  # pyright: ignore[reportAttributeAccessIssue]

    def test_variants_is_a_tuple(self, fr_message):
        assert isinstance(fr_message.variants, tuple)
        assert len(fr_message.variants) == 2

    def test_get_variant(self, fr_message):
        assert fr_message.get_variant(2) == Declension(
            "Bonjour M. {name}", ("Bonjour Messieurs", "Messieurs")
        )

    @pytest.mark.parametrize("variant", [0, 3, -1])
    def test_get_variant_out_of_range(self, fr_message, variant):
        with pytest.raises(IndexError):
            _ = fr_message.get_variant(variant)

    @pytest.mark.parametrize("variant", ["1", True, 1.0])
    def test_get_variant_wrong_type(self, fr_message, variant):
        with pytest.raises(TypeError, match="variant must be an int"):
            _ = fr_message.get_variant(variant)

    @pytest.mark.parametrize(
        "segment, variant, expected",
        [
            (0, 0, "Une fleur"),
            (2, 0, "Deux fleurs"),
            (3, 0, ""),
            (0, 1, "Une {flower}"),
            (1, 1, ""),
            (3, 2, "Plusieurs {flower} rares"),
        ],
    )
    def test_get_segment(self, draft_message, segment, variant, expected):
        assert draft_message.get_segment(segment, variant) == expected

    @pytest.mark.parametrize("segment, variant", [(4, 0), (-1, 0), (0, 3), (0, -1)])
    def test_get_segment_out_of_range(self, draft_message, segment, variant):
        with pytest.raises(IndexError):
            _ = draft_message.get_segment(segment, variant)

    @pytest.mark.parametrize("segment, variant", [("0", 0), (0, None), (False, 0)])
    def test_get_segment_wrong_type(self, draft_message, segment, variant):
        with pytest.raises(TypeError):
            _ = draft_message.get_segment(segment, variant)

    def test_matrix_is_a_padded_rectangle(self, draft_message):
        assert draft_message.matrix == DRAFT_MATRIX

    def test_matrix_is_new_on_each_access(self, fr_message):
        matrix = fr_message.matrix
        matrix[0][0] = "changed"
        assert fr_message.matrix[0][0] == "Bonjour"

    @pytest.mark.parametrize(
        "fixture_name, has_variants, has_plurals",
        [
            ("fr_message", True, True),
            ("draft_message", True, True),
            ("single_message", False, False),
            ("empty_message", False, False),
        ],
    )
    def test_has_variants_has_plurals(
        self, fixture_name, has_variants, has_plurals, request
    ):
        message = request.getfixturevalue(fixture_name)
        assert message.has_variants is has_variants
        assert message.has_plurals is has_plurals

    def test_structure_counts_even_when_empty(self):
        message = Message("3000", "", plurals=[""], alternatives=[[""]])
        assert message.has_variants
        assert message.has_plurals


class TestPrincipal:
    def test_add_principal_when_absent(self, empty_message):
        empty_message.add_principal(singular="Hello", plurals=["Hellos"])
        assert empty_message.principal == Declension("Hello", ("Hellos",))

    def test_add_principal_keeps_existing_segments(self, fr_message):
        fr_message.remove_principal()
        fr_message.add_principal(singular="Salut")
        assert fr_message.principal == Declension("Salut", ("", ""))

    def test_add_principal_when_present(self, fr_message):
        with pytest.raises(ValueError, match="already has a principal"):
            fr_message.add_principal(singular="Salut")

    @pytest.mark.parametrize("fields", [{}, {"singular": ""}, {"plurals": ["a"]}])
    def test_add_principal_needs_a_singular(self, empty_message, fields):
        with pytest.raises(ValueError, match="non-empty singular"):
            empty_message.add_principal(**fields)
        assert empty_message.principal == Declension()

    @pytest.mark.parametrize(
        "fields",
        [
            {"singular": "a", "plural": ["b"]},
            {"singular": 1},
            {"singular": "a", "plurals": "b"},
            {"singular": "a", "plurals": [1]},
        ],
        ids=["unknown-key", "singular-type", "plurals-type", "plural-type"],
    )
    def test_add_principal_wrong_fields(self, empty_message, fields):
        with pytest.raises(TypeError):
            empty_message.add_principal(**fields)

    @pytest.mark.parametrize(
        "fields, expected",
        [
            (
                {"singular": "Salut"},
                Declension("Salut", ("Bonjour à tous", "Bonjour tout le monde")),
            ),
            ({"plurals": ("Salut à tous",)}, Declension("Bonjour", ("Salut à tous",))),
            ({"singular": "Salut", "plurals": []}, Declension("Salut")),
        ],
    )
    def test_update_principal(self, fr_message, fields, expected):
        fr_message.update_principal(**fields)
        assert fr_message.principal == expected

    def test_update_principal_empty_singular(self, fr_message):
        with pytest.raises(ValueError, match="cannot be empty"):
            fr_message.update_principal(singular="")

    def test_update_principal_without_fields(self, fr_message):
        with pytest.raises(ValueError, match="No field given"):
            fr_message.update_principal()

    def test_update_absent_principal_plurals(self, empty_message):
        empty_message.update_principal(plurals=["Files"])
        assert empty_message.principal == Declension("", ("Files",))

    def test_remove_principal_keeps_segment_count(self, fr_message):
        fr_message.remove_principal()
        assert fr_message.principal == Declension("", ("", ""))
        assert len(fr_message.variants) == 2


class TestVariants:
    def test_add_variant_appends_and_returns_index(self, fr_message):
        index = fr_message.add_variant(singular="Salut {name}", plurals=["Salut"])
        assert index == 3
        assert fr_message.get_variant(3) == Declension("Salut {name}", ("Salut",))

    def test_add_variant_never_overwrites(self):
        """Regression: add_variant() replaced variant 1 when the singular was empty."""
        message = Message("y", alternatives=[["Doc"]])
        assert message.add_variant(singular="Pièce") == 2
        assert message.variants == (Declension("Doc"), Declension("Pièce"))

    def test_add_variant_is_not_padded(self, fr_message):
        _ = fr_message.add_variant(singular="Salut")
        assert fr_message.get_variant(3) == Declension("Salut")
        assert fr_message.matrix[1][3] == ""

    @pytest.mark.parametrize("fields", [{}, {"singular": ""}])
    def test_add_variant_needs_a_singular(self, fr_message, fields):
        with pytest.raises(ValueError, match="non-empty singular"):
            _ = fr_message.add_variant(**fields)
        assert len(fr_message.variants) == 2

    def test_update_variant(self, fr_message):
        fr_message.update_variant(1, singular="Bonjour Madame {name}")
        assert fr_message.get_variant(1) == Declension(
            "Bonjour Madame {name}", ("Bonjour Mesdames", "Mesdames")
        )

    def test_update_variant_zero(self, fr_message):
        """Regression: update_variant(0, ...) was a silent no-op."""
        with pytest.raises(IndexError, match="Variant 0 is the principal"):
            fr_message.update_variant(0, singular="Salut")
        assert fr_message.principal.singular == "Bonjour"

    @pytest.mark.parametrize("variant", [3, -1])
    def test_update_variant_out_of_range(self, fr_message, variant):
        with pytest.raises(IndexError):
            fr_message.update_variant(variant, singular="Salut")

    def test_update_variant_empty_singular(self, fr_message):
        with pytest.raises(ValueError, match="cannot be empty"):
            fr_message.update_variant(1, singular="")

    def test_remove_variant_shifts_the_next_ones(self, fr_message):
        second = fr_message.get_variant(2)
        fr_message.remove_variant(1)
        assert fr_message.variants == (second,)

    @pytest.mark.parametrize("variant", [0, 3])
    def test_remove_variant_out_of_range(self, fr_message, variant):
        with pytest.raises(IndexError):
            fr_message.remove_variant(variant)


class TestSegments:
    def test_add_segment_inserts_a_row(self, draft_message):
        draft_message.add_segment("Trois {flower} rares", 3, 2)
        assert draft_message.matrix == [
            ["Une fleur", "Une {flower}", "Une {flower} rare"],
            ["Des fleurs", "", "Des {flower} rares"],
            ["Deux fleurs", "", "Deux {flower} rares"],
            ["", "", "Trois {flower} rares"],
            ["", "", "Plusieurs {flower} rares"],
        ]
        assert draft_message.principal == Declension(
            "Une fleur", ("Des fleurs", "Deux fleurs", "")
        )
        assert draft_message.get_variant(1) == Declension("Une {flower}")

    def test_add_segment_pads_a_short_target(self, draft_message):
        draft_message.add_segment("Deux {flower}", 2, 1)
        assert draft_message.get_variant(1) == Declension(
            "Une {flower}", ("", "Deux {flower}")
        )
        assert [row[1] for row in draft_message.matrix] == [
            "Une {flower}",
            "",
            "Deux {flower}",
            "",
            "",
        ]

    def test_add_segment_after_the_last_row(self, single_message):
        single_message.add_segment("Bonjour à tous", 1)
        assert single_message.principal == Declension(
            "Bonjour {name}", ("Bonjour à tous",)
        )

    def test_add_segment_zero(self, draft_message):
        with pytest.raises(ValueError, match="Segment 0 is the singular"):
            draft_message.add_segment("x", 0)

    @pytest.mark.parametrize("segment, variant", [(5, 0), (-1, 0), (1, 3)])
    def test_add_segment_out_of_range(self, draft_message, segment, variant):
        with pytest.raises(IndexError):
            draft_message.add_segment("x", segment, variant)

    def test_add_segment_wrong_text(self, draft_message):
        with pytest.raises(TypeError, match="Segment text must be a string"):
            draft_message.add_segment(None, 1)  # pyright: ignore[reportArgumentType]

    @pytest.mark.parametrize(
        "text, segment, variant",
        [
            ("Trois fleurs", 3, 0),
            ("Des {flower}", 1, 1),
            ("", 0, 1),
            ("", 2, 0),
        ],
    )
    def test_update_segment(self, draft_message, text, segment, variant):
        rows = len(draft_message.matrix)
        draft_message.update_segment(text, segment, variant)
        assert draft_message.get_segment(segment, variant) == text
        assert len(draft_message.matrix) == rows

    def test_update_segment_extends_a_short_declension(self, draft_message):
        draft_message.update_segment("Deux {flower}", 2, 1)
        assert draft_message.get_variant(1) == Declension(
            "Une {flower}", ("", "Deux {flower}")
        )

    def test_update_segment_principal_singular_empty(self, draft_message):
        with pytest.raises(ValueError, match="cannot be emptied"):
            draft_message.update_segment("", 0, 0)

    @pytest.mark.parametrize("segment, variant", [(4, 0), (0, 3)])
    def test_update_segment_out_of_range(self, draft_message, segment, variant):
        with pytest.raises(IndexError):
            draft_message.update_segment("x", segment, variant)

    def test_remove_segment(self, draft_message):
        draft_message.remove_segment(1)
        assert draft_message.matrix == [
            ["Une fleur", "Une {flower}", "Une {flower} rare"],
            ["Deux fleurs", "", "Deux {flower} rares"],
            ["", "", "Plusieurs {flower} rares"],
        ]
        assert draft_message.get_variant(1) == Declension("Une {flower}")

    def test_remove_segment_zero(self, draft_message):
        with pytest.raises(ValueError, match="cannot be removed"):
            draft_message.remove_segment(0)

    @pytest.mark.parametrize("segment", [4, -1])
    def test_remove_segment_out_of_range(self, draft_message, segment):
        with pytest.raises(IndexError):
            draft_message.remove_segment(segment)


class TestReordering:
    def test_switch_principal_and_variant(self, fr_message):
        principal, first, second = fr_message.principal, *fr_message.variants
        fr_message.switch(0, 2)
        assert fr_message.principal == second
        assert fr_message.variants == (first, principal)

    def test_switch_variants(self, fr_message):
        principal, first, second = fr_message.principal, *fr_message.variants
        fr_message.switch(2, 1)
        assert fr_message.principal == principal
        assert fr_message.variants == (second, first)

    @pytest.mark.parametrize("source, destination", [(1, 1), (0, 3), (-1, 0)])
    def test_switch_wrong_indices(self, fr_message, source, destination):
        with pytest.raises(IndexError):
            fr_message.switch(source, destination)

    @pytest.mark.parametrize("direction", ["natural", "reverse"])
    def test_toggle(self, fr_message, direction):
        principal, first, second = fr_message.principal, *fr_message.variants
        fr_message.toggle(direction)
        if direction == "natural":
            assert fr_message.principal == second
            assert fr_message.variants == (principal, first)
        else:
            assert fr_message.principal == first
            assert fr_message.variants == (second, principal)

    def test_toggle_default_is_natural(self, fr_message):
        second = fr_message.get_variant(2)
        fr_message.toggle()
        assert fr_message.principal == second

    def test_toggle_without_variants(self, single_message):
        single_message.toggle()
        assert single_message.principal == Declension("Bonjour {name}")

    def test_toggle_wrong_direction(self, fr_message):
        with pytest.raises(ValueError, match="direction must be"):
            fr_message.toggle("forward")  # pyright: ignore[reportArgumentType]


class TestTokens:
    @pytest.mark.parametrize(
        "variant, segment, tokens, expected",
        [
            (0, 0, {}, "Bonjour"),
            (1, 0, {"name": "Curie"}, "Bonjour Mme Curie"),
            (2, 1, {"name": "unused"}, "Bonjour Messieurs"),
        ],
    )
    def test_format(self, fr_message, variant, segment, tokens, expected):
        assert fr_message.format(variant, segment, **tokens) == expected

    def test_format_reads_the_exact_cell(self, draft_message):
        """No fallback: an absent text formats to an empty string."""
        assert draft_message.format(1, 1) == ""
        assert draft_message.format(0, 3) == ""

    def test_format_missing_token(self, single_message):
        with pytest.raises(
            KeyError, match=re.escape("Missing token 'name' for message '2001'")
        ):
            _ = single_message.format()

    def test_format_malformed_text(self):
        # The model refuses such a text; format() still guards against one
        # stored by other means.
        message = Message("3000")
        message._principal = Declension("Hello {name")
        with pytest.raises(ValueError, match="Error formatting message '3000'"):
            _ = message.format(name="Ana")

    def test_format_out_of_range(self, draft_message):
        with pytest.raises(IndexError):
            _ = draft_message.format(3, 0)

    @pytest.mark.parametrize(
        "variant, expected",
        [
            (0, [[], [], []]),
            (1, [["flower"]]),
            (2, [["flower"], ["flower"], ["flower"], ["flower"]]),
        ],
    )
    def test_get_tokens(self, draft_message, variant, expected):
        assert draft_message.get_tokens(variant) == expected

    def test_get_tokens_out_of_range(self, draft_message):
        with pytest.raises(IndexError):
            _ = draft_message.get_tokens(3)

    @pytest.mark.parametrize(
        "text, expected",
        [
            ("Hello", []),
            ("Hello {name}", ["name"]),
            ("{count} files in {folder}, {count}", ["count", "folder", "count"]),
        ],
    )
    def test_extract_tokens(self, text, expected):
        assert extract_tokens(text) == expected


class TestComparisons:
    def test_equal_same_content(self, fr_message):
        other = _copy(fr_message)
        assert other == fr_message
        assert other.equal(fr_message)

    @pytest.mark.parametrize(
        "change",
        [
            lambda m: setattr(m, "id", "other"),
            lambda m: setattr(m, "context", "other"),
            lambda m: m.add_comment("user", "other"),
            lambda m: m.update_principal(singular="other"),
            lambda m: m.add_variant(singular="other"),
        ],
        ids=["id", "context", "metadata", "principal", "variants"],
    )
    def test_not_equal(self, fr_message, change):
        other = _copy(fr_message)
        change(other)
        assert other != fr_message
        assert not other.equal(fr_message)

    def test_padding_is_not_strictly_equal(self, draft_message):
        """A padded cell and a stored empty text give the same matrix only."""
        reloaded = Message.from_matrix("2000", draft_message.matrix, context="garden")
        assert reloaded != draft_message
        assert reloaded.isomorph(draft_message)

    def test_not_a_message(self, fr_message):
        assert fr_message != "1000"
        assert not fr_message.equal("1000")
        assert not fr_message.isomorph("1000")
        assert not fr_message.similar("1000")

    def test_isomorph_ignores_id_context_metadata(self, fr_message):
        other = Message.from_matrix("other", fr_message.matrix, context="x")
        assert other.isomorph(fr_message)
        assert other != fr_message

    def test_isomorph_compares_positions(self, fr_message):
        other = Message.from_matrix(fr_message.id, fr_message.matrix)
        other.switch(1, 2)
        assert not other.isomorph(fr_message)
        assert other.similar(fr_message)

    def test_similar_compares_texts(self, fr_message, en_message):
        assert not fr_message.similar(en_message)

    def test_texts(self, draft_message):
        assert draft_message.texts == frozenset(
            text for row in DRAFT_MATRIX for text in row if text
        )
        assert Message("3000").texts == frozenset()

    def test_unhashable(self, fr_message):
        with pytest.raises(TypeError, match="unhashable"):
            _ = hash(fr_message)

    def test_str_and_repr(self, single_message):
        assert str(single_message) == "Bonjour {name}"
        assert repr(single_message) == (
            "Message(id='2001', principal=Declension(singular='Bonjour {name}', "
            + "plurals=()), variants=[])"
        )


FR_RECORD = {
    "count": {
        "declensions": 3,
        "alternatives": 2,
        "singulars": 3,
        "plurals": 6,
        "segments": {"principal": 3, "alternatives": [3, 3]},
        "tokens": {
            "principal": [[], [], []],
            "alternatives": [[["name"], [], []], [["name"], [], []]],
        },
    },
    "fill_mask": {
        "principal": [True, True, True],
        "alternatives": [[True, True, True], [True, True, True]],
    },
}

LOCKED_CALLS = {
    "add_principal": lambda m: m.add_principal(singular="x"),
    "update_principal": lambda m: m.update_principal(singular="x"),
    "remove_principal": lambda m: m.remove_principal(),
    "add_variant": lambda m: m.add_variant(singular="x"),
    "update_variant": lambda m: m.update_variant(1, singular="x"),
    "remove_variant": lambda m: m.remove_variant(1),
    "add_segment": lambda m: m.add_segment("x", 1),
    "update_segment": lambda m: m.update_segment("x", 1),
    "remove_segment": lambda m: m.remove_segment(1),
    "switch": lambda m: m.switch(0, 1),
    "toggle": lambda m: m.toggle(),
}


class TestStatus:
    def test_new_message_is_a_draft(self, fr_message):
        assert fr_message.status == "draft"
        assert fr_message.metadata["status"] == "draft"
        assert fr_message.recorded is None
        assert not fr_message.has_divergence

    def test_observed(self, fr_message, draft_message):
        assert fr_message.observed.to_dict() == FR_RECORD
        assert fr_message.observed.default_setup == fr_message.metadata.default_setup
        assert draft_message.observed.fill_mask.to_dict() == {
            "principal": [True, True, True, False],
            "alternatives": [[True, False, False, False], [True, True, True, True]],
        }

    def test_mark_complete_records_the_content(self, fr_message):
        fr_message.mark_complete()
        assert fr_message.status == "complete"
        assert fr_message.metadata["status"] == "complete"
        assert fr_message.recorded.to_dict() == FR_RECORD
        assert fr_message.metadata["count"].to_dict() == FR_RECORD["count"]
        assert fr_message.metadata["fill_mask"].to_dict() == FR_RECORD["fill_mask"]
        assert not fr_message.has_divergence

    def test_recorded_is_a_view_on_the_metadata(self, fr_message):
        fr_message.mark_complete()
        recorded = fr_message.recorded
        assert recorded["count"] is fr_message.metadata["count"]
        assert recorded["fill_mask"] is fr_message.metadata["fill_mask"]

    def test_mark_complete_empty_principal(self, fr_message):
        fr_message.remove_principal()
        with pytest.raises(MessageError, match="principal singular is empty"):
            fr_message.mark_complete()
        assert fr_message.status == "draft"
        assert fr_message.recorded is None

    def test_mark_complete_breaks_rule_1(self, draft_message):
        with pytest.raises(MessageError, match=re.escape("segment counts [1, 3, 4]")):
            draft_message.mark_complete()
        assert draft_message.status == "draft"
        assert draft_message.recorded is None

    def test_mark_complete_twice(self, fr_message):
        fr_message.mark_complete()
        with pytest.raises(MessageError, match="already complete"):
            fr_message.mark_complete()

    def test_record_a_draft(self, draft_message):
        draft_message.record()
        assert draft_message.recorded == draft_message.observed
        assert draft_message.status == "draft"
        draft_message.update_segment("Trois fleurs", 3, 0)
        assert draft_message.has_divergence
        assert draft_message.recorded.differences(draft_message.observed) == [
            "text (0, 3) added"
        ]

    def test_record_a_complete_message(self, fr_message):
        fr_message.mark_complete()
        fr_message.reopen()
        fr_message.update_segment("", 2, 1)
        fr_message.mark_complete()
        recorded = fr_message.recorded.to_dict()
        with pytest.raises(MessageError, match="recorded by mark_complete"):
            fr_message.record()
        assert fr_message.recorded.to_dict() == recorded

    def test_reopen_keeps_the_record(self, fr_message):
        fr_message.mark_complete()
        fr_message.reopen()
        assert fr_message.status == "draft"
        assert fr_message.recorded.to_dict() == FR_RECORD

    def test_reopen_a_draft(self, fr_message):
        with pytest.raises(MessageError, match="already a draft"):
            fr_message.reopen()

    def test_reopened_draft_diverges_after_a_change(self, fr_message):
        fr_message.mark_complete()
        fr_message.reopen()
        fr_message.update_segment("", 2, 1)
        assert fr_message.has_divergence

    def test_token_change_diverges(self, fr_message):
        fr_message.mark_complete()
        fr_message.reopen()
        fr_message.update_segment("Bonjour Mme {title}", 0, 1)
        assert fr_message.recorded.differences(fr_message.observed) == [
            "tokens of text (1, 0): recorded [name], observed [title]"
        ]

    def test_accepting_a_change(self, fr_message):
        """reopen() then mark_complete() records the current content."""
        fr_message.mark_complete()
        fr_message.reopen()
        fr_message.update_segment("", 2, 1)
        fr_message.mark_complete()
        assert not fr_message.has_divergence
        assert fr_message.recorded[["fill_mask", "alternatives"]] == [
            [True, True, False],
            [True, True, True],
        ]

    def test_complete_without_record_diverges(self, fr_message):
        """A message read from a file as complete, without its record."""
        fr_message.metadata["status"] = "complete"
        assert fr_message.recorded is None
        assert fr_message.has_divergence

    def test_draft_without_record_does_not_diverge(self):
        assert not Message("3000", "a").has_divergence

    def test_status_and_recorded_are_read_only(self, fr_message):
        with pytest.raises(AttributeError):
            fr_message.status = (
                "complete"  # pyright: ignore[reportAttributeAccessIssue]
            )
        with pytest.raises(AttributeError):
            fr_message.recorded = None  # pyright: ignore[reportAttributeAccessIssue]

    def test_strict_equality_includes_status_and_record(self, fr_message):
        other = _copy(fr_message)
        fr_message.mark_complete()
        assert other != fr_message
        assert other.isomorph(fr_message)
        other.mark_complete()
        assert other == fr_message


class TestLock:
    @pytest.mark.parametrize("call", LOCKED_CALLS.values(), ids=LOCKED_CALLS.keys())
    def test_complete_refuses_changes(self, fr_message, call):
        fr_message.mark_complete()
        before = fr_message.matrix
        with pytest.raises(MessageError, match="is complete: reopen"):
            call(fr_message)
        assert fr_message.matrix == before
        assert not fr_message.has_divergence

    @pytest.mark.parametrize("call", LOCKED_CALLS.values(), ids=LOCKED_CALLS.keys())
    def test_reopened_draft_accepts_changes(self, fr_message, call):
        fr_message.mark_complete()
        fr_message.reopen()
        if call is LOCKED_CALLS["add_principal"]:
            fr_message.remove_principal()
        before = fr_message.matrix
        call(fr_message)
        assert fr_message.matrix != before

    def test_complete_keeps_metadata_editable(self, fr_message):
        fr_message.mark_complete()
        fr_message.context = "toolbar"
        fr_message.add_location("app.py", 12, variant=1)
        fr_message.add_comment("user", "checked")
        fr_message.update_metadata(flags=["fuzzy"])
        fr_message.add_flag("python-format")
        fr_message.rules = {"thresholds": {}}
        assert fr_message.metadata["flags"] == ["fuzzy", "python-format"]
        assert not fr_message.has_divergence


NOT_INTS = ["1", 1.0, True]

INDEXED_CALLS = {
    "get_variant": lambda m, bad: m.get_variant(bad),
    "get_segment-segment": lambda m, bad: m.get_segment(bad, 0),
    "get_segment-variant": lambda m, bad: m.get_segment(0, bad),
    "update_variant": lambda m, bad: m.update_variant(bad, singular="x"),
    "remove_variant": lambda m, bad: m.remove_variant(bad),
    "add_segment-segment": lambda m, bad: m.add_segment("x", bad),
    "add_segment-variant": lambda m, bad: m.add_segment("x", 1, bad),
    "update_segment-segment": lambda m, bad: m.update_segment("x", bad),
    "update_segment-variant": lambda m, bad: m.update_segment("x", 0, bad),
    "remove_segment": lambda m, bad: m.remove_segment(bad),
    "switch-source": lambda m, bad: m.switch(bad, 0),
    "switch-destination": lambda m, bad: m.switch(0, bad),
    "format-variant": lambda m, bad: m.format(bad),
    "format-segment": lambda m, bad: m.format(0, bad),
    "get_tokens": lambda m, bad: m.get_tokens(bad),
}

FIELD_CALLS = {
    "update_principal": lambda m, fields: m.update_principal(**fields),
    "add_variant": lambda m, fields: m.add_variant(**fields),
    "update_variant": lambda m, fields: m.update_variant(1, **fields),
}

WRONG_FIELDS = {
    "unknown-key": {"singular": "a", "plural": ["b"]},
    "singular-type": {"singular": 1},
    "plurals-type": {"singular": "a", "plurals": "b"},
    "plural-type": {"singular": "a", "plurals": [1]},
}


class TestArgumentGuards:
    """Every public entry point refuses arguments of the wrong type."""

    @pytest.mark.parametrize("bad", NOT_INTS, ids=["str", "float", "bool"])
    @pytest.mark.parametrize("call", INDEXED_CALLS.values(), ids=INDEXED_CALLS.keys())
    def test_index_is_an_int(self, fr_message, call, bad):
        before = fr_message.matrix
        with pytest.raises(TypeError, match="must be an int"):
            call(fr_message, bad)
        assert fr_message.matrix == before

    @pytest.mark.parametrize("fields", WRONG_FIELDS.values(), ids=WRONG_FIELDS.keys())
    @pytest.mark.parametrize("call", FIELD_CALLS.values(), ids=FIELD_CALLS.keys())
    def test_declension_fields(self, fr_message, call, fields):
        before = fr_message.matrix
        with pytest.raises(TypeError):
            call(fr_message, fields)
        assert fr_message.matrix == before

    def test_update_variant_without_fields(self, fr_message):
        with pytest.raises(ValueError, match="No field given"):
            fr_message.update_variant(1)

    def test_update_segment_text_is_a_string(self, fr_message):
        with pytest.raises(TypeError, match="Segment text must be a string"):
            fr_message.update_segment(None, 1)  # pyright: ignore[reportArgumentType]

    def test_toggle_direction_is_a_string(self, fr_message):
        with pytest.raises(ValueError, match="direction must be"):
            fr_message.toggle(1)  # pyright: ignore[reportArgumentType]


class TestFormatStrings:
    """A text that str.format cannot read is refused by every text mutator."""

    CALLS = {
        "add_principal": lambda m: (
            m.remove_principal(),
            m.add_principal(singular="{"),
        ),
        "update_principal": lambda m: m.update_principal(plurals=["a", "{n"]),
        "add_variant": lambda m: m.add_variant(singular="x {"),
        "update_variant": lambda m: m.update_variant(1, singular="}"),
        "add_segment": lambda m: m.add_segment("{0", 1, 2),
        "update_segment": lambda m: m.update_segment("{", 2, 1),
    }

    @pytest.mark.parametrize("call", CALLS.values(), ids=CALLS.keys())
    def test_refused(self, fr_message, call):
        before = fr_message.matrix
        with pytest.raises(
            ValueError, match=r"text \(\d, \d\) is not a valid format string"
        ):
            call(fr_message)
        if call is not self.CALLS["add_principal"]:
            assert fr_message.matrix == before

    def test_doubled_braces_and_positional_fields_accepted(self, fr_message):
        fr_message.update_segment("{{literal}} {} {0}", 2, 1)
        assert fr_message.get_segment(2, 1) == "{{literal}} {} {0}"


class TestLocations:
    def test_none_by_default(self, fr_message):
        assert fr_message.locations == []

    def test_add_location(self, fr_message):
        fr_message.add_location("app.py", 12)
        fr_message.add_location("cli.py", 40, variant=1, segment=0)
        fr_message.add_location("cli.py", 41, segment=1)
        assert fr_message.locations == [
            {"file": "app.py", "line": 12, "declension": None, "segment": None},
            {"file": "cli.py", "line": 40, "declension": 1, "segment": 0},
            {"file": "cli.py", "line": 41, "declension": None, "segment": 1},
        ]
        assert fr_message.locations is fr_message.metadata["locations"]

    def test_duplicate_is_ignored(self, fr_message):
        fr_message.add_location("app.py", 12, variant=1)
        fr_message.add_location("app.py", 12, variant=1)
        fr_message.add_location("app.py", 12)
        assert [item["declension"] for item in fr_message.locations] == [1, None]

    def test_coordinates_are_not_checked_against_the_content(self, single_message):
        """Source code may refer to a text not written yet."""
        single_message.add_location("app.py", 3, variant=4, segment=2)
        assert single_message.locations == [
            {"file": "app.py", "line": 3, "declension": 4, "segment": 2}
        ]

    def test_setter_checks_every_location(self, fr_message):
        fr_message.locations = [LOCATION]
        assert fr_message.locations == [LOCATION]
        with pytest.raises(ValueError, match="Location file must not be empty"):
            fr_message.locations = [LOCATION, {**LOCATION, "file": ""}]
        assert fr_message.locations == [LOCATION]

    def test_remove_location(self, fr_message):
        fr_message.add_location("app.py", 12)
        fr_message.add_location("cli.py", 40)
        fr_message.remove_location(0)
        assert [item["file"] for item in fr_message.locations] == ["cli.py"]
        with pytest.raises(
            IndexError, match=re.escape("Location 1 is out of range 0..0")
        ):
            fr_message.remove_location(1)
        with pytest.raises(TypeError, match="index must be an int"):
            fr_message.remove_location("0")  # pyright: ignore[reportArgumentType]

    def test_editable_on_a_complete_message(self, fr_message):
        fr_message.mark_complete()
        fr_message.add_location("app.py", 12)
        assert len(fr_message.locations) == 1
        assert not fr_message.has_divergence

    @pytest.mark.parametrize(
        "args, error",
        [
            ((12, "app.py"), TypeError),
            (("app.py", "12"), TypeError),
            (("app.py", True), TypeError),
            (("app.py", 12, "1"), TypeError),
            (("app.py", 12, None, 1.0), TypeError),
            (("", 12), ValueError),
            (("app.py", 0), ValueError),
            (("app.py", 12, -1), ValueError),
            (("app.py", 12, None, -1), ValueError),
        ],
        ids=[
            "old-argument-order",
            "line-str",
            "line-bool",
            "variant-str",
            "segment-float",
            "empty-file",
            "line-zero",
            "variant-negative",
            "segment-negative",
        ],
    )
    def test_wrong_arguments(self, fr_message, args, error):
        with pytest.raises(error):
            fr_message.add_location(*args)
        assert fr_message.locations == []


class TestMetadata:
    def test_keys_of_the_entry(self, fr_message):
        assert fr_message.get_metadata().to_dict() == {
            **EMPTY_METADATA,
            "id": "1000",
            "flags": ["python-format"],
            "user_comments": ["In French, Greeting message to one or more..."],
            "auto_comments": ["1000_000", "1000_001", "1000_02"],
        }

    @pytest.mark.parametrize(
        "path, expected",
        [("id", "1000"), ("status", "draft"), (["flags"], ["python-format"])],
    )
    def test_get_metadata_key(self, fr_message, path, expected):
        assert fr_message.get_metadata(path) == expected

    @pytest.mark.parametrize("path", ["count", ["count", "singulars"], "language"])
    def test_get_metadata_unknown(self, fr_message, path):
        with pytest.raises(KeyError, match="is not a key or path"):
            _ = fr_message.get_metadata(path)

    def test_language_and_version_are_not_message_keys(self, fr_message):
        assert "language" not in fr_message.metadata
        assert "version" not in fr_message.metadata
        assert not hasattr(fr_message, "add_language")

    def test_properties_read_the_keys(self, fr_message):
        fr_message.context = "toolbar"
        fr_message.rules = {"thresholds": {"2": 1}}
        assert fr_message.metadata["context"] == "toolbar"
        assert fr_message.metadata[["rules", "thresholds", "2"]] == 1
        assert fr_message.rules is fr_message.metadata["rules"]
        assert fr_message.flags is fr_message.metadata["flags"]
        assert fr_message.user_comments is fr_message.metadata["user_comments"]
        assert fr_message.auto_comments is fr_message.metadata["auto_comments"]

    def test_id_setter(self, fr_message):
        fr_message.id = 42
        assert fr_message.metadata["id"] == "42"
        with pytest.raises(
            TypeError, match="Message identifier must be a str or an int"
        ):
            fr_message.id = False
        with pytest.raises(ValueError, match="Message identifier must not be empty"):
            fr_message.id = ""
        assert fr_message.id == "42"

    @pytest.mark.parametrize(
        "name, value, error, expected",
        [
            ("context", 1, TypeError, "Message context must be a str"),
            ("rules", [], TypeError, "Message rules must be a mapping"),
            ("flags", ["a", "a"], ValueError, "given more than once: a"),
            (
                "user_comments",
                "text",
                TypeError,
                "Message user_comments must be a list",
            ),
            (
                "auto_comments",
                [None],
                TypeError,
                "Message auto_comments must be a list",
            ),
        ],
    )
    def test_setters_refuse(self, fr_message, name, value, error, expected):
        before = fr_message.metadata.to_dict()
        with pytest.raises(error, match=expected):
            setattr(fr_message, name, value)
        assert fr_message.metadata.to_dict() == before

    def test_flags(self, fr_message):
        fr_message.add_flag("fuzzy")
        fr_message.add_flag("fuzzy")
        assert fr_message.flags == ["python-format", "fuzzy"]
        fr_message.remove_flag("python-format")
        assert fr_message.flags == ["fuzzy"]
        with pytest.raises(ValueError, match="Message '1000' has no flag 'c-format'"):
            fr_message.remove_flag("c-format")
        with pytest.raises(ValueError, match="A flag must not be empty"):
            fr_message.add_flag("")
        assert fr_message.flags == ["fuzzy"]

    @pytest.mark.parametrize("mode", ["user", "auto"])
    def test_comments(self, empty_message, mode):
        empty_message.add_comment(mode, "first")
        empty_message.add_comment(mode, "second")
        assert empty_message.metadata[mode + "_comments"] == ["first", "second"]
        empty_message.remove_comment(mode, "first")
        assert empty_message.metadata[mode + "_comments"] == ["second"]
        with pytest.raises(
            ValueError, match=f"Message '1000' has no {mode} comment 'x'"
        ):
            empty_message.remove_comment(mode, "x")

    def test_add_comment_empty(self, fr_message):
        with pytest.raises(ValueError, match="Unable to add empty comment"):
            fr_message.add_comment("user", "")

    @pytest.mark.parametrize(
        "pairs, keywords",
        [
            ([["context", "menu"], [["flags"], []]], {}),
            ([["context", "menu"]], {"flags": []}),
            ((), {"context": "menu", "flags": []}),
        ],
    )
    def test_add_metadata(self, fr_message, pairs, keywords):
        fr_message.add_metadata(*pairs, **keywords)
        assert (fr_message.context, fr_message.flags) == ("menu", [])

    def test_add_metadata_inside_rules(self, fr_message):
        fr_message.add_metadata((["rules", "opaque"], True))
        assert fr_message.rules.to_dict() == {"opaque": True}

    @pytest.mark.parametrize(
        "key, methods",
        [
            ("status", "mark_complete(), reopen()"),
            ("count", "mark_complete(), record()"),
            ("fill_mask", "mark_complete(), record()"),
        ],
    )
    @pytest.mark.parametrize("method", ["add_metadata", "update_metadata"])
    def test_guarded_keys_refused(self, fr_message, method, key, methods):
        before = fr_message.metadata.to_dict()
        with pytest.raises(
            ValueError,
            match=re.escape(
                f"metadata key '{key}' is not changed by {method}(): use {methods}"
            ),
        ):
            getattr(fr_message, method)(**{key: "complete"})
        assert fr_message.metadata.to_dict() == before

    @pytest.mark.parametrize(
        "pairs, keywords, error, expected",
        [
            (
                [["context:", "x"]],
                {},
                KeyError,
                "The key 'context:' is not a present key in the metadata dictionary",
            ),
            (
                (),
                {"language": "fr"},
                KeyError,
                "The key 'language' is not a present key in the metadata dictionary",
            ),
            (
                [[["flags", 0], "x"]],
                {},
                KeyError,
                "The path '['flags', 0]' is not a present key in the metadata",
            ),
            ((), {"flags": [""]}, ValueError, "A flag must not be empty"),
            ((), {"context": 1}, TypeError, "Message context must be a str"),
        ],
    )
    def test_add_metadata_rejected(self, fr_message, pairs, keywords, error, expected):
        before = fr_message.metadata.to_dict()
        with pytest.raises(error, match=re.escape(expected)):
            fr_message.add_metadata(*pairs, **keywords)
        assert fr_message.metadata.to_dict() == before

    def test_update_metadata(self, fr_message):
        fr_message.update_metadata((["context"], "menu"), flags=[])
        assert (fr_message.context, fr_message.flags) == ("menu", [])

    def test_update_metadata_same_value(self, fr_message):
        with pytest.raises(
            ValueError,
            match=re.escape("The value () is already stored in the path 'context'"),
        ):
            fr_message.update_metadata(context="")

    @pytest.mark.parametrize("key", ["context", "flags", "user_comments", "rules"])
    def test_remove_metadata(self, fr_message, key):
        fr_message.rules = {"opaque": True}
        fr_message.context = "menu"
        fr_message.remove_metadata(key)
        assert fr_message.metadata.to_dict()[key] == EMPTY_METADATA[key]

    def test_remove_all_keeps_identifier_status_and_record(self, fr_message):
        fr_message.context = "menu"
        fr_message.mark_complete()
        fr_message.remove_metadata()
        assert fr_message.metadata.to_dict() == {
            **EMPTY_METADATA,
            "id": "1000",
            "status": "complete",
            **FR_RECORD,
        }

    def test_remove_metadata_inside_rules(self, fr_message):
        fr_message.rules = {"opaque": True, "kept": 1}
        fr_message.remove_metadata(["rules", "opaque"])
        assert fr_message.rules.to_dict() == {"kept": 1}

    @pytest.mark.parametrize(
        "key, error, expected",
        [
            ("language", KeyError, "path 'language' is not a present key"),
            (
                ["rules", "absent"],
                KeyError,
                "path '['rules', 'absent']' is not a present key",
            ),
            (
                "status",
                ValueError,
                "metadata key 'status' is not changed by remove_metadata()",
            ),
            ("id", ValueError, "metadata key 'id' is not changed by remove_metadata()"),
        ],
    )
    def test_remove_metadata_refused(self, fr_message, key, error, expected):
        with pytest.raises(error, match=re.escape(expected)):
            fr_message.remove_metadata(key)
