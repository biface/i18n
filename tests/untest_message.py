"""
Test module for the Message class in the formatter module.
"""

import pytest
import re

from i18n_tools.models import Message
from ndict_tools import StrictNestedDictionary


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


@pytest.fixture(scope="module")
def empty_module_message():
    return Message(
        message_id="1000",
        translation="",
    )


# 1. Testing attributes


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


def test_failed_init():
    with pytest.raises(ValueError):
        Message("1001", "A failed", alternatives={2: "Failed index"})


# 2. Test access to data

# 2.1 Testing messages


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


# 2.2 Testing translations


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
    "fixture_name, location, expect",
    [
        ("fr_message", 1, ["Bonjour Mme {name}", "Bonjour Mesdames", "Mesdames"]),
        ("fr_message", 2, ["Bonjour M. {name}", "Bonjour Messieurs", "Messieurs"]),
        ("en_message", 1, ["Hello {name}", "Hi everybody", "Ladies"]),
        ("en_message", 2, ["Hello {name}", "Hi everyone", "Gentlemen"]),
    ],
)
def test_message_get_alternative_translation(
        fixture_name, location, expect, request
) -> None:
    message = request.getfixturevalue(fixture_name)
    assert message.get_alternative_translation(location) == expect


@pytest.mark.parametrize(
    "fixture_name, location, expect",
    [
        ("fr_message", 5, "Alternative translation at index 5 not found"),
        ("en_message", 6, "Alternative translation at index 6 not found"),
        ("en_message", 3, "Alternative translation at index 3 not found"),
        ("fr_message", 4, "Alternative translation at index 4 not found"),
    ],
)
def test_message_get_alternative_translation_failed(
        fixture_name, location, expect, request
) -> None:
    message = request.getfixturevalue(fixture_name)
    with pytest.raises(IndexError, match=re.escape(expect)):
        assert message.get_alternative_translation(location) == ""


@pytest.mark.parametrize(
    "fixture_name, expect",
    [
        ("fr_message", ["Bonjour à tous", "Bonjour tout le monde"]),
        ("en_message", ["Hi everybody", "Hi everyone"]),
        ("empty_message", []),
    ],
)
def test_message_get_plural_translation(fixture_name, expect, request) -> None:
    message = request.getfixturevalue(fixture_name)
    assert message.get_plural_translation() == expect


@pytest.mark.parametrize("fixture_name, option, expected", [
    ("fr_message", 1, ["Bonjour Mesdames", "Mesdames"]),
    ("en_message", 2, ["Hi everyone", "Gentlemen"]),
    ("en_message", 1, ["Hi everybody", "Ladies"]),
    ("fr_message", 2, ["Bonjour Messieurs", "Messieurs"])
])
def test_message_get_alternative_plural_translation(fixture_name, option, expected, request) -> None:
    message = request.getfixturevalue(fixture_name)
    assert message.get_alternative_plural_translation(option) == expected


@pytest.mark.parametrize("fixture_name, option, expected", [
    ("fr_message", 0, "Alternative translation at index 0 is out of range"),
    ("en_message", -1, "Alternative translation at index -1 is out of range"),
    ("en_message", 3, "Alternative translation at index 3 is out of range"),
    ("fr_message", 4, "Alternative translation at index 4 is out of range")
])
def test_message_get_alternative_plural_translation_failed(fixture_name, option, expected, request) -> None:
    message = request.getfixturevalue(fixture_name)
    with pytest.raises(IndexError, match=re.escape(expected)):
        assert message.get_alternative_plural_translation(option) == expected


# 2.3 Testing components


@pytest.mark.parametrize(
    "fixture_name, expect",
    [("fr_message", "Bonjour"), ("en_message", "Hello"), ("empty_message", "")],
)
def test_message_get_component(fixture_name, expect, request) -> None:
    message = request.getfixturevalue(fixture_name)
    assert message.get_component() == expect


