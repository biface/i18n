"""
Test module for the Message class in the formatter module.
"""

import pytest
import re

from i18n_tools.models import Message


@pytest.fixture
def fr_message():
    return Message(
        message_id="1000",
        translation="Bonjour",
        alternatives={
            1: "Bonjour Mme {name}",
            2: "Bonjour M. {name}",
        },
        plural_forms={1: "Bonjour à tous", 2: "Bonjour tout le monde"},
        alternative_plural_forms={
            1: {1: "Bonjour Mesdames", 2: "Mesdames"},
            2: {1: "Bonjour Messieurs", 2: "Messieurs"},
        },
        metadata={
            "version": "0.1.0",
            "language": "fr-FR",
            "location": [],
            "flags": ["python-format"],
            "comments": "In French, Greeting message to one or more...",
            "count": {"singular": 0, "plurals": []},
        },
    )


@pytest.fixture
def en_message():
    return Message(
        message_id="1000",
        translation="Hello",
        alternatives={
            1: "Hello {name}",
            2: "Hello {name}",
        },
        plural_forms={1: "Hi everybody", 2: "Hi everyone"},
        alternative_plural_forms={
            1: {1: "Hi everybody", 2: "Ladies"},
            2: {1: "Hi everyone", 2: "Gentlemen"},
        },
        metadata={
            "version": "0.1.0",
            "language": "en",
            "location": [],
            "flags": ["python-format"],
            "comments": "Greeting message to one or more...",
            "count": {"singular": 0, "plurals": []},
        },
    )


@pytest.fixture
def empty_message():
    return Message(message_id="1000", translation="")


class TestMessageCreation:

    @pytest.mark.parametrize(
        "fixture_name", ["fr_message", "en_message", "empty_message"]
    )
    def test_id(self, fixture_name, request):
        message = request.getfixturevalue(fixture_name)
        assert message.message_id == "1000"

    @pytest.mark.parametrize(
        "fixture_name, expect",
        [("fr_message", "Bonjour"), ("en_message", "Hello"), ("empty_message", "")],
    )
    def test_translation(self, fixture_name, expect, request):
        message = request.getfixturevalue(fixture_name)
        assert message.translation == expect

    @pytest.mark.parametrize(
        "fixture_name, loc, expect",
        [
            ("fr_message", 1, "Bonjour Mme {name}"),
            ("en_message", 1, "Hello {name}"),
            ("fr_message", 2, "Bonjour M. {name}"),
            ("en_message", 2, "Hello {name}"),
        ],
    )
    def test_alternatives(self, fixture_name, loc, expect, request):
        message = request.getfixturevalue(fixture_name)
        assert message.alternatives[loc] == expect

    def test_alternatives_empty(self, empty_message):
        assert empty_message.alternatives == {}

    @pytest.mark.parametrize(
        "fixture_name, loc, expect",
        [
            ("fr_message", 1, "Bonjour à tous"),
            ("en_message", 1, "Hi everybody"),
            ("fr_message", 2, "Bonjour tout le monde"),
            ("en_message", 2, "Hi everyone"),
        ],
    )
    def test_plural_forms(self, fixture_name, loc, expect, request):
        message = request.getfixturevalue(fixture_name)
        assert message.plural_forms[loc] == expect

    def test_plural_forms_empty(self, empty_message):
        assert empty_message.plural_forms == {}

    @pytest.mark.parametrize(
        "fixture_name, loc, index, expect",
        [
            ("fr_message", 1, 2, "Mesdames"),
            ("en_message", 1, 2, "Ladies"),
            ("fr_message", 2, 1, "Bonjour Messieurs"),
            ("en_message", 2, 1, "Hi everyone"),
        ],
    )
    def test_alternative_plural_forms(self, fixture_name, loc, index, expect, request):
        message = request.getfixturevalue(fixture_name)
        assert message.alternative_plural_forms[[loc, index]] == expect

    def test_alternative_plural_forms_empty(self, empty_message):
        assert empty_message.alternative_plural_forms == {}

    @pytest.mark.parametrize(
        "fixture_name", ["fr_message", "en_message", "empty_message"]
    )
    def test_metadata_version(self, fixture_name, request):
        message = request.getfixturevalue(fixture_name)
        assert message.metadata["version"] == "0.1.0"

    @pytest.mark.parametrize(
        "fixture_name, expect",
        [("fr_message", "fr-FR"), ("en_message", "en"), ("empty_message", "")],
    )
    def test_metadata_language(self, fixture_name, expect, request):
        message = request.getfixturevalue(fixture_name)
        assert message.metadata["language"] == expect

    @pytest.mark.parametrize(
        "fixture_name, key, expect",
        [
            ("fr_message", "singular", 3),
            ("fr_message", "plurals", [2, 2, 2]),
            ("en_message", "singular", 3),
            ("en_message", "plurals", [2, 2, 2]),
            ("empty_message", "singular", 0),
            ("empty_message", "plurals", [0]),
        ],
    )
    def test_metadata_counts(self, fixture_name, key, expect, request):
        message = request.getfixturevalue(fixture_name)
        assert message.metadata["count"][key] == expect


