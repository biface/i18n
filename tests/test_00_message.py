"""
Test module for the Message class in the formatter module.
"""

import re

import pytest
from ndict_tools import StrictNestedDictionary

from i18n_tools.models import Message


@pytest.fixture
def fr_message():
    return Message(
        id="1000",
        default="Bonjour",
        options={
            1: "Bonjour Mme {name}",
            2: "Bonjour M. {name}",
        },
        default_plurals={1: "Bonjour à tous", 2: "Bonjour tout le monde"},
        options_plurals={
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
        id="1000",
        default="Hello",
        options={
            1: "Hello {name}",
            2: "Hello {name}",
        },
        default_plurals={1: "Hi everybody", 2: "Hi everyone"},
        options_plurals={
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
    return Message(id="1000", default="")


@pytest.fixture(scope="module")
def empty_module_message():
    return Message(
        id="1000",
        default="",
    )


# 1. Testing attributes


class TestMessageCreation:

    @pytest.mark.parametrize(
        "fixture_name", ["fr_message", "en_message", "empty_message"]
    )
    def test_id(self, fixture_name, request):
        message = request.getfixturevalue(fixture_name)
        assert message.id == "1000"

    @pytest.mark.parametrize(
        "fixture_name, expect",
        [("fr_message", "Bonjour"), ("en_message", "Hello"), ("empty_message", "")],
    )
    def test_default(self, fixture_name, expect, request):
        message = request.getfixturevalue(fixture_name)
        assert message.default == expect

    @pytest.mark.parametrize(
        "fixture_name, loc, expect",
        [
            ("fr_message", 1, "Bonjour Mme {name}"),
            ("en_message", 1, "Hello {name}"),
            ("fr_message", 2, "Bonjour M. {name}"),
            ("en_message", 2, "Hello {name}"),
        ],
    )
    def test_options(self, fixture_name, loc, expect, request):
        message = request.getfixturevalue(fixture_name)
        assert message.options[loc] == expect

    def test_options_empty(self, empty_message):
        assert empty_message.options == {}

    @pytest.mark.parametrize(
        "fixture_name, loc, expect",
        [
            ("fr_message", 1, "Bonjour à tous"),
            ("en_message", 1, "Hi everybody"),
            ("fr_message", 2, "Bonjour tout le monde"),
            ("en_message", 2, "Hi everyone"),
        ],
    )
    def test_default_forms(self, fixture_name, loc, expect, request):
        message = request.getfixturevalue(fixture_name)
        assert message.default_plurals[loc] == expect

    def test_plural_forms_empty(self, empty_message):
        assert empty_message.default_plurals == {}

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
        assert message.options_plurals[[loc, index]] == expect

    def test_alternative_plural_forms_empty(self, empty_message):
        assert empty_message.options_plurals == {}

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
        Message("1001", "A failed", options={2: "Failed index"})


# 2. Test access to data

# 2.1 Testing main translations


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
def test_message_get_main(fixture_name, expect, request) -> None:
    message = request.getfixturevalue(fixture_name)
    assert message.get_main() == expect
    assert message.default == expect[0]
    assert message.get_main()[0] == expect[0]


@pytest.mark.parametrize(
    "fixture_name, expect",
    [
        ("fr_message", ["Bonjour à tous", "Bonjour tout le monde"]),
        ("en_message", ["Hi everybody", "Hi everyone"]),
        ("empty_message", []),
    ],
)
def test_message_get_main_plurals(fixture_name, expect, request) -> None:
    message = request.getfixturevalue(fixture_name)
    assert message.get_main_plurals() == expect


# 2.2 Testing  variant translations


@pytest.mark.parametrize(
    "fixture_name, location, expect",
    [
        ("fr_message", 1, ["Bonjour Mme {name}", "Bonjour Mesdames", "Mesdames"]),
        ("fr_message", 2, ["Bonjour M. {name}", "Bonjour Messieurs", "Messieurs"]),
        ("en_message", 1, ["Hello {name}", "Hi everybody", "Ladies"]),
        ("en_message", 2, ["Hello {name}", "Hi everyone", "Gentlemen"]),
    ],
)
def test_message_get_variant(fixture_name, location, expect, request) -> None:
    message = request.getfixturevalue(fixture_name)
    assert message.get_variant(location) == expect


@pytest.mark.parametrize(
    "fixture_name, location, expect",
    [
        ("fr_message", 5, "Alternative translation at index 5 not found"),
        ("en_message", 6, "Alternative translation at index 6 not found"),
        ("en_message", 3, "Alternative translation at index 3 not found"),
        ("fr_message", 4, "Alternative translation at index 4 not found"),
    ],
)
def test_message_get_variant_failed(fixture_name, location, expect, request) -> None:
    message = request.getfixturevalue(fixture_name)
    with pytest.raises(IndexError, match=re.escape(expect)):
        assert message.get_variant(location) == ""


@pytest.mark.parametrize(
    "fixture_name, option, expected",
    [
        ("fr_message", 1, ["Bonjour Mesdames", "Mesdames"]),
        ("en_message", 2, ["Hi everyone", "Gentlemen"]),
        ("en_message", 1, ["Hi everybody", "Ladies"]),
        ("fr_message", 2, ["Bonjour Messieurs", "Messieurs"]),
    ],
)
def test_message_get_variant_plurals(fixture_name, option, expected, request) -> None:
    message = request.getfixturevalue(fixture_name)
    assert message.get_variant_plurals(option) == expected


@pytest.mark.parametrize(
    "fixture_name, option, expected",
    [
        ("fr_message", 0, "Alternative translation at index 0 is out of range"),
        ("en_message", -1, "Alternative translation at index -1 is out of range"),
        ("en_message", 3, "Alternative translation at index 3 is out of range"),
        ("fr_message", 4, "Alternative translation at index 4 is out of range"),
    ],
)
def test_message_get_variant_plurals_failed(
    fixture_name, option, expected, request
) -> None:
    message = request.getfixturevalue(fixture_name)
    with pytest.raises(IndexError, match=re.escape(expected)):
        assert message.get_variant_plurals(option) == expected


# 2.4 Testing components


@pytest.mark.parametrize(
    "fixture_name, expect",
    [("fr_message", "Bonjour"), ("en_message", "Hello"), ("empty_message", "")],
)
def test_message_get_main_segment(fixture_name, expect, request) -> None:
    message = request.getfixturevalue(fixture_name)
    assert message.get_main_segment() == expect


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
def test_message_get_main_segment_token(fixture_name, token, expect, request) -> None:
    message = request.getfixturevalue(fixture_name)
    assert message.get_main_segment(token) == expect


@pytest.mark.parametrize(
    "fixture_name, token, expect",
    [
        ("fr_message", 4, "Segment location '4' is out of range"),
        ("en_message", -1, "Segment location '-1' is out of range"),
        ("empty_message", 1, "Segment location '1' is out of range"),
    ],
)
def test_message_get_main_segment_token_failed(
    fixture_name, token, expect, request
) -> None:
    message = request.getfixturevalue(fixture_name)
    with pytest.raises(IndexError, match=re.escape(expect)):
        message.get_main_segment(token)


@pytest.mark.parametrize(
    "fixture_name, expected",
    [
        ("fr_message", "Bonjour Mme {name}"),
        ("en_message", "Hello {name}"),
    ],
)
def test_message__get_variant_segment(fixture_name, expected, request) -> None:
    message = request.getfixturevalue(fixture_name)
    assert message.get_variant_segment() == expected


@pytest.mark.parametrize(
    "fixture_name, option, token, expected",
    [
        ("fr_message", 1, 0, "Bonjour Mme {name}"),
        ("fr_message", 2, 0, "Bonjour M. {name}"),
        ("en_message", 1, 0, "Hello {name}"),
        ("en_message", 2, 0, "Hello {name}"),
        ("fr_message", 1, 1, "Bonjour Mesdames"),
        ("fr_message", 2, 1, "Bonjour Messieurs"),
        ("en_message", 1, 1, "Hi everybody"),
        ("en_message", 2, 1, "Hi everyone"),
        ("fr_message", 1, 2, "Mesdames"),
        ("fr_message", 2, 2, "Messieurs"),
        ("en_message", 1, 2, "Ladies"),
        ("en_message", 2, 2, "Gentlemen"),
    ],
)
def test_message_get_variant_segment_token(
    fixture_name, option, token, expected, request
) -> None:
    message = request.getfixturevalue(fixture_name)
    assert message.get_variant_segment(option, token) == expected


@pytest.mark.parametrize(
    "fixture_name, option, token, expected",
    [
        ("empty_message", 1, 0, "Alternative translation at index 1 not found"),
        ("fr_message", 3, 0, "Alternative translation at index 3 not found"),
        ("en_message", 0, 0, "Alternative translation at index 0 not found"),
        (
            "fr_message",
            1,
            -1,
            "Segment location '-1' of variant option '1' is out of range",
        ),
        (
            "en_message",
            1,
            4,
            "Segment location '4' of variant option '1' is out of range",
        ),
    ],
)
def test_message_get_options_segment_failed(
    fixture_name, option, token, expected, request
) -> None:
    message = request.getfixturevalue(fixture_name)
    with pytest.raises(IndexError, match=re.escape(expected)):
        message.get_variant_segment(option, token)


@pytest.mark.parametrize(
    "fixture_name, source, parameters, expected",
    [
        ("fr_message", "main", {}, "Bonjour"),
        ("en_message", "main", {}, "Hello"),
        ("empty_message", "main", {}, ""),
        (
            "fr_message",
            "main",
            {
                "token": 0,
            },
            "Bonjour",
        ),
        (
            "en_message",
            "main",
            {
                "token": 0,
            },
            "Hello",
        ),
        (
            "empty_message",
            "main",
            {
                "token": 0,
            },
            "",
        ),
        ("fr_message", "main", {"token": 1}, "Bonjour à tous"),
        ("en_message", "main", {"token": 1}, "Hi everybody"),
        ("fr_message", "main", {"token": 2}, "Bonjour tout le monde"),
        ("en_message", "main", {"token": 2}, "Hi everyone"),
        ("fr_message", "variant", {}, "Bonjour Mme {name}"),
        ("en_message", "variant", {}, "Hello {name}"),
        ("fr_message", "variant", {"option": 1, "token": 0}, "Bonjour Mme {name}"),
        ("fr_message", "variant", {"option": 2, "token": 0}, "Bonjour M. {name}"),
        ("en_message", "variant", {"option": 1, "token": 0}, "Hello {name}"),
        ("en_message", "variant", {"option": 2, "token": 0}, "Hello {name}"),
        ("fr_message", "variant", {"option": 1, "token": 1}, "Bonjour Mesdames"),
        ("fr_message", "variant", {"option": 2, "token": 1}, "Bonjour Messieurs"),
        ("en_message", "variant", {"option": 1, "token": 1}, "Hi everybody"),
        ("en_message", "variant", {"option": 2, "token": 1}, "Hi everyone"),
        ("fr_message", "variant", {"option": 1, "token": 2}, "Mesdames"),
        ("fr_message", "variant", {"option": 2, "token": 2}, "Messieurs"),
        ("en_message", "variant", {"option": 1, "token": 2}, "Ladies"),
        ("en_message", "variant", {"option": 2, "token": 2}, "Gentlemen"),
        # Default token = 0
        ("fr_message", "variant", {"option": 1}, "Bonjour Mme {name}"),
        ("fr_message", "variant", {"option": 2}, "Bonjour M. {name}"),
        ("en_message", "variant", {"option": 1}, "Hello {name}"),
        ("en_message", "variant", {"option": 2}, "Hello {name}"),
        # Default option = 1
        ("fr_message", "variant", {"token": 0}, "Bonjour Mme {name}"),
        ("en_message", "variant", {"token": 0}, "Hello {name}"),
        ("fr_message", "variant", {"token": 1}, "Bonjour Mesdames"),
        ("en_message", "variant", {"token": 1}, "Hi everybody"),
        ("fr_message", "variant", {"token": 2}, "Mesdames"),
        ("en_message", "variant", {"token": 2}, "Ladies"),
    ],
)
def test_message_get_segment(
    fixture_name, source, parameters, expected, request
) -> None:
    message = request.getfixturevalue(fixture_name)
    parameters["source"] = source
    assert message.get_segment(**parameters) == expected


@pytest.mark.parametrize(
    "fixture_name, source, parameters, expected",
    [
        (
            "empty_message",
            "variant",
            {"option": 1, "token": 0},
            "Alternative translation at index 1 not found",
        ),
        (
            "fr_message",
            "variant",
            {"option": 3, "token": 0},
            "Alternative translation at index 3 not found",
        ),
        (
            "en_message",
            "variant",
            {"option": 0, "token": 0},
            "Alternative translation at index 0 not found",
        ),
        (
            "fr_message",
            "variant",
            {"option": 1, "token": -1},
            "Segment location '-1' of variant option '1' is out of range",
        ),
        (
            "en_message",
            "variant",
            {"option": 1, "token": 4},
            "Segment location '4' of variant option '1' is out of range",
        ),
        ("fr_message", "main", {"token": 4}, "Segment location '4' is out of range"),
        ("en_message", "main", {"token": -1}, "Segment location '-1' is out of range"),
        ("empty_message", "main", {"token": 1}, "Segment location '1' is out of range"),
        (
            "empty_message",
            "alternative",
            {},
            "The source 'alternative' is not defined : ['main', 'variant']",
        ),
    ],
)
def test_message_get_segment_failed(
    fixture_name, source, parameters, expected, request
) -> None:
    message = request.getfixturevalue(fixture_name)
    parameters["source"] = source
    with pytest.raises((KeyError, IndexError), match=re.escape(expected)):
        message.get_segment(**parameters)


# 2.5 Testing metadata


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
        ("empty_message", {"default": "Hello"}, [("default", "Hello")]),
        (
            "empty_message",
            {"default": "Hello", "options": {1: "Bonjour Mme {name}"}},
            [("default", "Hello"), ("options", {1: "Bonjour Mme {name}"})],
        ),
        (
            "empty_message",
            {
                "default": "Hello",
                "options": {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"},
            },
            [
                ("default", "Hello"),
                ("options", {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"}),
            ],
        ),
        (
            "empty_message",
            {
                "default": "Hello",
                "options": {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"},
                "default_plurals": {1: "Bonjour tout le monde"},
            },
            [
                ("default", "Hello"),
                ("options", {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"}),
                ("default_plurals", {1: "Bonjour tout le monde"}),
            ],
        ),
        (
            "empty_message",
            {
                "default": "Hello",
                "options": {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"},
                "default_plurals": {1: "Bonjour tout le monde", 2: "Bonjour à tous"},
            },
            [
                ("default", "Hello"),
                ("options", {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"}),
                ("default_plurals", {1: "Bonjour tout le monde", 2: "Bonjour à tous"}),
            ],
        ),
        (
            "empty_message",
            {
                "default": "Hello",
                "options": {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"},
                "default_plurals": {1: "Bonjour tout le monde", 2: "Bonjour à tous"},
                "options_plurals": {
                    1: {1: "Bonjour Mesdames"},
                },
            },
            [
                ("default", "Hello"),
                ("options", {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"}),
                ("default_plurals", {1: "Bonjour tout le monde", 2: "Bonjour à tous"}),
                (
                    "options_plurals",
                    {
                        1: {1: "Bonjour Mesdames"},
                    },
                ),
            ],
        ),
        (
            "empty_message",
            {
                "default": "Hello",
                "options": {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"},
                "default_plurals": {1: "Bonjour tout le monde", 2: "Bonjour à tous"},
                "options_plurals": {
                    1: {1: "Bonjour Mesdames"},
                    2: {1: "Bonjour Messieurs"},
                },
            },
            [
                ("default", "Hello"),
                ("options", {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"}),
                ("default_plurals", {1: "Bonjour tout le monde", 2: "Bonjour à tous"}),
                (
                    "options_plurals",
                    {1: {1: "Bonjour Mesdames"}, 2: {1: "Bonjour Messieurs"}},
                ),
            ],
        ),
        (
            "empty_message",
            {
                "default": "Hello",
                "options": {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"},
                "default_plurals": {1: "Bonjour tout le monde", 2: "Bonjour à tous"},
                "options_plurals": {
                    1: {1: "Bonjour Mesdames", 2: "Mesdames"},
                    2: {1: "Bonjour Messieurs", 2: "Messieurs"},
                },
            },
            [
                ("default", "Hello"),
                ("options", {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"}),
                ("default_plurals", {1: "Bonjour tout le monde", 2: "Bonjour à tous"}),
                (
                    "options_plurals",
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
            {"options": "Hello"},
            "At least one translation is required",
        ),
        (
            "fr_message",
            {"options": {1: "Bonjour Mme {name}"}},
            "At least one translation is required",
        ),
        (
            "empty_message",
            {"default": "Hello", "options": {2: "Bonjour Mme {name}"}},
            "The options value is malformed",
        ),
        (
            "empty_message",
            {
                "default": "Hello",
                "options": {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"},
                "default_plurals": {2: "Bonjour tout le monde"},
            },
            "The default_plurals value is malformed",
        ),
        (
            "empty_message",
            {
                "default": "Hello",
                "options": {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"},
                "default_plurals": {1: "Bonjour tout le monde", 2: "Bonjour à tous"},
                "options_plurals": {
                    1: {1: "Bonjour Mesdames", 2: "Mesdames"},
                    3: {1: "Bonjour Messieurs", 2: "Messieurs"},
                },
            },
            "The options_plurals value is malformed",
        ),
    ],
)
def test_message_add_message_failed(fixture_name, options, expected, request) -> None:
    message = request.getfixturevalue(fixture_name)
    with pytest.raises(ValueError, match=re.escape(expected)):
        message.add_message(**options)


# 3.2 Testing main translation


@pytest.mark.parametrize(
    "fixture_name, translation, expected",
    [
        ("empty_message", ["Hello"], ("Hello", {}, 1, [0])),
        (
            "empty_message",
            ["Hello", "Hi everybody"],
            ("Hello", {1: "Hi everybody"}, 1, [1]),
        ),
        (
            "empty_message",
            ["Hello", "Hi everybody", "Hi everyone"],
            ("Hello", {1: "Hi everybody", 2: "Hi everyone"}, 1, [2]),
        ),
        ("empty_message", {"default": "Hello"}, ("Hello", {}, 1, [0])),
        (
            "empty_message",
            {"default": "Hello", "default_plurals": {1: "Hi everybody"}},
            ("Hello", {1: "Hi everybody"}, 1, [1]),
        ),
        (
            "empty_message",
            {
                "default": "Hello",
                "default_plurals": {1: "Hi everybody", 2: "Hi everyone"},
            },
            ("Hello", {1: "Hi everybody", 2: "Hi everyone"}, 1, [2]),
        ),
    ],
)
def test_message_add_main(fixture_name, translation, expected, request) -> None:
    message = request.getfixturevalue(fixture_name)
    if isinstance(translation, dict):
        message.add_main(**translation)
    else:
        message.add_main(translation)
    assert message.default == expected[0]
    assert message.default_plurals == expected[1]
    assert message.metadata[["count", "singular"]] == expected[2]
    assert message.metadata[["count", "plurals"]] == expected[3]


@pytest.mark.parametrize(
    "fixture_name, translation, expected",
    [
        ("empty_message", None, "No translation specified"),
        (
            "empty_message",
            [""],
            "Singular of translation is required and cannot be None or empty : ''",
        ),
        (
            "empty_message",
            {"default": None},
            "Singular of translation is required and cannot be None or empty : 'None'",
        ),
        (
            "empty_message",
            {"default": ""},
            "Singular of translation is required and cannot be None or empty : ''",
        ),
        (
            "empty_message",
            {"default": "Hello", "default_plurals": {2: "Hi everybody"}},
            "Plural forms is malformed : {2: 'Hi everybody'}",
        ),
    ],
)
def test_message_add_main_failed(fixture_name, translation, expected, request) -> None:
    message = request.getfixturevalue(fixture_name)
    with pytest.raises(ValueError, match=re.escape(expected)):
        if isinstance(translation, dict):
            message.add_main(**translation)
        else:
            message.add_main(translation)


# 3.3 Testing variant translation


@pytest.mark.parametrize(
    "fixture_name, translation, expected",
    [
        ("empty_message", ["Hello {name}"], ({1: "Hello {name}"}, {1: {}}, 2, [2, 0])),
        (
            "empty_message",
            {"options": "Hello {name}"},
            ({1: "Hello {name}"}, {1: {}}, 2, [2, 0]),
        ),
        (
            "empty_message",
            ["Hello {name}", "Hi everybody"],
            ({1: "Hello {name}"}, {1: {1: "Hi everybody"}}, 2, [2, 1]),
        ),
        (
            "empty_message",
            {
                "options": "Hello {name}",
                "options_plurals": ["Hi everybody"],
            },
            ({1: "Hello {name}"}, {1: {1: "Hi everybody"}}, 2, [2, 1]),
        ),
        (
            "empty_message",
            {
                "options": "Hello {name}",
                "options_plurals": {1: "Hi everybody"},
            },
            ({1: "Hello {name}"}, {1: {1: "Hi everybody"}}, 2, [2, 1]),
        ),
        (
            "empty_message",
            ["Hello {name}", "Hi everybody", "Hi everyone"],
            (
                {1: "Hello {name}"},
                {1: {1: "Hi everybody", 2: "Hi everyone"}},
                2,
                [2, 2],
            ),
        ),
        (
            "empty_message",
            {
                "options": "Hello {name}",
                "options_plurals": ["Hi everybody", "Hi everyone"],
            },
            (
                {1: "Hello {name}"},
                {1: {1: "Hi everybody", 2: "Hi everyone"}},
                2,
                [2, 2],
            ),
        ),
        (
            "empty_message",
            {
                "options": "Hello {name}",
                "options_plurals": {1: "Hi everybody", 2: "Hi everyone"},
            },
            (
                {1: "Hello {name}"},
                {1: {1: "Hi everybody", 2: "Hi everyone"}},
                2,
                [2, 2],
            ),
        ),
        (
            "fr_message",
            ["Cher {name}", "Chères et chers collègues", "Chers vous tous"],
            (
                {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}", 3: "Cher {name}"},
                {
                    1: {1: "Bonjour Mesdames", 2: "Mesdames"},
                    2: {1: "Bonjour Messieurs", 2: "Messieurs"},
                    3: {1: "Chères et chers collègues", 2: "Chers vous tous"},
                },
                4,
                [2, 2, 2, 2],
            ),
        ),
        (
            "fr_message",
            {
                "options": "Cher {name}",
                "options_plurals": ["Chères et chers collègues", "Chers vous tous"],
            },
            (
                {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}", 3: "Cher {name}"},
                {
                    1: {1: "Bonjour Mesdames", 2: "Mesdames"},
                    2: {1: "Bonjour Messieurs", 2: "Messieurs"},
                    3: {1: "Chères et chers collègues", 2: "Chers vous tous"},
                },
                4,
                [2, 2, 2, 2],
            ),
        ),
        (
            "fr_message",
            {
                "options": "Cher {name}",
                "options_plurals": {
                    1: "Chères et chers collègues",
                    2: "Chers vous tous",
                },
            },
            (
                {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}", 3: "Cher {name}"},
                {
                    1: {1: "Bonjour Mesdames", 2: "Mesdames"},
                    2: {1: "Bonjour Messieurs", 2: "Messieurs"},
                    3: {1: "Chères et chers collègues", 2: "Chers vous tous"},
                },
                4,
                [2, 2, 2, 2],
            ),
        ),
        (
            "fr_message",
            ["Cher {name}", "Chères et chers collègues"],
            (
                {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}", 3: "Cher {name}"},
                {
                    1: {1: "Bonjour Mesdames", 2: "Mesdames"},
                    2: {1: "Bonjour Messieurs", 2: "Messieurs"},
                    3: {1: "Chères et chers collègues"},
                },
                4,
                [2, 2, 2, 1],
            ),
        ),
        (
            "fr_message",
            {
                "options": "Cher {name}",
                "options_plurals": ["Chères et chers collègues"],
            },
            (
                {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}", 3: "Cher {name}"},
                {
                    1: {1: "Bonjour Mesdames", 2: "Mesdames"},
                    2: {1: "Bonjour Messieurs", 2: "Messieurs"},
                    3: {1: "Chères et chers collègues"},
                },
                4,
                [2, 2, 2, 1],
            ),
        ),
        (
            "fr_message",
            {
                "options": "Cher {name}",
                "options_plurals": {1: "Chères et chers collègues"},
            },
            (
                {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}", 3: "Cher {name}"},
                {
                    1: {1: "Bonjour Mesdames", 2: "Mesdames"},
                    2: {1: "Bonjour Messieurs", 2: "Messieurs"},
                    3: {1: "Chères et chers collègues"},
                },
                4,
                [2, 2, 2, 1],
            ),
        ),
    ],
)
def test_message_add_variant(fixture_name, translation, expected, request) -> None:
    message = request.getfixturevalue(fixture_name)
    if message.default == "":
        message.add_main(["Hello", "Hi everybody", "Hi everyone"])
    if isinstance(translation, dict):
        message.add_variant(**translation)
    else:
        message.add_variant(translation)
    assert message.options == expected[0]
    assert message.options_plurals.to_dict() == expected[1]
    assert message.metadata[["count", "singular"]] == expected[2]
    assert message.metadata[["count", "plurals"]] == expected[3]


@pytest.mark.parametrize(
    "fixture_name, translation, expected",
    [
        ("en_message", None, "No variant translation is specified"),
        (
            "empty_message",
            ["Hello {name}"],
            "Cannot add an alternative translation, there presently is no translation",
        ),
        (
            "fr_message",
            [None, "Chères et chers collègues", "Chers vous tous"],
            "Singular of a variant is required and cannot be None or empty : 'None'",
        ),
        (
            "fr_message",
            ["", "Chères et chers collègues", "Chers vous tous"],
            "Singular of a variant is required and cannot be None or empty : ''",
        ),
        (
            "fr_message",
            {
                "options": None,
                "options_plurals": ["Chères et chers collègues", "Chers vous tous"],
            },
            "Singular of a variant is required and cannot be None or empty : 'None'",
        ),
        (
            "fr_message",
            {
                "options": "",
                "options_plurals": {
                    1: "Chères et chers collègues",
                    2: "Chers vous tous",
                },
            },
            "Singular of a variant is required and cannot be None or empty : ''",
        ),
        (
            "fr_message",
            {
                "options": "Cher {name}",
                "options_plurals": ("Chères et chers collègues", "Chers vous tous"),
            },
            "Plural of this variant is malformed : ('Chères et chers collègues', 'Chers vous tous')",
        ),
        (
            "fr_message",
            {
                "options": "Cher {name}",
                "options_plurals": {2: "Chères et chers collègues"},
            },
            "Plural of this variant is malformed : {2: 'Chères et chers collègues'}",
        ),
    ],
)
def test_message_add_variant_failed(
    fixture_name, translation, expected, request
) -> None:
    message = request.getfixturevalue(fixture_name)
    with pytest.raises(ValueError, match=re.escape(expected)):
        if isinstance(translation, dict):
            message.add_variant(**translation)
        else:
            message.add_variant(translation)


# 3.4 Testing components


@pytest.mark.parametrize(
    "fixture_name, segment, token, expected",
    [
        ("empty_message", "Good morning", 0, "Good morning"),
        ("en_message", "Good morning", 3, "Good morning"),
    ],
)
def test_message_add_main_segment(
    fixture_name, segment, token, expected, request
) -> None:
    message = request.getfixturevalue(fixture_name)
    message.add_main_segment(segment, token)
    assert message.get_main()[token] == expected


@pytest.mark.parametrize(
    "fixture_name, segment, token, expected",
    [
        (
            "empty_message",
            "Good morning",
            -1,
            "Plural form index (-1) is not in a valid range",
        ),
        (
            "en_message",
            "Good morning",
            4,
            "Plural form index (4) is not in a valid range",
        ),
        (
            "fr_message",
            "",
            0,
            "Singular of translation is required and cannot be None or empty : ''",
        ),
    ],
)
def test_message_add_main_segment_failed(
    fixture_name, segment, token, expected, request
) -> None:
    message = request.getfixturevalue(fixture_name)
    with pytest.raises(ValueError, match=re.escape(expected)):
        message.add_main_segment(segment, token)


@pytest.mark.parametrize("plural, expected", [
    ("Good morning everyone", {1:"Good morning everyone"}),
    ("Good morning all", {1:"Good morning everyone", 2: "Good morning all"})
])
def test_message_protected_add_default_plural_segment(empty_module_message, plural, expected) -> None:
    empty_module_message._add_default_plurals_segment(plural)
    assert empty_module_message.default_plurals == expected

def test_message_protected_add_default_plural_segment_failed(empty_module_message) -> None:
    with pytest.raises(ValueError, match=re.escape("Empty plural cannot be added")):
        empty_module_message._add_default_plurals_segment("")


@pytest.mark.parametrize(
    "fixture_name, segment, option, token, expected",
    [
        ("empty_module_message", "Good morning {name}", 1, 0, "Good morning {name}"),
        (
            "empty_module_message",
            "Good afternoon {name}",
            2,
            0,
            "Good afternoon {name}",
        ),
        ("empty_module_message", "Good morning guys", 1, 1, "Good morning guys"),
        ("empty_module_message", "Good morning all", 1, 2, "Good morning all"),
        ("empty_module_message", "Good afternoon guys", 2, 1, "Good afternoon guys"),
        ("empty_module_message", "Good afternoon all", 2, 2, "Good afternoon all"),
    ],
)
def test_message_add_variant_segment(
    fixture_name, segment, option, token, expected, request
) -> None:
    message = request.getfixturevalue(fixture_name)
    message.add_variant_segment(segment, option, token)
    assert message.get_variant(option)[token] == expected


@pytest.mark.parametrize(
    "fixture_name, segment, option, token, expected",
    [
        (
            "empty_message",
            "Good morning {name}",
            0,
            0,
            "Option index (0) is not in a valid range",
        ),
        (
            "en_message",
            "Good morning {name}",
            1,
            -1,
            "Segment index (-1) in options (1) is not in a valid range",
        ),
        (
            "en_message",
            "Good afternoon {name}",
            4,
            1,
            "Option index (4) is not in a valid range",
        ),
    ],
)
def test_message_add_variant_segment(
    fixture_name, segment, option, token, expected, request
) -> None:
    message = request.getfixturevalue(fixture_name)
    with pytest.raises(IndexError, match=re.escape(expected)):
        message.add_variant_segment(segment, option, token)


@pytest.mark.parametrize(
    "segment, expected",
    [
        ("Good morning", [(1, "Good morning")]),
        ("Good morning {name}", [(1, "Good morning"), (2, "Good morning {name}")]),
    ],
)
def test_message_protected_add_options_segment(
    empty_module_message, segment, expected
) -> None:
    empty_module_message._add_options_segment(segment)
    for token, result in expected:
        assert empty_module_message.options[token] == result


@pytest.mark.parametrize(
    "fixture_message, segment, expected",
    [
        ("empty_message", "", "Option segment to be added cannot be empty"),
    ],
)
def test_message_protected_add_options_segment_failed(
    fixture_message, segment, expected, request
) -> None:
    message = request.getfixturevalue(fixture_message)
    with pytest.raises(ValueError, match=re.escape(expected)):
        message._add_options_segment(segment)


@pytest.mark.parametrize(
    "options, alt_index, additional, expected",
    [
        (
            {
                "default": "Good morning {name}",
                "options": {1: "Good afternoon Mme {name}"},
                "default_plurals": {1: "Good morning all", 2: "Good morning"},
            },
            2,
            "Good afternoon all",
            {2: {1: "Good afternoon all"}},
        ),
        (
            {
                "default": "Hello",
                "options": {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"},
                "default_plurals": {1: "Bonjour tout le monde", 2: "Bonjour à tous"},
            },
            1,
            "Bonjour Mesdames",
            {1: {1: "Bonjour Mesdames"}},
        ),
        (
            {
                "default": "Hello",
                "options": {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"},
                "default_plurals": {1: "Bonjour tout le monde", 2: "Bonjour à tous"},
                "options_plurals": {
                    1: {1: "Bonjour Mesdames"},
                },
            },
            2,
            "Bonjour Messieurs",
            {1: {1: "Bonjour Mesdames"}, 2: {1: "Bonjour Messieurs"}},
        ),
        (
            {
                "default": "Hello",
                "options": {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"},
                "default_plurals": {1: "Bonjour tout le monde", 2: "Bonjour à tous"},
                "options_plurals": {
                    1: {1: "Bonjour Mesdames"},
                    2: {1: "Bonjour Messieurs", 2: "Messieurs"},
                },
            },
            1,
            "Mesdames",
            {
                1: {1: "Bonjour Mesdames", 2: "Mesdames"},
                2: {1: "Bonjour Messieurs", 2: "Messieurs"},
            },
        ),
    ],
)
def test_message_add_options_plurals_segment(
    empty_message, options, alt_index, additional, expected
) -> None:
    message = empty_message
    message.add_message(**options)
    message._add_options_plurals_segment(additional, alt_index)
    assert message.options_plurals == expected


@pytest.mark.parametrize(
    "options, alt_index, additional, error, expected",
    [
        (
            {
                "default": "Hello",
                "options": {},
                "default_plurals": {},
            },
            0,
            "Bonjour Mesdames",
            IndexError,
            "Option index (0) is not in a valid range",
        ),
        (
            {
                "default": "Hello",
                "options": {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"},
                "default_plurals": {1: "Bonjour tout le monde", 2: "Bonjour à tous"},
                "options_plurals": {
                    1: {1: "Bonjour Mesdames"},
                },
            },
            4,
            "Bonjour Messieurs",
            IndexError,
            "Option index (4) is not in a valid range",
        ),
    ],
)
def test_message_add_options_plurals_segment_failed(
    empty_message, options, alt_index, additional, error, expected
) -> None:
    message = empty_message
    message.add_message(**options)
    with pytest.raises(error, match=re.escape(expected)):
        message._add_options_plurals_segment(additional, alt_index)


# 3.5 Testing metadata


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


@pytest.mark.parametrize(
    "options, expected",
    [
        ({"default": None}, [("default", "A test for update message")]),
        ({"default": ""}, [("default", "A test for update message")]),
        ({"default": "Another translation"}, [("default", "Another translation")]),
        (
            {
                "default": "Hello",
                "default_plurals": {1: "Hi everybody", 2: "Hi everyone"},
            },
            [
                ("default", "Hello"),
                ("default_plurals", {1: "Hi everybody", 2: "Hi everyone"}),
            ],
        ),
        (
            {
                "default": "Good morning {name}",
                "default_plurals": {1: "Hi everybody", 2: "Hi everyone"},
                "options": {1: "Good afternoon {name}", 2: "Good evening {name}"},
            },
            [
                ("default", "Good morning {name}"),
                ("default_plurals", {1: "Hi everybody", 2: "Hi everyone"}),
                ("options", {1: "Good afternoon {name}", 2: "Good evening {name}"}),
            ],
        ),
        (
            {
                "default": "Good morning {name}",
                "default_plurals": {
                    1: "Good morning everybody",
                    2: "Good morning everyone",
                },
                "options": {1: "Good afternoon {name}", 2: "Good evening {name}"},
                "options_plurals": {
                    1: {1: "Good afternoon everybody", 2: "Good afternoon everyone"},
                    2: {1: "Good evening everybody", 2: "Good evening everyone"},
                },
            },
            [
                ("default", "Good morning {name}"),
                (
                    "default_plurals",
                    {1: "Good morning everybody", 2: "Good morning everyone"},
                ),
                ("options", {1: "Good afternoon {name}", 2: "Good evening {name}"}),
                (
                    "options_plurals",
                    StrictNestedDictionary(
                        {
                            1: {
                                1: "Good afternoon everybody",
                                2: "Good afternoon everyone",
                            },
                            2: {
                                1: "Good evening everybody",
                                2: "Good evening everyone",
                            },
                        }
                    ),
                ),
            ],
        ),
    ],
)
def test_message_update_message(options, expected) -> None:
    message = Message("1001", "A test for update message")
    message.update_message(**options)
    for attr, value in expected:
        assert getattr(message, attr) == value


@pytest.mark.parametrize(
    "options, expected",
    [
        (
            {
                "default": "Hello",
                "default_plurals": {2: "Hi everybody", 3: "Hi everyone"},
            },
            "The 'default_plurals' value is malformed",
        ),
        (
            {
                "default": "Good morning {name}",
                "default_plurals": {1: "Hi everybody", 2: "Hi everyone"},
                "options": {0: "Good afternoon {name}", 2: "Good evening {name}"},
            },
            "The 'options' value is malformed",
        ),
        (
            {
                "default": "Good morning {name}",
                "default_plurals": {
                    1: "Good morning everybody",
                    2: "Good morning everyone",
                },
                "options": {1: "Good afternoon {name}", 2: "Good evening {name}"},
                "options_plurals": {
                    1: {1: "Good afternoon everybody", 2: "Good afternoon everyone"},
                    3: {1: "Good evening everybody", 2: "Good evening everyone"},
                },
            },
            "The 'options_plurals' value is malformed",
        ),
    ],
)
def test_message_update_message_failed(options, expected) -> None:
    message = Message("1001", "A test for metadata")
    with pytest.raises(ValueError, match=re.escape(expected)):
        message.update_message(**options)


# 4.2 Testing main translation


@pytest.mark.parametrize(
    "translation, expected",
    [
        (["Hello {name}"], [("default", "Hello {name}"), ("default_plurals", {})]),
        (
            ["Hello", "Hi everybody"],
            [("default", "Hello"), ("default_plurals", {1: "Hi everybody"})],
        ),
        (
            ["", "Hi everybody", "Hi everyone"],
            [
                ("default", "Hi"),
                ("default_plurals", {1: "Hi everybody", 2: "Hi everyone"}),
            ],
        ),
        (
            {"default": "Hello {name}"},
            [("default", "Hello {name}"), ("default_plurals", {})],
        ),
        (
            {"default": "Hello", "default_plurals": {1: "Hi everybody"}},
            [("default", "Hello"), ("default_plurals", {1: "Hi everybody"})],
        ),
        (
            {"default": "", "default_plurals": ["Hi everybody", "Hi everyone"]},
            [
                ("default", "Hi"),
                ("default_plurals", {1: "Hi everybody", 2: "Hi everyone"}),
            ],
        ),
        (
            {"default": "", "default_plurals": {1: "Hi everybody", 2: "Hi everyone"}},
            [
                ("default", "Hi"),
                ("default_plurals", {1: "Hi everybody", 2: "Hi everyone"}),
            ],
        ),
    ],
)
def test_message_update_main(translation, expected) -> None:
    message = Message("1001", "Hi")
    if isinstance(translation, dict):
        message.update_main(**translation)
    else:
        message.update_main(translation)
    for attr, value in expected:
        assert getattr(message, attr) == value


@pytest.mark.parametrize(
    "translation, expected",
    [
        (None, "No updates specified"),
        ({}, "No updates specified"),
        (
            {"default": "Hello", "default_plurals": {0: "Hi everybody"}},
            "plural translation context is malformed : {0: 'Hi everybody'}",
        ),
    ],
)
def test_message_update_main_failed(translation, expected) -> None:
    message = Message("1001", "Hi")
    with pytest.raises(ValueError, match=re.escape(expected)):
        if isinstance(translation, dict):
            message.update_main(**translation)
        else:
            message.update_main(translation)


# 4.3 Testing variant translation


@pytest.mark.parametrize(
    "fixture_message, option, translation, expected",
    [
        (
            "en_message",
            0,
            ["Hi {name}"],
            [
                ("default", "Hi {name}"),
                ("default_plurals", {1: "Hi everybody", 2: "Hi everyone"}),
            ],
        ),
        (
            "en_message",
            0,
            {"default": "Hi {name}"},
            [
                ("default", "Hi {name}"),
                ("default_plurals", {1: "Hi everybody", 2: "Hi everyone"}),
            ],
        ),
        (
            "fr_message",
            1,
            ["Chère Mme {name}"],
            [
                ("default", "Bonjour"),
                ("default_plurals", {1: "Bonjour à tous", 2: "Bonjour tout le monde"}),
                ("options", {1: "Chère Mme {name}", 2: "Bonjour M. {name}"}),
            ],
        ),
        (
            "fr_message",
            2,
            ["Cher M. {name}", "Chers Messieurs", "Chers tous"],
            [
                ("default", "Bonjour"),
                ("default_plurals", {1: "Bonjour à tous", 2: "Bonjour tout le monde"}),
                ("options", {1: "Bonjour Mme {name}", 2: "Cher M. {name}"}),
                (
                    "options_plurals",
                    StrictNestedDictionary(
                        {
                            1: {1: "Bonjour Mesdames", 2: "Mesdames"},
                            2: {1: "Chers Messieurs", 2: "Chers tous"},
                        }
                    ),
                ),
            ],
        ),
        (
            "fr_message",
            1,
            {"options": "Chère Mme {name}"},
            [
                ("default", "Bonjour"),
                ("default_plurals", {1: "Bonjour à tous", 2: "Bonjour tout le monde"}),
                ("options", {1: "Chère Mme {name}", 2: "Bonjour M. {name}"}),
            ],
        ),
        (
            "fr_message",
            2,
            {
                "options": "Cher M. {name}",
                "options_plurals": {1: "Chers Messieurs", 2: "Chers tous"},
            },
            [
                ("default", "Bonjour"),
                ("default_plurals", {1: "Bonjour à tous", 2: "Bonjour tout le monde"}),
                ("options", {1: "Bonjour Mme {name}", 2: "Cher M. {name}"}),
                (
                    "options_plurals",
                    StrictNestedDictionary(
                        {
                            1: {1: "Bonjour Mesdames", 2: "Mesdames"},
                            2: {1: "Chers Messieurs", 2: "Chers tous"},
                        }
                    ),
                ),
            ],
        ),
        (
            "fr_message",
            2,
            {
                "options": "Cher M. {name}",
                "options_plurals": ["Chers Messieurs", "Chers tous"],
            },
            [
                ("default", "Bonjour"),
                ("default_plurals", {1: "Bonjour à tous", 2: "Bonjour tout le monde"}),
                ("options", {1: "Bonjour Mme {name}", 2: "Cher M. {name}"}),
                (
                    "options_plurals",
                    StrictNestedDictionary(
                        {
                            1: {1: "Bonjour Mesdames", 2: "Mesdames"},
                            2: {1: "Chers Messieurs", 2: "Chers tous"},
                        }
                    ),
                ),
            ],
        ),
    ],
)
def test_message_update_variant(
    fixture_message, option, translation, expected, request
) -> None:
    message = request.getfixturevalue(fixture_message)
    if isinstance(translation, dict):
        message.update_variant(option, **translation)
    else:
        message.update_variant(option, translation)
    for attr, value in expected:
        assert getattr(message, attr) == value


@pytest.mark.parametrize(
    "fixture_message, option, translation, expected",
    [
        ("fr_message", 1, None, "No updates specified"),
        ("en_message", 4, ["Hi {name}"], "Option '4' out of range"),
        (
            "fr_message",
            2,
            {
                "alternative_translation": "Cher M. {name}",
                "options_plurals": {2: "Chers Messieurs", 3: "Chers tous"},
            },
            "Plural translation context is malformed : {2: 'Chers Messieurs', 3: 'Chers tous'}",
        ),
    ],
)
def test_message_update_variant_failed(
    fixture_message, option, translation, expected, request
) -> None:
    message = request.getfixturevalue(fixture_message)
    with pytest.raises((ValueError, IndexError), match=re.escape(expected)):
        if isinstance(translation, dict):
            message.update_variant(option, **translation)
        else:
            message.update_variant(option, translation)


# 4.4 Testing components

# 4.5 Testing metadata

# 5 Testing delete

# 5.1 Testing messages

# 5.2 Testing main translations

# 5.2 Testing variant translations

# 5.4 Testing components

# 5.5 Testing metadata

# 6 Testing components formats


def test_message_format():
    """Test formatting a message with variables."""
    message = Message(
        id="greeting",
        default="Hello, {name}!",
        options={1: "Hi, {name}!"},
        default_plurals={1: "Hello, {count} {name}s!"},
        options_plurals={1: {1: "Hi, {count} {name}s!"}},
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