@pytest.mark.parametrize(
    "fixture_name, token, expect",
    [
        ("fr_message", 0, "Bonjour"),
        ("en_message", 0, "Hello"),
        ("empty_message", 0, ""),
        ("fr_message", 1, "Bonjour à tous"),
        ("en_message", 1, "Hi everybody"),
        ("fr_message", 2, "Bonjour tout le monde"),
        ("en_message", 2, "Hi everyone"),
    ],
)
def test_message_get_component_token(fixture_name, token, expect, request) -> None:
    message = request.getfixturevalue(fixture_name)
    assert message.get_component(token) == expect


@pytest.mark.parametrize(
    "fixture_name, token, expect",
    [
        ("fr_message", 4, "Message token (4) is out of range"),
        ("en_message", -1, "Token index (-1) must be positive"),
        ("empty_message", 1, "Message token (1) is out of range"),
    ],
)
def test_message_get_component_token_failed(
        fixture_name, token, expect, request
) -> None:
    message = request.getfixturevalue(fixture_name)
    with pytest.raises(IndexError, match=re.escape(expect)):
        message.get_component(token)


@pytest.mark.parametrize(
    "fixture_name, option, expected",
    [
        ("fr_message", 1, "Bonjour Mme {name}"),
        ("fr_message", 2, "Bonjour M. {name}"),
        ("en_message", 1, "Hello {name}"),
        ("en_message", 2, "Hello {name}"),
    ],
)
def test_message_get_alternative_component(
        fixture_name, option, expected, request
) -> None:
    message = request.getfixturevalue(fixture_name)
    assert message.get_alternative_component(option) == expected


@pytest.mark.parametrize(
    "fixture_name, option, token, expected",
    [
        ("empty_message", 1, 0, "Alternative translation at index 1 not found"),
        ("fr_message", 3, 0, "Alternative translation at index 3 not found"),
        ("en_message", 0, 0, "Alternative translation at index 0 not found"),
        ("fr_message", 1, -1, "The token (-1) of alternative is out of range"),
        ("en_message", 1, 4, "The token (4) of alternative is out of range"),
    ],
)
def test_message_get_alternative_component_failed(
        fixture_name, option, token, expected, request
) -> None:
    message = request.getfixturevalue(fixture_name)
    with pytest.raises(IndexError, match=re.escape(expected)):
        message.get_alternative_component(option, token)


@pytest.mark.parametrize(
    "fixture_name, location, expect",
    [
        ("fr_message", 1, "Bonjour à tous"),
        ("en_message", 1, "Hi everybody"),
        ("fr_message", 2, "Bonjour tout le monde"),
        ("en_message", 2, "Hi everyone"),
    ],
)
def test_message_get_plural_component(fixture_name, location, expect, request) -> None:
    message = request.getfixturevalue(fixture_name)
    assert message.get_plural_component(location) == expect


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
def test_message_get_plural_component_failed(
        fixture_name, location, expect, request
) -> None:
    message = request.getfixturevalue(fixture_name)
    with pytest.raises(IndexError, match=re.escape(expect)):
        assert message.get_plural_component(location) == ""


@pytest.mark.parametrize(
    "fixture_name, loc, index, expected",
    [
        ("fr_message", 1, 1, "Bonjour Mesdames"),
        ("fr_message", 1, 2, "Mesdames"),
        ("en_message", 1, 1, "Hi everybody"),
        ("en_message", 1, 1, "Hi everybody"),
    ],
)
def test_message_get_alternative_plural_component(
        fixture_name, loc, index, expected, request
) -> None:
    message = request.getfixturevalue(fixture_name)
    assert message.get_alternative_plural_component(loc, index) == expected


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
def test_message_get_alternative_plural_component_failed(
        fixture_name, location, option, expect, request
) -> None:
    message = request.getfixturevalue(fixture_name)
    with pytest.raises(IndexError, match=re.escape(expect)):
        assert message.get_alternative_plural_component(location, option) == ""


# 2.4 Testing metadata


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


# 3 Testing adding function

# 3.1 Testing Messages


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
def test_message_add_message(fixture_name, options, expected, request) -> None:
    message = request.getfixturevalue(fixture_name)
    message.add_message(**options)
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
def test_message_add_message_failed(fixture_name, options, expected, request) -> None:
    message = request.getfixturevalue(fixture_name)
    with pytest.raises(ValueError, match=re.escape(expected)):
        message.add_message(**options)