@pytest.mark.parametrize(
    "fixture_name, expected_language",
    [("fr_message", "fr-FR"), ("en_message", "en"), ("empty_message", "")],
)
def test_message_get_id(fixture_name, expected_language, request) -> None:
    # Get the fixture dynamically using the request object
    message = request.getfixturevalue(fixture_name)

    # Test both the ID and language in a more direct way
    assert message.get_id() == "1000"
    assert message.metadata["language"] == expected_language


@pytest.mark.parametrize(
    "fixture_name, expect",
    [
        ("fr_message", ["Bonjour", "Bonjour à tous", "Bonjour tout le monde"]),
        ("en_message", ["Hello", "Hi everybody", "Hi everyone"]),
        ("empty_message", [""]),
    ],
)
def test_message_get_translation(fixture_name, expect, request) -> None:
    message = request.getfixturevalue(fixture_name)
    assert message.get_translation() == expect
    assert message.translation == expect[0]
    assert message.get_translation()[0] == expect[0]


@pytest.mark.parametrize(
    "fixture_name, expect",
    [("fr_message", "Bonjour"), ("en_message", "Hello"), ("empty_message", "")],
)
def test_message_get_message(fixture_name, expect, request) -> None:
    message = request.getfixturevalue(fixture_name)
    assert message.get_message() == expect


@pytest.mark.parametrize(
    "fixture_name, expect",
    [
        ("fr_message", ["Bonjour à tous", "Bonjour tout le monde"]),
        ("en_message", ["Hi everybody", "Hi everyone"]),
        ("empty_message", []),
    ],
)
def test_message_get_plural(fixture_name, expect, request) -> None:
    message = request.getfixturevalue(fixture_name)
    assert message.get_plural() == expect


@pytest.mark.parametrize(
    "fixture_name, location, expect",
    [
        ("fr_message", 1, "Bonjour à tous"),
        ("en_message", 1, "Hi everybody"),
        ("fr_message", 2, "Bonjour tout le monde"),
        ("en_message", 2, "Hi everyone"),
    ],
)
def test_message_get_plural_form(fixture_name, location, expect, request) -> None:
    message = request.getfixturevalue(fixture_name)
    assert message.get_plural_form(location) == expect


@pytest.mark.parametrize(
    "fixture_name, location, expect",
    [
        ("fr_message", 0, "The location 0 index is out of range"),
        ("en_message", 5, "The location 5 index is out of range"),
        ("fr_message", 10, "The location 10 index is out of range"),
        ("en_message", 3, "The location 3 index is out of range"),
        ("empty_message", 1, "The location 1 index is out of range"),
    ],
)
def test_message_get_plural_form_failed(
    fixture_name, location, expect, request
) -> None:
    message = request.getfixturevalue(fixture_name)
    with pytest.raises(IndexError, match=re.escape(expect)):
        assert message.get_plural_form(location) == ""


@pytest.mark.parametrize(
    "fixture_name, location, expect",
    [
        ("fr_message", 1, ["Bonjour Mme {name}", "Bonjour Mesdames", "Mesdames"]),
        ("fr_message", 2, ["Bonjour M. {name}", "Bonjour Messieurs", "Messieurs"]),
        ("en_message", 1, ["Hello {name}", "Hi everybody", "Ladies"]),
        ("en_message", 2, ["Hello {name}", "Hi everyone", "Gentlemen"]),
    ],
)
def test_message_get_alternative(fixture_name, location, expect, request) -> None:
    message = request.getfixturevalue(fixture_name)
    assert message.get_alternative(location) == expect