# 3.2 Testing translations

@pytest.mark.parametrize("fixture_name, translation, expected", [
    ("empty_message", ["Hello"], ("Hello", {}, 1, [0])),
    ("empty_message", ["Hello", "Hi everybody"], ("Hello", {1: "Hi everybody"}, 1, [1])),
    ("empty_message", ["Hello", "Hi everybody", "Hi everyone"],
     ("Hello", {1: "Hi everybody", 2: "Hi everyone"}, 1, [2])),
    ("empty_message", {"translation": "Hello"}, ("Hello", {}, 1, [0])),
    ("empty_message", {"translation": "Hello", "plural_forms": {1: "Hi everybody"}},
     ("Hello", {1: "Hi everybody"}, 1, [1])),
    ("empty_message", {"translation": "Hello", "plural_forms": {1: "Hi everybody", 2: "Hi everyone"}},
     ("Hello", {1: "Hi everybody", 2: "Hi everyone"}, 1, [2])),
])
def test_message_add_translation(fixture_name, translation, expected, request) -> None:
    message = request.getfixturevalue(fixture_name)
    if isinstance(translation, dict):
        message.add_translation(**translation)
    else:
        message.add_translation(translation)
    assert message.translation == expected[0]
    assert message.plural_forms == expected[1]
    assert message.metadata[['count', 'singular']] == expected[2]
    assert message.metadata[['count', 'plurals']] == expected[3]


@pytest.mark.parametrize("fixture_name, translation, expected", [
    ("empty_message", None,
     "No translation specified"),
    ("empty_message", [""],
     "Singular of translation is required and cannot be None or empty : ''"),
    ("empty_message", {"translation": None},
     "Singular of translation is required and cannot be None or empty : 'None'"),
    ("empty_message", {"translation": ""},
     "Singular of translation is required and cannot be None or empty : ''"),
    ("empty_message", {"translation": "Hello", "plural_forms": {2: "Hi everybody"}},
     "Plural forms is malformed : {2: 'Hi everybody'}"),
])
def test_message_add_translation_failed(fixture_name, translation, expected, request) -> None:
    message = request.getfixturevalue(fixture_name)
    with pytest.raises(ValueError, match=re.escape(expected)):
        if isinstance(translation, dict):
            message.add_translation(**translation)
        else:
            message.add_translation(translation)


@pytest.mark.parametrize("fixture_name, translation, expected", [
    ("empty_message", ["Hello {name}"], ({1: "Hello {name}"}, {1: {}}, 2, [2, 0])),
    ("empty_message", {"alternative_translation": "Hello {name}"},
     ({1: "Hello {name}"}, {1: {}}, 2, [2, 0])),
    ("empty_message", ["Hello {name}", "Hi everybody"], ({1: "Hello {name}"}, {1: {1: "Hi everybody"}}, 2, [2, 1])),
    ("empty_message", {"alternative_translation": "Hello {name}",
                       "alternative_plural_forms": ["Hi everybody"]},
     ({1: "Hello {name}"}, {1: {1: "Hi everybody"}}, 2, [2, 1])),
    ("empty_message", {"alternative_translation": "Hello {name}",
                       "alternative_plural_forms": {1: "Hi everybody"}},
     ({1: "Hello {name}"}, {1: {1: "Hi everybody"}}, 2, [2, 1])),
    ("empty_message", ["Hello {name}", "Hi everybody", "Hi everyone"],
     ({1: "Hello {name}"}, {1: {1: "Hi everybody", 2: "Hi everyone"}}, 2, [2, 2])),
    ("empty_message", {"alternative_translation": "Hello {name}",
                       "alternative_plural_forms": ["Hi everybody", "Hi everyone"]},
     ({1: "Hello {name}"}, {1: {1: "Hi everybody", 2: "Hi everyone"}}, 2, [2, 2])),
    ("empty_message", {"alternative_translation": "Hello {name}",
                       "alternative_plural_forms": {1: "Hi everybody", 2: "Hi everyone"}},
     ({1: "Hello {name}"}, {1: {1: "Hi everybody", 2: "Hi everyone"}}, 2, [2, 2])),
    ("fr_message", ["Cher {name}", "Chères et chers collègues", "Chers vous tous"],
     ({1: "Bonjour Mme {name}", 2: "Bonjour M. {name}", 3: "Cher {name}"},
      {1: {1: "Bonjour Mesdames", 2: "Mesdames"},
       2: {1: "Bonjour Messieurs", 2: "Messieurs"},
       3: {1: "Chères et chers collègues", 2: "Chers vous tous"}
       }, 4, [2, 2, 2, 2]
      )),
    ("fr_message", {"alternative_translation": "Cher {name}",
                    "alternative_plural_forms": ["Chères et chers collègues", "Chers vous tous"]},
     ({1: "Bonjour Mme {name}", 2: "Bonjour M. {name}", 3: "Cher {name}"},
      {1: {1: "Bonjour Mesdames", 2: "Mesdames"},
       2: {1: "Bonjour Messieurs", 2: "Messieurs"},
       3: {1: "Chères et chers collègues", 2: "Chers vous tous"}
       }, 4, [2, 2, 2, 2]
      )),
    ("fr_message", {"alternative_translation": "Cher {name}",
                    "alternative_plural_forms": {1: "Chères et chers collègues", 2: "Chers vous tous"}},
     ({1: "Bonjour Mme {name}", 2: "Bonjour M. {name}", 3: "Cher {name}"},
      {1: {1: "Bonjour Mesdames", 2: "Mesdames"},
       2: {1: "Bonjour Messieurs", 2: "Messieurs"},
       3: {1: "Chères et chers collègues", 2: "Chers vous tous"}
       }, 4, [2, 2, 2, 2]
      )),
    ("fr_message", ["Cher {name}", "Chères et chers collègues"],
     ({1: "Bonjour Mme {name}", 2: "Bonjour M. {name}", 3: "Cher {name}"},
      {1: {1: "Bonjour Mesdames", 2: "Mesdames"},
       2: {1: "Bonjour Messieurs", 2: "Messieurs"},
       3: {1: "Chères et chers collègues"}
       }, 4, [2, 2, 2, 1]
      )),
    ("fr_message", {"alternative_translation": "Cher {name}",
                    "alternative_plural_forms": ["Chères et chers collègues"]},
     ({1: "Bonjour Mme {name}", 2: "Bonjour M. {name}", 3: "Cher {name}"},
      {1: {1: "Bonjour Mesdames", 2: "Mesdames"},
       2: {1: "Bonjour Messieurs", 2: "Messieurs"},
       3: {1: "Chères et chers collègues"}
       }, 4, [2, 2, 2, 1]
      )),
    ("fr_message", {"alternative_translation": "Cher {name}",
                    "alternative_plural_forms": {1: "Chères et chers collègues"}},
     ({1: "Bonjour Mme {name}", 2: "Bonjour M. {name}", 3: "Cher {name}"},
      {1: {1: "Bonjour Mesdames", 2: "Mesdames"},
       2: {1: "Bonjour Messieurs", 2: "Messieurs"},
       3: {1: "Chères et chers collègues"}
       }, 4, [2, 2, 2, 1]
      ))
])
def test_message_add_alternative_translation(fixture_name, translation, expected, request) -> None:
    message = request.getfixturevalue(fixture_name)
    if message.translation == "":
        message.add_translation(["Hello", "Hi everybody", "Hi everyone"])
    if isinstance(translation, dict):
        message.add_alternative_translation(**translation)
    else:
        message.add_alternative_translation(translation)
    assert message.alternatives == expected[0]
    assert message.alternative_plural_forms.to_dict() == expected[1]
    assert message.metadata[['count', 'singular']] == expected[2]
    assert message.metadata[['count', 'plurals']] == expected[3]