@pytest.mark.parametrize(
    "fixture_name, location, expect",
    [
        ("fr_message", 5, "Alternative translation at index 5 not found"),
        ("en_message", 6, "Alternative translation at index 6 not found"),
        ("en_message", 3, "Alternative translation at index 3 not found"),
        ("fr_message", 4, "Alternative translation at index 4 not found"),
    ],
)
def test_message_get_alternative_failed(
    fixture_name, location, expect, request
) -> None:
    message = request.getfixturevalue(fixture_name)
    with pytest.raises(IndexError, match=re.escape(expect)):
        assert message.get_alternative(location) == ""


@pytest.mark.parametrize(
    "fixture_name, loc, index, expected",
    [
        ("fr_message", 1, 1, "Bonjour Mesdames"),
        ("fr_message", 1, 2, "Mesdames"),
        ("en_message", 1, 1, "Hi everybody"),
        ("en_message", 1, 1, "Hi everybody"),
    ],
)
def test_message_get_alternative_plural_form(
    fixture_name, loc, index, expected, request
) -> None:
    message = request.getfixturevalue(fixture_name)
    assert message.get_alternative_plural_form(loc, index) == expected


@pytest.mark.parametrize(
    "fixture_name, location, option, expect",
    [
        ("fr_message", 0, 1, "The alternative message index (0) is out of range"),
        (
            "en_message",
            1,
            3,
            "The plural index (3) of alternative message (1) is out of range",
        ),
        ("en_message", 4, 1, "The alternative message index (4) is out of range"),
        (
            "fr_message",
            1,
            0,
            "The plural index (0) of alternative message (1) is out of range",
        ),
        ("empty_message", 1, 1, "The alternative message index (1) is out of range"),
    ],
)
def test_message_get_alternative_plural_form_failed(
    fixture_name, location, option, expect, request
) -> None:
    message = request.getfixturevalue(fixture_name)
    with pytest.raises(IndexError, match=re.escape(expect)):
        assert message.get_alternative_plural_form(location, option) == ""


@pytest.mark.parametrize(
    "fixture_name, dict",
    [
        (
            "fr_message",
            {
                "version": "0.1.0",
                "language": "fr-FR",
                "location": [],
                "flags": ["python-format"],
                "comments": "In French, Greeting message to one or more...",
                "count": {"singular": 3, "plurals": [2, 2, 2]},
            },
        ),
        (
            "empty_message",
            {
                "version": "0.1.0",
                "language": "",
                "location": [],
                "flags": ["python-format"],
                "comments": "",
                "count": {"singular": 0, "plurals": [0]},
            },
        ),
        (
            "en_message",
            {
                "version": "0.1.0",
                "language": "en",
                "location": [],
                "flags": ["python-format"],
                "comments": "Greeting message to one or more...",
                "count": {"singular": 3, "plurals": [2, 2, 2]},
            },
        ),
    ],
)
def test_message_get_metadata_void(fixture_name, dict, request) -> None:
    message = request.getfixturevalue(fixture_name)
    mdict = message.get_metadata().to_dict()
    assert mdict == dict


@pytest.mark.parametrize(
    "fixture_name, path, expected",
    [
        ("fr_message", "version", "0.1.0"),
        ("fr_message", "language", "fr-FR"),
        ("fr_message", "flags", ["python-format"]),
        ("fr_message", "count", {"singular": 3, "plurals": [2, 2, 2]}),
        ("fr_message", ["count", "singular"], 3),
        ("fr_message", ["count", "plurals"], [2, 2, 2]),
        ("empty_message", "version", "0.1.0"),
        ("empty_message", "language", ""),
        ("empty_message", "flags", ["python-format"]),
        ("empty_message", "count", {"singular": 0, "plurals": [0]}),
        ("empty_message", ["count", "singular"], 0),
        ("empty_message", ["count", "plurals"], [0]),
        ("en_message", "version", "0.1.0"),
        ("en_message", "language", "en"),
        ("en_message", "flags", ["python-format"]),
        ("en_message", "count", {"singular": 3, "plurals": [2, 2, 2]}),
        ("en_message", ["count", "singular"], 3),
        ("en_message", ["count", "plurals"], [2, 2, 2]),
    ],
)
def test_message_get_metadata(fixture_name, path, expected, request) -> None:
    message = request.getfixturevalue(fixture_name)
    assert message.get_metadata(path) == expected


def test_message_get_metadata_failed(fr_message):
    with pytest.raises(
        KeyError,
        match=re.escape("Metadata '['counts', 'singular']' is not a key or path"),
    ):
        fr_message.get_metadata(["counts", "singular"])