@pytest.mark.parametrize("fixture_name, translation, expected", [
    ("en_message", None, "No alternative translation specified"),
    ("empty_message", ["Hello {name}"], "Cannot add an alternative translation, there presently is no translation"),
    ("fr_message", [None, "Chères et chers collègues", "Chers vous tous"],
     "Singular of translation is required and cannot be None or empty : 'None'"),
    ("fr_message", ["", "Chères et chers collègues", "Chers vous tous"],
     "Singular of translation is required and cannot be None or empty : ''"),
    ("fr_message", {"alternative_translation": None,
                    "alternative_plural_forms": ["Chères et chers collègues", "Chers vous tous"]},
     "Singular of translation is required and cannot be None or empty : 'None'"),
    ("fr_message", {"alternative_translation": "",
                    "alternative_plural_forms": {1: "Chères et chers collègues", 2: "Chers vous tous"}},
     "Singular of translation is required and cannot be None or empty : ''"),

    ("fr_message", {"alternative_translation": "Cher {name}",
                    "alternative_plural_forms": ("Chères et chers collègues", "Chers vous tous")},
     "Alternative plural forms is malformed : ('Chères et chers collègues', 'Chers vous tous')"),
    ("fr_message", {"alternative_translation": "Cher {name}",
                    "alternative_plural_forms": {2: "Chères et chers collègues"}},
     "Alternative plural forms is malformed : {2: 'Chères et chers collègues'}")
])
def test_message_add_alternative_translation_failed(fixture_name, translation, expected, request) -> None:
    message = request.getfixturevalue(fixture_name)
    with pytest.raises(ValueError, match=re.escape(expected)):
        if isinstance(translation, dict):
            message.add_alternative_translation(**translation)
        else:
            message.add_alternative_translation(translation)


# 3.3 Testing components


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
def test_message_add_plural_component(
        fixture_name, additional, expected, request
) -> None:
    message = request.getfixturevalue(fixture_name)
    message.add_plural_component(additional[0], additional[1])
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
def test_message_add_plural_component_failed(
        fixture_name, additional, expected, request
) -> None:
    message = request.getfixturevalue(fixture_name)
    with pytest.raises(ValueError, match=re.escape(expected)):
        message.add_plural_component(additional[0], additional[1])


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
def test_message_add_alternative_component(
        empty_message, translation, index, alternatives, additional, expected
) -> None:
    message = empty_message
    message.add_message(translation=translation, alternatives=alternatives)
    message.add_alternative_component(index, additional)
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
def test_message_add_alternative_component_failed(
        empty_message, translation, index, alternatives, additional, expected
) -> None:
    message = empty_message
    message.add_message(translation=translation, alternatives=alternatives)
    with pytest.raises(ValueError, match=re.escape(expected)):
        message.add_alternative_component(index, additional)


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
def test_message_add_alternative_plural_component(
        empty_message, options, alt_index, plural_index, additional, expected
) -> None:
    message = empty_message
    message.add_message(**options)
    message.add_alternative_plural_component(alt_index, plural_index, additional)
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
def test_message_add_alternative_plural_component_failed(
        empty_message, options, alt_index, plural_index, additional, error, expected
) -> None:
    message = empty_message
    message.add_message(**options)
    with pytest.raises(error, match=re.escape(expected)):
        message.add_alternative_plural_component(alt_index, plural_index, additional)


# 3.4 Testing metadata


@pytest.mark.parametrize(
    "line, file, expected",
    [
        (126, "files.text", [("files.text", 126)]),
        (67, "explain.txt", [("files.text", 126), ("explain.txt", 67)]),
        (
                67,
                "files.txt",
                [("files.text", 126), ("explain.txt", 67), ("files.txt", 67)],
        ),
    ],
)
def test_message_add_metadata_location(
        empty_module_message, line, file, expected
) -> None:
    message = empty_module_message
    message.add_location(line, file)
    assert message.metadata["location"] == expected


def test_message_add_metadata_language(empty_module_message) -> None:
    message = empty_module_message
    message.add_language("en-IE")
    assert message.metadata["language"] == "en-IE"


def test_message_add_metadata_language_failed(empty_module_message) -> None:
    message = empty_module_message
    with pytest.raises(
            ValueError, match="Invalid language tag: ja.Latn/hepburn@heploc"
    ):
        message.add_language("ja.Latn/hepburn@heploc")