@pytest.mark.parametrize(
    "fixture_name, option, expected",
    [
        ("fr_message", 1, "Bonjour Mme {name}"),
        ("fr_message", 2, "Bonjour M. {name}"),
        ("en_message", 1, "Hello {name}"),
        ("en_message", 2, "Hello {name}"),
    ],
)
def test_message_get_alternative_message(
    fixture_name, option, expected, request
) -> None:
    message = request.getfixturevalue(fixture_name)
    assert message.get_alternative_message(option) == expected


@pytest.mark.parametrize(
    "fixture_name, option, expected",
    [
        ("empty_message", 1, "Alternative translation at index 1 not found"),
        ("fr_message", 3, "Alternative translation at index 3 not found"),
        ("en_message", 0, "Alternative translation at index 0 not found"),
    ],
)
def test_message_get_alternative_message_failed(
    fixture_name, option, expected, request
) -> None:
    message = request.getfixturevalue(fixture_name)
    with pytest.raises(IndexError, match=re.escape(expected)):
        message.get_alternative_message(option)


@pytest.mark.parametrize(
    "fixture_name, options, expected",
    [
        ("empty_message", {"translation": "Hello"}, [("translation", "Hello")]),
        (
            "empty_message",
            {"translation": "Hello", "alternatives": {1: "Bonjour Mme {name}"}},
            [("translation", "Hello"), ("alternatives", {1: "Bonjour Mme {name}"})],
        ),
        (
            "empty_message",
            {
                "translation": "Hello",
                "alternatives": {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"},
            },
            [
                ("translation", "Hello"),
                ("alternatives", {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"}),
            ],
        ),
        (
            "empty_message",
            {
                "translation": "Hello",
                "alternatives": {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"},
                "plural_forms": {1: "Bonjour tout le monde"},
            },
            [
                ("translation", "Hello"),
                ("alternatives", {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"}),
                ("plural_forms", {1: "Bonjour tout le monde"}),
            ],
        ),
        (
            "empty_message",
            {
                "translation": "Hello",
                "alternatives": {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"},
                "plural_forms": {1: "Bonjour tout le monde", 2: "Bonjour à tous"},
            },
            [
                ("translation", "Hello"),
                ("alternatives", {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"}),
                ("plural_forms", {1: "Bonjour tout le monde", 2: "Bonjour à tous"}),
            ],
        ),
        (
            "empty_message",
            {
                "translation": "Hello",
                "alternatives": {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"},
                "plural_forms": {1: "Bonjour tout le monde", 2: "Bonjour à tous"},
                "alternative_plural_forms": {
                    1: {1: "Bonjour Mesdames"},
                },
            },
            [
                ("translation", "Hello"),
                ("alternatives", {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"}),
                ("plural_forms", {1: "Bonjour tout le monde", 2: "Bonjour à tous"}),
                (
                    "alternative_plural_forms",
                    {
                        1: {1: "Bonjour Mesdames"},
                    },
                ),
            ],
        ),
        (
            "empty_message",
            {
                "translation": "Hello",
                "alternatives": {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"},
                "plural_forms": {1: "Bonjour tout le monde", 2: "Bonjour à tous"},
                "alternative_plural_forms": {
                    1: {1: "Bonjour Mesdames"},
                    2: {1: "Bonjour Messieurs"},
                },
            },
            [
                ("translation", "Hello"),
                ("alternatives", {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"}),
                ("plural_forms", {1: "Bonjour tout le monde", 2: "Bonjour à tous"}),
                (
                    "alternative_plural_forms",
                    {1: {1: "Bonjour Mesdames"}, 2: {1: "Bonjour Messieurs"}},
                ),
            ],
        ),
        (
            "empty_message",
            {
                "translation": "Hello",
                "alternatives": {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"},
                "plural_forms": {1: "Bonjour tout le monde", 2: "Bonjour à tous"},
                "alternative_plural_forms": {
                    1: {1: "Bonjour Mesdames", 2: "Mesdames"},
                    2: {1: "Bonjour Messieurs", 2: "Messieurs"},
                },
            },
            [
                ("translation", "Hello"),
                ("alternatives", {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"}),
                ("plural_forms", {1: "Bonjour tout le monde", 2: "Bonjour à tous"}),
                (
                    "alternative_plural_forms",
                    {
                        1: {1: "Bonjour Mesdames", 2: "Mesdames"},
                        2: {1: "Bonjour Messieurs", 2: "Messieurs"},
                    },
                ),
            ],
        ),
    ],
)
def test_message_add_translation(fixture_name, options, expected, request) -> None:
    message = request.getfixturevalue(fixture_name)
    message.add_translation(**options)
    for attribute, value in expected:
        assert message.__getattribute__(attribute) == value


@pytest.mark.parametrize(
    "fixture_name, options, expected",
    [
        (
            "fr_message",
            {"translations": "Hello"},
            "At least one translation is required",
        ),
        (
            "fr_message",
            {"alternatives": {1: "Bonjour Mme {name}"}},
            "At least one translation is required",
        ),
        (
            "empty_message",
            {"translation": "Hello", "alternatives": {2: "Bonjour Mme {name}"}},
            "The alternatives value is malformed",
        ),
        (
            "empty_message",
            {
                "translation": "Hello",
                "alternatives": {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"},
                "plural_forms": {2: "Bonjour tout le monde"},
            },
            "The plural_forms value is malformed",
        ),
        (
            "empty_message",
            {
                "translation": "Hello",
                "alternatives": {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"},
                "plural_forms": {1: "Bonjour tout le monde", 2: "Bonjour à tous"},
                "alternative_plural_forms": {
                    1: {1: "Bonjour Mesdames", 2: "Mesdames"},
                    3: {1: "Bonjour Messieurs", 2: "Messieurs"},
                },
            },
            "The alternative_plural_forms value is malformed",
        ),
    ],
)
def test_message_add_translation_failed(
    fixture_name, options, expected, request
) -> None:
    message = request.getfixturevalue(fixture_name)
    with pytest.raises(ValueError, match=re.escape(expected)):
        message.add_translation(**options)


@pytest.mark.parametrize(
    "fixture_name, additional, expected",
    [
        (
            "fr_message",
            (3, "Salut à tous"),
            {1: "Bonjour à tous", 2: "Bonjour tout le monde", 3: "Salut à tous"},
        ),
        (
            "en_message",
            (3, "Hello everyone"),
            {1: "Hi everybody", 2: "Hi everyone", 3: "Hello everyone"},
        ),
    ],
)
def test_message_add_plural_form(fixture_name, additional, expected, request) -> None:
    message = request.getfixturevalue(fixture_name)
    message.add_plural_form(additional[0], additional[1])
    assert message.plural_forms == expected


@pytest.mark.parametrize(
    "fixture_name, additional, expected",
    [
        (
            "fr_message",
            (4, "Salut à tous"),
            "Plural form index (4) is not in a valid range",
        ),
        (
            "en_message",
            (6, "Hello everyone"),
            "Plural form index (6) is not in a valid range",
        ),
        (
            "fr_message",
            (0, "Salut à tous"),
            "Plural form index (0) is not in a valid range",
        ),
        (
            "en_message",
            (-1, "Hello everyone"),
            "Plural form index (-1) is not in a valid range",
        ),
    ],
)
def test_message_add_plural_form_failed(
    fixture_name, additional, expected, request
) -> None:
    message = request.getfixturevalue(fixture_name)
    with pytest.raises(ValueError, match=re.escape(expected)):
        message.add_plural_form(additional[0], additional[1])


@pytest.mark.parametrize(
    "translation, alternatives, index, additional, expected",
    [
        ("Bonjour", None, 1, "Bonjour, {name}", {1: "Bonjour, {name}"}),
        (
            "Bonjour",
            {1: "Bonjour, {name}"},
            2,
            "Bonjour M. {name}",
            {1: "Bonjour, {name}", 2: "Bonjour M. {name}"},
        ),
        (
            "Bonjour",
            {1: "Bonjour, {name}", 2: "Bonjour M. {name}"},
            3,
            "Bonjour, Mme {name}",
            {1: "Bonjour, {name}", 2: "Bonjour M. {name}", 3: "Bonjour, Mme {name}"},
        ),
    ],
)
def test_message_add_alternative(
    empty_message, translation, index, alternatives, additional, expected
) -> None:
    message = empty_message
    message.add_translation(translation=translation, alternatives=alternatives)
    message.add_alternative(index, additional)
    assert message.alternatives == expected


@pytest.mark.parametrize(
    "translation, alternatives, index, additional, expected",
    [
        (
            "Bonjour",
            None,
            2,
            "Bonjour, {name}",
            "Alternative index (2) is not in a valid range",
        ),
        (
            "Bonjour",
            {1: "Bonjour, {name}"},
            0,
            "Bonjour M. {name}",
            "Alternative index (0) is not in a valid range",
        ),
        (
            "Bonjour",
            {1: "Bonjour, {name}", 2: "Bonjour M. {name}"},
            -1,
            "Bonjour, Mme {name}",
            "Alternative index (-1) is not in a valid range",
        ),
    ],
)
def test_message_add_alternative_failed(
    empty_message, translation, index, alternatives, additional, expected
) -> None:
    message = empty_message
    message.add_translation(translation=translation, alternatives=alternatives)
    with pytest.raises(ValueError, match=re.escape(expected)):
        message.add_alternative(index, additional)


@pytest.mark.parametrize(
    "options, alt_index, plural_index, additional,expected",
    [
        (
            {
                "translation": "Hello",
                "alternatives": {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"},
                "plural_forms": {1: "Bonjour tout le monde", 2: "Bonjour à tous"},
            },
            1,
            1,
            "Bonjour Mesdames",
            {1: {1: "Bonjour Mesdames"}},
        ),
        (
            {
                "translation": "Hello",
                "alternatives": {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"},
                "plural_forms": {1: "Bonjour tout le monde", 2: "Bonjour à tous"},
                "alternative_plural_forms": {
                    1: {1: "Bonjour Mesdames"},
                },
            },
            2,
            1,
            "Bonjour Messieurs",
            {1: {1: "Bonjour Mesdames"}, 2: {1: "Bonjour Messieurs"}},
        ),
        (
            {
                "translation": "Hello",
                "alternatives": {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"},
                "plural_forms": {1: "Bonjour tout le monde", 2: "Bonjour à tous"},
                "alternative_plural_forms": {
                    1: {1: "Bonjour Mesdames"},
                    2: {1: "Bonjour Messieurs", 2: "Messieurs"},
                },
            },
            1,
            2,
            "Mesdames",
            {
                1: {1: "Bonjour Mesdames", 2: "Mesdames"},
                2: {1: "Bonjour Messieurs", 2: "Messieurs"},
            },
        ),
    ],
)
def test_message_add_plural_forms(
    empty_message, options, alt_index, plural_index, additional, expected
) -> None:
    message = empty_message
    message.add_translation(**options)
    message.add_alternative_plural_form(alt_index, plural_index, additional)
    assert message.alternative_plural_forms == expected


@pytest.mark.parametrize(
    "options, alt_index, plural_index, additional, error, expected",
    [
        (
            {
                "translation": "Hello",
                "alternatives": {},
                "plural_forms": {},
            },
            1,
            1,
            "Bonjour Mesdames",
            KeyError,
            "Alternative translation at index (1) not found",
        ),
        (
            {
                "translation": "Hello",
                "alternatives": {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"},
                "plural_forms": {1: "Bonjour tout le monde", 2: "Bonjour à tous"},
                "alternative_plural_forms": {
                    1: {1: "Bonjour Mesdames"},
                },
            },
            4,
            1,
            "Bonjour Messieurs",
            ValueError,
            "Alternative index (4) in not in a valid range",
        ),
        (
            {
                "translation": "Hello",
                "alternatives": {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"},
                "plural_forms": {1: "Bonjour tout le monde", 2: "Bonjour à tous"},
                "alternative_plural_forms": {
                    1: {1: "Bonjour Mesdames"},
                    2: {1: "Bonjour Messieurs", 2: "Messieurs"},
                },
            },
            1,
            6,
            "Mesdames",
            ValueError,
            "Plural form index (6) is not in a valid range",
        ),
    ],
)
def test_message_add_plural_forms_failed(
    empty_message, options, alt_index, plural_index, additional, error, expected
) -> None:
    message = empty_message
    message.add_translation(**options)
    with pytest.raises(error, match=re.escape(expected)):
        message.add_alternative_plural_form(alt_index, plural_index, additional)


# TODO add_location


def test_message_format():
    """Test formatting a message with variables."""
    message = Message(
        message_id="greeting",
        translation="Hello, {name}!",
        alternatives={1: "Hi, {name}!"},
        plural_forms={1: "Hello, {count} {name}s!"},
        alternative_plural_forms={1: {1: "Hi, {count} {name}s!"}},
    )

    # Test formatting the main translation
    assert message.format(name="John") == "Hello, John!"

    # Test formatting an alternative
    assert message.format(alternative=1, name="John") == "Hi, John!"

    # Test formatting a plural form
    assert message.format(plural_index=1, name="user", count=5) == "Hello, 5 users!"

    # Test formatting an alternative plural form
    assert (
        message.format(alternative=1, plural_index=1, name="user", count=3)
        == "Hi, 3 users!"
    )

    # Test missing variable
    with pytest.raises(KeyError):
        message.format()