@pytest.mark.parametrize(
    "comment, expected",
    [("A first comment", "A first comment"), ("Another comment", "Another comment")],
)
def test_message_add_comment(empty_module_message, comment, expected) -> None:
    message = empty_module_message
    message.add_comment(comment)
    assert message.metadata["comment"] == expected


@pytest.mark.parametrize(
    "dictionary, expected",
    [
        (
                {
                    "version": "0.2.0",
                    "language": "fr-FR",
                    "location": [("file.py", 132)],
                    "flags": ["python-format"],
                    "comments": "A test for metadata",
                    "count": {
                        "singular": 0,
                        "plurals": [0],
                    },
                },
                {
                    "version": "0.2.0",
                    "language": "fr-FR",
                    "location": [("file.py", 132)],
                    "flags": ["python-format"],
                    "comments": "A test for metadata",
                    "count": {
                        "singular": 0,
                        "plurals": [0],
                    },
                },
        ),
        (
                StrictNestedDictionary(
                    {
                        "version": "0.2.0",
                        "language": "fr-FR",
                        "location": [("file.py", 132)],
                        "flags": ["python-format"],
                        "comments": "A test for metadata",
                        "count": {
                            "singular": 0,
                            "plurals": [0],
                        },
                    }
                ),
                {
                    "version": "0.2.0",
                    "language": "fr-FR",
                    "location": [("file.py", 132)],
                    "flags": ["python-format"],
                    "comments": "A test for metadata",
                    "count": {
                        "singular": 0,
                        "plurals": [0],
                    },
                },
        ),
    ],
)
def test_message_add_metadata(dictionary, expected) -> None:
    message = Message("1001", "A test for metadata")
    message.add_metadata(dictionary)
    control = message.metadata.to_dict()
    assert control == expected


@pytest.mark.parametrize(
    "dictionary, expected",
    [
        (
                {
                    "version": "0.2.0",
                    "location": [("file.py", 132)],
                    "flags": ["python-format"],
                    "comments": "A test for metadata",
                    "count": {
                        "singular": 0,
                        "plurals": [0],
                    },
                },
                "The path ['language'] is not a present key in the metadata dictionary",
        ),
        (
                {
                    "version": "0.2.0",
                    "language": "fr-FR",
                    "location": [("file.py", 132)],
                    "flags": ["python-format"],
                    "comments": "A test for metadata",
                    "count": {
                        "plurals": [0],
                    },
                },
                "The path ['count', 'singular'] is not a present key in the metadata dictionary",
        ),
    ],
)
def test_message_add_metadata_failed(dictionary, expected) -> None:
    message = Message("1001", "A test for metadata")
    with pytest.raises(ValueError, match=re.escape(expected)):
        message.add_metadata(dictionary)


@pytest.mark.parametrize(
    "key_or_path, value, key, expected",
    [
        ("version", "0.2.0", "version", "0.2.0"),
        (["location"], [("file.py", 132)], "location", [("file.py", 132)]),
        ("count", {"singular": 0, "plurals": [0]}, ["count", "singular"], 0),
        (
                ["count", "singular"],
                1,
                "count",
                StrictNestedDictionary({"singular": 1, "plurals": []}),
        ),
    ],
)
def test_message_add_metadata_key(key_or_path, value, key, expected) -> None:
    message = Message("1001", "A test for metadata")
    message.add_metadata(key_or_path, value)
    assert message.metadata[key] == expected


@pytest.mark.parametrize(
    "key_or_path, value, expected",
    [
        (
                "version",
                None,
                "Value of 'version' cannot be None when setting a specific metadata key",
        ),
        (
                ["count", "plurals"],
                None,
                "Value of '['count', 'plurals']' cannot be None when setting a specific metadata key",
        ),
        (
                "versions",
                0,
                "The key 'versions' is not a present key in the metadata dictionary",
        ),
        (
                ["versions"],
                0,
                "The path ['versions'] is not a present key in the metadata dictionary",
        ),
        (
                ["count", "plural"],
                1,
                "The path ['count', 'plural'] is not a present key in the metadata dictionary",
        ),
    ],
)
def test_message_add_metadata_key_failed(key_or_path, value, expected) -> None:
    message = Message("1001", "A test for metadata")
    with pytest.raises(ValueError, match=re.escape(expected)):
        message.add_metadata(key_or_path, value)


# 4 Testing updates

# 4.1 Testing messages

@pytest.mark.parametrize("options, expected", [
    ({"translation": None},
     [("translation", "A test for update message")]),
    ({"translation": ""},
     [("translation", "A test for update message")]),
    ({"translation": "Another translation"},
     [("translation", "Another translation")]),
    ({"translation": "Hello", "plural_forms": {1: "Hi everybody", 2: "Hi everyone"}},
     [("translation", "Hello"),
      ("plural_forms", {1: "Hi everybody", 2: "Hi everyone"})]),
    ({"translation": "Good morning {name}",
      "plural_forms": {1: "Hi everybody", 2: "Hi everyone"},
      "alternatives": {1: "Good afternoon {name}", 2: "Good evening {name}"}},
     [("translation", "Good morning {name}"),
      ("plural_forms", {1: "Hi everybody", 2: "Hi everyone"}),
      ("alternatives", {1: "Good afternoon {name}", 2: "Good evening {name}"})]),
    ({"translation": "Good morning {name}",
      "plural_forms": {1: "Good morning everybody", 2: "Good morning everyone"},
      "alternatives": {1: "Good afternoon {name}", 2: "Good evening {name}"},
      "alternative_plural_forms": {
          1: {1: "Good afternoon everybody", 2: "Good afternoon everyone"},
          2: {1: "Good evening everybody", 2: "Good evening everyone"}
      }},
     [("translation", "Good morning {name}"),
      ("plural_forms", {1: "Good morning everybody", 2: "Good morning everyone"}),
      ("alternatives", {1: "Good afternoon {name}", 2: "Good evening {name}"}),
      ("alternative_plural_forms", StrictNestedDictionary({
          1: {1: "Good afternoon everybody", 2: "Good afternoon everyone"},
          2: {1: "Good evening everybody", 2: "Good evening everyone"}
      }))])
])
def test_message_update_message(options, expected) -> None:
    message = Message("1001", "A test for update message")
    message.update_message(**options)
    for (attr, value) in expected:
        assert getattr(message, attr) == value

@pytest.mark.parametrize("options, expected", [
    ({"translation": "Hello", "plural_forms": {2: "Hi everybody", 3: "Hi everyone"}},
     "The 'plural_forms' value is malformed"),
    ({"translation": "Good morning {name}",
      "plural_forms": {1: "Hi everybody", 2: "Hi everyone"},
      "alternatives": {0: "Good afternoon {name}", 2: "Good evening {name}"}},
     "The 'alternatives' value is malformed"),
    ({"translation": "Good morning {name}",
      "plural_forms": {1: "Good morning everybody", 2: "Good morning everyone"},
      "alternatives": {1: "Good afternoon {name}", 2: "Good evening {name}"},
      "alternative_plural_forms": {
          1: {1: "Good afternoon everybody", 2: "Good afternoon everyone"},
          3: {1: "Good evening everybody", 2: "Good evening everyone"}
      }},
     "The 'alternative_plural_forms' value is malformed")
])
def test_message_update_message_failed(options, expected) -> None:
    message = Message("1001", "A test for metadata")
    with pytest.raises(ValueError, match=re.escape(expected)):
        message.update_message(**options)
# 4.2 Testing translations

# 4.3 Testing components

# 4.4 Testing metadata

# 5 Testing delete

# 5 Testing updates

# 5.1 Testing messages

# 5.2 Testing translations

# 5.3 Testing components

# 5.4 Testing metadata

# 6 Testing components formats


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
    assert message.format(option=1, name="John") == "Hi, John!"

    # Test formatting a plural form
    assert message.format(token=1, name="user", count=5) == "Hello, 5 users!"

    # Test formatting an alternative plural form
    assert message.format(option=1, token=1, name="user", count=3) == "Hi, 3 users!"

    # Test missing variable
    with pytest.raises(KeyError):
        message.format()

    # 7 Testing conversions
