"""
Test module for the Message class in the models module.
"""

import re

import pytest
from ndict_tools import StrictNestedDictionary

from i18n_tools import __version__
from i18n_tools.models import Message


class TestMessageGet:
    @pytest.mark.parametrize(
        "fixture_name, expected_language",
        [("fr_message", "fr-FR"), ("en_message", "en"), ("empty_message", "")],
    )
    def test_message_get_id(self, fixture_name, expected_language, request) -> None:
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
    def test_message_get_main(self, fixture_name, expect, request) -> None:
        message = request.getfixturevalue(fixture_name)
        assert message.get_principal() == expect
        assert message.default == expect[0]
        assert message.get_principal()[0] == expect[0]

    @pytest.mark.parametrize(
        "fixture_name, expect",
        [
            ("fr_message", ["Bonjour à tous", "Bonjour tout le monde"]),
            ("en_message", ["Hi everybody", "Hi everyone"]),
            ("empty_message", []),
        ],
    )
    def test_message_get_main_plurals(self, fixture_name, expect, request) -> None:
        message = request.getfixturevalue(fixture_name)
        assert message.get_principal_plurals() == expect

    @pytest.mark.parametrize(
        "fixture_name, location, expect",
        [
            ("fr_message", 1, ["Bonjour Mme {name}", "Bonjour Mesdames", "Mesdames"]),
            ("fr_message", 2, ["Bonjour M. {name}", "Bonjour Messieurs", "Messieurs"]),
            ("en_message", 1, ["Hello {name}", "Hi everybody", "Ladies"]),
            ("en_message", 2, ["Hello {name}", "Hi everyone", "Gentlemen"]),
        ],
    )
    def test_message_get_variant(self, fixture_name, location, expect, request) -> None:
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
    def test_message_get_variant_failed(
        self, fixture_name, location, expect, request
    ) -> None:
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
    def test_message_get_variant_plurals(
        self, fixture_name, option, expected, request
    ) -> None:
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
        self, fixture_name, option, expected, request
    ) -> None:
        message = request.getfixturevalue(fixture_name)
        with pytest.raises(IndexError, match=re.escape(expected)):
            assert message.get_variant_plurals(option) == expected


class TestMessageGetSegment:
    @pytest.mark.parametrize(
        "fixture_name, expect",
        [("fr_message", "Bonjour"), ("en_message", "Hello"), ("empty_message", "")],
    )
    def test_message_get_main_segment(self, fixture_name, expect, request) -> None:
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
    def test_message_get_main_segment_token(
        self, fixture_name, token, expect, request
    ) -> None:
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
        self, fixture_name, token, expect, request
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
    def test_message__get_variant_segment(
        self, fixture_name, expected, request
    ) -> None:
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
        self, fixture_name, option, token, expected, request
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
        self, fixture_name, option, token, expected, request
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
        self, fixture_name, source, parameters, expected, request
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
            (
                "fr_message",
                "main",
                {"token": 4},
                "Segment location '4' is out of range",
            ),
            (
                "en_message",
                "main",
                {"token": -1},
                "Segment location '-1' is out of range",
            ),
            (
                "empty_message",
                "main",
                {"token": 1},
                "Segment location '1' is out of range",
            ),
            (
                "empty_message",
                "alternative",
                {},
                "The source 'alternative' is not defined : ['main', 'variant']",
            ),
        ],
    )
    def test_message_get_segment_failed(
        self, fixture_name, source, parameters, expected, request
    ) -> None:
        message = request.getfixturevalue(fixture_name)
        parameters["source"] = source
        with pytest.raises((KeyError, IndexError), match=re.escape(expected)):
            message.get_segment(**parameters)


class TestMessageGetMetadata:
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
                    "user_comments": ["In French, Greeting message to one or more..."],
                    "auto_comments": ["1000_000", "1000_001", "1000_02"],
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
                    "user_comments": [],
                    "auto_comments": [],
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
                    "user_comments": ["Greeting message to one or more..."],
                    "auto_comments": ["1000_000", "1000_001", "1000_02"],
                    "count": {"singular": 3, "plurals": [2, 2, 2]},
                },
            ),
        ],
    )
    def test_message_get_metadata_void(self, fixture_name, dict, request) -> None:
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
    @pytest.mark.skip(reason="ndict_tools equality has be rewieved")
    def test_message_get_metadata(self, fixture_name, path, expected, request) -> None:
        message = request.getfixturevalue(fixture_name)
        assert message.get_metadata(path) == expected

    def test_message_get_metadata_failed(self, fr_message):
        with pytest.raises(
            KeyError,
            match=re.escape("Metadata '['counts', 'singular']' is not a key or path"),
        ):
            fr_message.get_metadata(["counts", "singular"])


class TestMessageAdd:
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
                    "default_plurals": {
                        1: "Bonjour tout le monde",
                        2: "Bonjour à tous",
                    },
                },
                [
                    ("default", "Hello"),
                    ("options", {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"}),
                    (
                        "default_plurals",
                        {1: "Bonjour tout le monde", 2: "Bonjour à tous"},
                    ),
                ],
            ),
            (
                "empty_message",
                {
                    "default": "Hello",
                    "options": {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"},
                    "default_plurals": {
                        1: "Bonjour tout le monde",
                        2: "Bonjour à tous",
                    },
                    "options_plurals": {
                        1: {1: "Bonjour Mesdames"},
                    },
                },
                [
                    ("default", "Hello"),
                    ("options", {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"}),
                    (
                        "default_plurals",
                        {1: "Bonjour tout le monde", 2: "Bonjour à tous"},
                    ),
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
                    "default_plurals": {
                        1: "Bonjour tout le monde",
                        2: "Bonjour à tous",
                    },
                    "options_plurals": {
                        1: {1: "Bonjour Mesdames"},
                        2: {1: "Bonjour Messieurs"},
                    },
                },
                [
                    ("default", "Hello"),
                    ("options", {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"}),
                    (
                        "default_plurals",
                        {1: "Bonjour tout le monde", 2: "Bonjour à tous"},
                    ),
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
                    "default_plurals": {
                        1: "Bonjour tout le monde",
                        2: "Bonjour à tous",
                    },
                    "options_plurals": {
                        1: {1: "Bonjour Mesdames", 2: "Mesdames"},
                        2: {1: "Bonjour Messieurs", 2: "Messieurs"},
                    },
                },
                [
                    ("default", "Hello"),
                    ("options", {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"}),
                    (
                        "default_plurals",
                        {1: "Bonjour tout le monde", 2: "Bonjour à tous"},
                    ),
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
    @pytest.mark.skip(reason="ndict_tools equality has be rewieved")
    def test_message_add_message(
        self, fixture_name, options, expected, request
    ) -> None:
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
                    "default_plurals": {
                        1: "Bonjour tout le monde",
                        2: "Bonjour à tous",
                    },
                    "options_plurals": {
                        1: {1: "Bonjour Mesdames", 2: "Mesdames"},
                        3: {1: "Bonjour Messieurs", 2: "Messieurs"},
                    },
                },
                "The options_plurals value is malformed",
            ),
        ],
    )
    def test_message_add_message_failed(
        self, fixture_name, options, expected, request
    ) -> None:
        message = request.getfixturevalue(fixture_name)
        with pytest.raises(ValueError, match=re.escape(expected)):
            message.add_message(**options)

    # 3.2 Testing adding main translation

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
    def test_message_add_main(
        self, fixture_name, translation, expected, request
    ) -> None:
        message = request.getfixturevalue(fixture_name)
        if isinstance(translation, dict):
            message.add_principal(**translation)
        else:
            message.add_principal(translation)
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
    def test_message_add_main_failed(
        self, fixture_name, translation, expected, request
    ) -> None:
        message = request.getfixturevalue(fixture_name)
        with pytest.raises(ValueError, match=re.escape(expected)):
            if isinstance(translation, dict):
                message.add_principal(**translation)
            else:
                message.add_principal(translation)

    @pytest.mark.parametrize(
        "fixture_name, translation, expected",
        [
            (
                "empty_message",
                ["Hello {name}"],
                ({1: "Hello {name}"}, {1: {}}, 2, [2, 0]),
            ),
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
    def test_message_add_variant(
        self, fixture_name, translation, expected, request
    ) -> None:
        message = request.getfixturevalue(fixture_name)
        if message.default == "":
            message.add_principal(["Hello", "Hi everybody", "Hi everyone"])
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
        self, fixture_name, translation, expected, request
    ) -> None:
        message = request.getfixturevalue(fixture_name)
        with pytest.raises(ValueError, match=re.escape(expected)):
            if isinstance(translation, dict):
                message.add_variant(**translation)
            else:
                message.add_variant(translation)


class TestMessageAddSegment:
    @pytest.mark.parametrize(
        "fixture_name, segment, token, expected",
        [
            ("empty_message", "Good morning", 0, "Good morning"),
            ("en_message", "Good morning", 3, "Good morning"),
        ],
    )
    def test_message_add_main_segment(
        self, fixture_name, segment, token, expected, request
    ) -> None:
        message = request.getfixturevalue(fixture_name)
        message.add_main_segment(segment, token)
        assert message.get_principal()[token] == expected

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
        self, fixture_name, segment, token, expected, request
    ) -> None:
        message = request.getfixturevalue(fixture_name)
        with pytest.raises(ValueError, match=re.escape(expected)):
            message.add_main_segment(segment, token)

    @pytest.mark.parametrize(
        "fixture_name, segment, expected",
        [
            ("empty_message", "Good morning", "Good morning"),
            ("en_message", "Good morning", "Good morning"),
        ],
    )
    def test_message_protected_add_default_segment(
        self, fixture_name, segment, expected, request
    ) -> None:
        message = request.getfixturevalue(fixture_name)
        message._add_default_segment(segment)
        assert message.default == expected

    @pytest.mark.parametrize(
        "plural, expected",
        [
            ("Good morning everyone", {1: "Good morning everyone"}),
            ("Good morning all", {1: "Good morning everyone", 2: "Good morning all"}),
        ],
    )
    def test_message_protected_add_default_plural_segment(
        self, empty_module_message, plural, expected
    ) -> None:
        empty_module_message._add_default_plurals_segment(plural)
        assert empty_module_message.default_plurals == expected

    @pytest.mark.parametrize(
        "fixture_name, segment, option, token, expected",
        [
            (
                "empty_module_message",
                "Good morning {name}",
                1,
                0,
                "Good morning {name}",
            ),
            (
                "empty_module_message",
                "Good afternoon {name}",
                2,
                0,
                "Good afternoon {name}",
            ),
            ("empty_module_message", "Good morning guys", 1, 1, "Good morning guys"),
            ("empty_module_message", "Good morning all", 1, 2, "Good morning all"),
            (
                "empty_module_message",
                "Good afternoon guys",
                2,
                1,
                "Good afternoon guys",
            ),
            ("empty_module_message", "Good afternoon all", 2, 2, "Good afternoon all"),
        ],
    )
    def test_message_add_variant_segment(
        self, fixture_name, segment, option, token, expected, request
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
    def test_message_add_variant_segment_failed(
        self, fixture_name, segment, option, token, expected, request
    ) -> None:
        message = request.getfixturevalue(fixture_name)
        with pytest.raises(IndexError, match=re.escape(expected)):
            message.add_variant_segment(segment, option, token)

    # empty_module_message has a module scope and has been used in test of add_variant_segment,
    # so options are not empty and indexes 1 and 2 are already stored.

    @pytest.mark.parametrize(
        "segment, expected",
        [
            ("Howdy", [(3, "Howdy")]),
            ("Hi {name}", [(1, "Good morning {name}"), (3, "Howdy"), (4, "Hi {name}")]),
        ],
    )
    def test_message_protected_add_options_segment(
        self, empty_module_message, segment, expected
    ) -> None:
        empty_module_message._add_options_segment(segment)
        for token, result in expected:
            assert empty_module_message.options[token] == result

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
                    "default_plurals": {
                        1: "Bonjour tout le monde",
                        2: "Bonjour à tous",
                    },
                },
                1,
                "Bonjour Mesdames",
                {1: {1: "Bonjour Mesdames"}},
            ),
            (
                {
                    "default": "Hello",
                    "options": {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"},
                    "default_plurals": {
                        1: "Bonjour tout le monde",
                        2: "Bonjour à tous",
                    },
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
                    "default_plurals": {
                        1: "Bonjour tout le monde",
                        2: "Bonjour à tous",
                    },
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
    @pytest.mark.skip(reason="ndict_tools equality has be rewieved")
    def test_message_add_options_plurals_segment(
        self, empty_message, options, alt_index, additional, expected
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
                    "default_plurals": {
                        1: "Bonjour tout le monde",
                        2: "Bonjour à tous",
                    },
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
        self, empty_message, options, alt_index, additional, error, expected
    ) -> None:
        message = empty_message
        message.add_message(**options)
        with pytest.raises(error, match=re.escape(expected)):
            message._add_options_plurals_segment(additional, alt_index)


class TestMessageAddMetadata:
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
        self, empty_module_message, line, file, expected
    ) -> None:
        message = empty_module_message
        message.add_location(line, file)
        assert message.metadata["location"] == expected

    def test_message_add_metadata_language(self, empty_module_message) -> None:
        message = empty_module_message
        message.add_language("en-IE")
        assert message.metadata["language"] == "en-IE"

    def test_message_add_metadata_language_failed(self, empty_module_message) -> None:
        message = empty_module_message
        with pytest.raises(
            ValueError, match="Invalid language tag: ja.Latn/hepburn@heploc"
        ):
            message.add_language("ja.Latn/hepburn@heploc")

    @pytest.mark.parametrize(
        "comment, mode, expected",
        [
            ("A first comment", "user", ["A first comment"]),
            ("Another comment", "user", ["A first comment", "Another comment"]),
            ("1000", "auto", ["1000"]),
            ("1000_001", "auto", ["1000", "1000_001"]),
        ],
    )
    def test_message_add_comment(
        self, empty_module_message, comment, mode, expected
    ) -> None:
        message = empty_module_message
        message.add_comment(mode, comment)
        key = mode + "_comments"
        assert message.metadata[key] == expected

    def test_message_add_comment_failed(self, fr_message) -> None:
        with pytest.raises(ValueError):
            fr_message.add_comment("user", "")

    @pytest.mark.parametrize(
        "alist, dictionary, expected",
        [
            (
                [
                    ["version", "0.2.0"],
                    ["language", "fr-FR"],
                    ["language", "fr-FR"],
                    ["location", [("file.py", 132)]],
                    ["flags", ["python-format"]],
                    ["user_comments", ["A test for metadata"]],
                    [["count", "singular"], 0],
                    [["count", "plurals"], [0]],
                ],
                {},
                {
                    "version": "0.2.0",
                    "language": "fr-FR",
                    "location": [("file.py", 132)],
                    "flags": ["python-format"],
                    "user_comments": ["A test for metadata"],
                    "auto_comments": [],
                    "count": {
                        "singular": 0,
                        "plurals": [0],
                    },
                },
            ),
            (
                [
                    ["language", "fr-FR"],
                    ["language", "fr-FR"],
                    ["location", [("file.py", 132)]],
                    ["flags", ["python-format"]],
                    ["user_comments", ["A test for metadata"]],
                    [["count", "singular"], 0],
                    [["count", "plurals"], [0]],
                ],
                {
                    "version": "0.2.0",
                },
                {
                    "version": "0.2.0",
                    "language": "fr-FR",
                    "location": [("file.py", 132)],
                    "flags": ["python-format"],
                    "user_comments": ["A test for metadata"],
                    "auto_comments": [],
                    "count": {
                        "singular": 0,
                        "plurals": [0],
                    },
                },
            ),
            (
                [
                    ["location", [("file.py", 132)]],
                    ["flags", ["python-format"]],
                    ["user_comments", ["A test for metadata"]],
                    [["count", "singular"], 0],
                    [["count", "plurals"], [0]],
                ],
                {"version": "0.2.0", "language": "fr-FR"},
                {
                    "version": "0.2.0",
                    "language": "fr-FR",
                    "location": [("file.py", 132)],
                    "flags": ["python-format"],
                    "user_comments": ["A test for metadata"],
                    "auto_comments": [],
                    "count": {
                        "singular": 0,
                        "plurals": [0],
                    },
                },
            ),
            (
                [
                    ["flags", ["python-format"]],
                    ["user_comments", ["A test for metadata"]],
                    [["count", "singular"], 0],
                    [["count", "plurals"], [0]],
                ],
                {
                    "version": "0.2.0",
                    "language": "fr-FR",
                    "location": [("file.py", 132)],
                },
                {
                    "version": "0.2.0",
                    "language": "fr-FR",
                    "location": [("file.py", 132)],
                    "flags": ["python-format"],
                    "user_comments": ["A test for metadata"],
                    "auto_comments": [],
                    "count": {
                        "singular": 0,
                        "plurals": [0],
                    },
                },
            ),
            (
                [
                    ["user_comments", ["A test for metadata"]],
                    [["count", "singular"], 0],
                    [["count", "plurals"], [0]],
                ],
                {
                    "version": "0.2.0",
                    "language": "fr-FR",
                    "location": [("file.py", 132)],
                    "flags": ["python-format"],
                },
                {
                    "version": "0.2.0",
                    "language": "fr-FR",
                    "location": [("file.py", 132)],
                    "flags": ["python-format"],
                    "user_comments": ["A test for metadata"],
                    "auto_comments": [],
                    "count": {
                        "singular": 0,
                        "plurals": [0],
                    },
                },
            ),
            (
                [[["count", "singular"], 0], [["count", "plurals"], [0]]],
                {
                    "version": "0.2.0",
                    "language": "fr-FR",
                    "location": [("file.py", 132)],
                    "flags": ["python-format"],
                    "user_comments": ["A test for metadata"],
                },
                {
                    "version": "0.2.0",
                    "language": "fr-FR",
                    "location": [("file.py", 132)],
                    "flags": ["python-format"],
                    "user_comments": ["A test for metadata"],
                    "auto_comments": [],
                    "count": {
                        "singular": 0,
                        "plurals": [0],
                    },
                },
            ),
            (
                (),
                {
                    "version": "0.2.0",
                    "language": "fr-FR",
                    "location": [("file.py", 132)],
                    "flags": ["python-format"],
                    "user_comments": ["A test for metadata"],
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
                    "user_comments": ["A test for metadata"],
                    "auto_comments": [],
                    "count": {
                        "singular": 0,
                        "plurals": [0],
                    },
                },
            ),
            (
                (),
                StrictNestedDictionary(
                    {
                        "version": "0.2.0",
                        "language": "fr-FR",
                        "location": [("file.py", 132)],
                        "flags": ["python-format"],
                        "user_comments": ["A test for metadata"],
                        "auto_comments": ["1000", "1000_001"],
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
                    "user_comments": ["A test for metadata"],
                    "auto_comments": ["1000", "1000_001"],
                    "count": {
                        "singular": 0,
                        "plurals": [0],
                    },
                },
            ),
        ],
    )
    def test_message_add_metadata(self, alist, dictionary, expected) -> None:
        message = Message("1001", "A test for metadata")
        message.add_metadata(*alist, **dictionary)
        control = message.metadata.to_dict()
        assert control == expected

    @pytest.mark.parametrize(
        "alist, dictionary, expected",
        [
            (
                [["language:", "fr-Fr"]],
                {
                    "version": "0.2.0",
                    "location": [("file.py", 132)],
                    "flags": ["python-format"],
                    "user_comments": ["A test for metadata"],
                    "count": {
                        "singular": 0,
                        "plurals": [0],
                    },
                },
                "The path 'language:' is not a present key in the metadata dictionary",
            ),
            (
                (),
                {
                    "version": "0.2.0",
                    "language": "fr-FR",
                    "location": [("file.py", 132)],
                    "flags": ["python-format"],
                    "user_comments": ["A test for metadata"],
                    "count": {
                        "plurals: [0]",
                    },
                },
                "<class 'set'> type of {'plurals: [0]'} is not compatible metadata",
            ),
            (
                (),
                {
                    "version": "0.2.0",
                    "language": "fr-FR",
                    "location": [("file.py", 132)],
                    "flags": ["python-format"],
                    "user_comments": ["A test for metadata"],
                    "count": {"singular": 0, "plural": [0]},
                },
                "The path '['count', 'plural']' is not a present key in the metadata dictionary",
            ),
            (
                (),
                {
                    "version": "0.2.0",
                    "language": "fr-FR",
                    "locations": [("file.py", 132)],
                    "flags": ["python-format"],
                    "user_comments": ["A test for metadata"],
                    "count": {"singular": 0, "plurals": [0]},
                },
                "The key 'locations' is not a present key in the metadata dictionary",
            ),
        ],
    )
    def test_message_add_metadata_failed(self, alist, dictionary, expected) -> None:
        message = Message("1001", "A test for metadata")
        with pytest.raises((KeyError, TypeError), match=re.escape(expected)):
            message.add_metadata(*alist, **dictionary)


class TestMessageUpdate:
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
                        1: {
                            1: "Good afternoon everybody",
                            2: "Good afternoon everyone",
                        },
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
    @pytest.mark.skip(reason="ndict_tools equality has be rewieved")
    def test_message_update_message(self, options, expected) -> None:
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
                        1: {
                            1: "Good afternoon everybody",
                            2: "Good afternoon everyone",
                        },
                        3: {1: "Good evening everybody", 2: "Good evening everyone"},
                    },
                },
                "The 'options_plurals' value is malformed",
            ),
        ],
    )
    def test_message_update_message_failed(self, options, expected) -> None:
        message = Message("1001", "A test for metadata")
        with pytest.raises(ValueError, match=re.escape(expected)):
            message.update_message(**options)

    # 4.2 Testing updating main translation

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
                {
                    "default": "",
                    "default_plurals": {1: "Hi everybody", 2: "Hi everyone"},
                },
                [
                    ("default", "Hi"),
                    ("default_plurals", {1: "Hi everybody", 2: "Hi everyone"}),
                ],
            ),
        ],
    )
    def test_message_update_main(self, translation, expected) -> None:
        message = Message("1001", "Hi")
        if isinstance(translation, dict):
            message.update_principal(**translation)
        else:
            message.update_principal(translation)
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
    def test_message_update_main_failed(self, translation, expected) -> None:
        message = Message("1001", "Hi")
        with pytest.raises(ValueError, match=re.escape(expected)):
            if isinstance(translation, dict):
                message.update_principal(**translation)
            else:
                message.update_principal(translation)

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
                    (
                        "default_plurals",
                        {1: "Bonjour à tous", 2: "Bonjour tout le monde"},
                    ),
                    ("options", {1: "Chère Mme {name}", 2: "Bonjour M. {name}"}),
                ],
            ),
            (
                "fr_message",
                2,
                ["Cher M. {name}", "Chers Messieurs", "Chers tous"],
                [
                    ("default", "Bonjour"),
                    (
                        "default_plurals",
                        {1: "Bonjour à tous", 2: "Bonjour tout le monde"},
                    ),
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
                    (
                        "default_plurals",
                        {1: "Bonjour à tous", 2: "Bonjour tout le monde"},
                    ),
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
                    (
                        "default_plurals",
                        {1: "Bonjour à tous", 2: "Bonjour tout le monde"},
                    ),
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
                    (
                        "default_plurals",
                        {1: "Bonjour à tous", 2: "Bonjour tout le monde"},
                    ),
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
        self, fixture_message, option, translation, expected, request
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
        self, fixture_message, option, translation, expected, request
    ) -> None:
        message = request.getfixturevalue(fixture_message)
        with pytest.raises((ValueError, IndexError), match=re.escape(expected)):
            if isinstance(translation, dict):
                message.update_variant(option, **translation)
            else:
                message.update_variant(option, translation)


class TestMessageUpdateSegment:
    @pytest.mark.parametrize(
        "fixture_message, segment, token, expected",
        [
            ("en_message", "Good morning", 0, [(0, "Good morning")]),
            (
                "en_message",
                "Good morning everybody",
                1,
                [(0, "Hello"), (1, "Good morning everybody")],
            ),
        ],
    )
    def test_message_update_main_segment(
        dself, fixture_message, segment, token, expected, request
    ) -> None:
        message = request.getfixturevalue(fixture_message)
        message.update_main_segment(segment, token)
        for token, text in expected:
            assert message.get_principal()[token] == text

    @pytest.mark.parametrize(
        "fixture_message, segment, token, expected",
        [
            ("empty_message", "", 0, "Empty text cannot be added"),
            (
                "fr_message",
                "Good morning everybody",
                -1,
                "The token location (-1) is out of range",
            ),
            (
                "fr_message",
                "Good morning everybody",
                4,
                "The token location (4) is out of range",
            ),
            (
                "fr_message",
                "Bonjour",
                0,
                "The text value ('Bonjour') is already stored as default singular translation : 'Bonjour'",
            ),
            (
                "en_message",
                "Hi everyone",
                2,
                "The text value ('Hi everyone') is already stored as default plural index (2) : 'Hi everyone'",
            ),
        ],
    )
    def test_message_update_main_segment_failed(
        self, fixture_message, segment, token, expected, request
    ) -> None:
        message = request.getfixturevalue(fixture_message)
        with pytest.raises((ValueError, IndexError), match=re.escape(expected)):
            message.update_main_segment(segment, token)

    @pytest.mark.parametrize(
        "fixture_message, segment, expected",
        [
            ("en_message", "Good morning", [(0, "Good morning"), (1, "Hi everybody")]),
            ("empty_message", "", [(0, "")]),
        ],
    )
    def test_message_protected_update_default_segment(
        self, fixture_message, segment, expected, request
    ) -> None:
        message = request.getfixturevalue(fixture_message)
        message._update_default_segment(segment)
        for token, text in expected:
            assert message.get_principal()[token] == text

    @pytest.mark.parametrize(
        "fixture_message, segment, token, expected",
        [
            (
                "en_message",
                "Good morning everybody",
                1,
                [(0, "Hello"), (1, "Good morning everybody")],
            ),
            ("fr_message", "", 2, [(0, "Bonjour"), (1, "Bonjour à tous"), (2, "")]),
        ],
    )
    def test_message_protected_update_default_plurals_segment(
        self, fixture_message, segment, token, expected, request
    ) -> None:
        message = request.getfixturevalue(fixture_message)
        message._update_default_plurals_segment(segment, token)
        for token, text in expected:
            assert message.get_principal()[token] == text

    @pytest.mark.parametrize(
        "fixture_message, segment, token, expected",
        [
            (
                "en_message",
                "Good morning everybody",
                -1,
                "The token location (-1) is out of range",
            ),
            (
                "en_message",
                "Good morning everybody",
                3,
                "The token location (3) is out of range",
            ),
            ("empty_message", "", 1, "The token location (1) is out of range"),
        ],
    )
    def test_message_protected_update_default_plurals_segment_failed(
        self, fixture_message, segment, token, expected, request
    ) -> None:
        message = request.getfixturevalue(fixture_message)
        with pytest.raises(IndexError, match=re.escape(expected)):
            message._update_default_plurals_segment(segment, token)

    @pytest.mark.parametrize(
        "fixture_message, segment, option, token, expected",
        [
            (
                "en_message",
                "Good morning {name}",
                1,
                0,
                [
                    (1, 0, "Good morning {name}"),
                    (2, 0, "Hello {name}"),
                    (1, 1, "Hi everybody"),
                    (1, 2, "Ladies"),
                ],
            ),
            (
                "en_message",
                "Good morning everybody",
                1,
                1,
                [
                    (1, 0, "Hello {name}"),
                    (2, 0, "Hello {name}"),
                    (1, 1, "Good morning everybody"),
                    (1, 2, "Ladies"),
                ],
            ),
            (
                "en_message",
                "Good morning everybody",
                1,
                2,
                [
                    (1, 0, "Hello {name}"),
                    (2, 0, "Hello {name}"),
                    (1, 1, "Hi everybody"),
                    (1, 2, "Good morning everybody"),
                ],
            ),
        ],
    )
    def test_message_update_variant_segment(
        self, fixture_message, segment, option, token, expected, request
    ) -> None:
        message = request.getfixturevalue(fixture_message)
        message.update_variant_segment(segment, option, token)
        for expected_option, expected_token, expected_text in expected:
            assert message.get_variant(expected_option)[expected_token] == expected_text

    @pytest.mark.parametrize(
        "fixture_message, segment, option, token, expected",
        [
            ("en_message", "", 1, 0, "Empty text cannot be added"),
            ("en_message", "", 1, 1, "Empty text cannot be added"),
            (
                "empty_message",
                "Good morning everybody",
                -1,
                0,
                "The variant location (-1) is out of range",
            ),
            (
                "empty_message",
                "Good morning everybody",
                1,
                0,
                "The variant location (1) is out of range",
            ),
            (
                "empty_message",
                "Good morning everybody",
                1,
                1,
                "The variant location (1) is out of range",
            ),
            (
                "en_message",
                "Good morning everybody",
                1,
                -1,
                "The token location (-1) of the variant location (1) is out of range",
            ),
            (
                "en_message",
                "Good morning everybody",
                1,
                3,
                "The token location (3) of the variant location (1) is out of range",
            ),
        ],
    )
    def test_message_update_variant_segment_failed(
        self, fixture_message, segment, option, token, expected, request
    ) -> None:
        message = request.getfixturevalue(fixture_message)
        with pytest.raises((IndexError, ValueError), match=re.escape(expected)):
            message.update_variant_segment(segment, option, token)

    @pytest.mark.parametrize(
        "fixture_message, segment, option, expected",
        [
            ("fr_message", "", 1, [(1, 0, "")]),
            (
                "en_message",
                "Good morning {name}",
                1,
                [
                    (1, 0, "Good morning {name}"),
                    (2, 0, "Hello {name}"),
                    (1, 1, "Hi everybody"),
                    (1, 2, "Ladies"),
                ],
            ),
            (
                "en_message",
                "Good afternoon {name}",
                2,
                [
                    (1, 0, "Hello {name}"),
                    (2, 0, "Good afternoon {name}"),
                    (1, 1, "Hi everybody"),
                    (1, 2, "Ladies"),
                ],
            ),
        ],
    )
    def test_message_protected_update_options_segment(
        self, fixture_message, segment, option, expected, request
    ) -> None:
        message = request.getfixturevalue(fixture_message)
        message._update_options_segment(segment, option)
        for expected_option, expected_token, expected_text in expected:
            assert message.get_variant(expected_option)[expected_token] == expected_text

    @pytest.mark.parametrize(
        "fixture_message, segment, option, expected",
        [
            (
                "empty_message",
                "Good morning everybody",
                -1,
                "The variant location (-1) is out of range",
            ),
            (
                "empty_message",
                "Good morning everybody",
                1,
                "The variant location (1) is out of range",
            ),
            (
                "en_message",
                "Good morning everybody",
                3,
                "The variant location (3) is out of range",
            ),
        ],
    )
    def test_message_protected_update_options_segment_failed(
        self, fixture_message, segment, option, expected, request
    ) -> None:
        message = request.getfixturevalue(fixture_message)
        with pytest.raises((IndexError, ValueError), match=re.escape(expected)):
            message._update_options_segment(segment, option)

    @pytest.mark.parametrize(
        "fixture_message, segment, option, token, expected",
        [
            (
                "en_message",
                "",
                1,
                1,
                [
                    (1, 0, "Hello {name}"),
                    (2, 0, "Hello {name}"),
                    (1, 1, ""),
                    (1, 2, "Ladies"),
                ],
            ),
            (
                "en_message",
                "Good morning everybody",
                1,
                1,
                [
                    (1, 0, "Hello {name}"),
                    (2, 0, "Hello {name}"),
                    (1, 1, "Good morning everybody"),
                    (1, 2, "Ladies"),
                ],
            ),
            (
                "en_message",
                "Good morning everybody",
                1,
                2,
                [
                    (1, 0, "Hello {name}"),
                    (2, 0, "Hello {name}"),
                    (1, 1, "Hi everybody"),
                    (1, 2, "Good morning everybody"),
                ],
            ),
        ],
    )
    def test_message_protected_update_options_plurals_segment(
        self, fixture_message, segment, option, token, expected, request
    ) -> None:
        message = request.getfixturevalue(fixture_message)
        message._update_options_plurals_segment(segment, option, token)
        for expected_option, expected_token, expected_text in expected:
            assert message.get_variant(expected_option)[expected_token] == expected_text

    @pytest.mark.parametrize(
        "fixture_message, segment, option, token, expected",
        [
            (
                "empty_message",
                "Good morning everybody",
                -1,
                0,
                "The variant location (-1) is out of range",
            ),
            (
                "empty_message",
                "Good morning everybody",
                1,
                0,
                "The variant location (1) is out of range",
            ),
            (
                "empty_message",
                "Good morning everybody",
                1,
                1,
                "The variant location (1) is out of range",
            ),
            (
                "en_message",
                "Good morning everybody",
                1,
                -1,
                "The token location (-1) of the variant location (1) is out of range",
            ),
            (
                "en_message",
                "Good morning everybody",
                1,
                3,
                "The token location (3) of the variant location (1) is out of range",
            ),
        ],
    )
    def test_message_protected_update_options_plurals_segment_failed(
        self, fixture_message, segment, option, token, expected, request
    ) -> None:
        message = request.getfixturevalue(fixture_message)
        with pytest.raises(IndexError, match=re.escape(expected)):
            message._update_options_plurals_segment(segment, option, token)


class TestMessageUpdateMetadata:
    @pytest.mark.parametrize(
        "fixture_message, alist, dictionary, expected",
        [
            (
                "fr_message",
                [
                    [["version"], "0.2.0"],
                    [["language"], "fr"],
                    [["user_comments"], ["A test for metadata"]],
                ],
                {},
                {
                    "version": "0.2.0",
                    "language": "fr",
                    "location": [],
                    "flags": ["python-format"],
                    "user_comments": ["A test for metadata"],
                    "auto_comments": ["1000_000", "1000_001", "1000_02"],
                    "count": {
                        "singular": 3,
                        "plurals": [2, 2, 2],
                    },
                },
            ),
            (
                "fr_message",
                [[["language"], "fr"], [["user_comments"], ["A test for metadata"]]],
                {"version": "0.2.0"},
                {
                    "version": "0.2.0",
                    "language": "fr",
                    "location": [],
                    "flags": ["python-format"],
                    "user_comments": ["A test for metadata"],
                    "auto_comments": ["1000_000", "1000_001", "1000_02"],
                    "count": {
                        "singular": 3,
                        "plurals": [2, 2, 2],
                    },
                },
            ),
            (
                "fr_message",
                [[["user_comments"], ["A test for metadata"]]],
                {"version": "0.2.0", "language": "fr"},
                {
                    "version": "0.2.0",
                    "language": "fr",
                    "location": [],
                    "flags": ["python-format"],
                    "user_comments": ["A test for metadata"],
                    "auto_comments": ["1000_000", "1000_001", "1000_02"],
                    "count": {
                        "singular": 3,
                        "plurals": [2, 2, 2],
                    },
                },
            ),
            (
                "fr_message",
                [],
                {
                    "version": "0.2.0",
                    "language": "fr",
                    "user_comments": ["A test for metadata"],
                    "auto_comments": ["1000", "1000_001"],
                },
                {
                    "version": "0.2.0",
                    "language": "fr",
                    "location": [],
                    "flags": ["python-format"],
                    "user_comments": ["A test for metadata"],
                    "auto_comments": ["1000", "1000_001"],
                    "count": {
                        "singular": 3,
                        "plurals": [2, 2, 2],
                    },
                },
            ),
            (
                "en_message",
                [],
                {"location": [("file.txt", 126)], "language": "en-GB"},
                {
                    "version": "0.1.0",
                    "language": "en-GB",
                    "location": [("file.txt", 126)],
                    "flags": ["python-format"],
                    "user_comments": ["Greeting message to one or more..."],
                    "auto_comments": ["1000_000", "1000_001", "1000_02"],
                    "count": {
                        "singular": 3,
                        "plurals": [2, 2, 2],
                    },
                },
            ),
            (
                "en_message",
                [[["location"], [("file.txt", 126)]], [["language"], "en-GB"]],
                {},
                {
                    "version": "0.1.0",
                    "language": "en-GB",
                    "location": [("file.txt", 126)],
                    "flags": ["python-format"],
                    "user_comments": ["Greeting message to one or more..."],
                    "auto_comments": ["1000_000", "1000_001", "1000_02"],
                    "count": {
                        "singular": 3,
                        "plurals": [2, 2, 2],
                    },
                },
            ),
        ],
    )
    def test_message_update_metadata(
        self, fixture_message, alist, dictionary, expected, request
    ) -> None:
        message = request.getfixturevalue(fixture_message)
        message.update_metadata(*alist, **dictionary)
        control = message.metadata.to_dict()
        assert control == expected

    @pytest.mark.parametrize(
        "alist, dictionary, expected",
        [
            (
                [["language:", "fr-Fr"]],
                {
                    "version": "0.2.0",
                    "location": [("file.py", 132)],
                    "user_comments": ["A test for metadata"],
                },
                "The path 'language:' is not a present key in the metadata dictionary",
            ),
            (
                (),
                {
                    "version": "0.2.0",
                    "language": "fr-FR",
                    "location": [("file.py", 132)],
                    "user_comments": ["A test for metadata"],
                    "count": {
                        "plurals: [0]",
                    },
                },
                "<class 'set'> of {'plurals: [0]'} is not compatible metadata",
            ),
            (
                (),
                {
                    "version": "0.2.0",
                    "language": "fr-FR",
                    "location": [("file.py", 132)],
                    "user_comments": ["A test for metadata"],
                    "count": {"singular": 0, "plural": [0]},
                },
                "The path '['count', 'plural']' is not a present key in the metadata dictionary",
            ),
            (
                (),
                {
                    "version": "0.2.0",
                    "language": "fr-FR",
                    "locations": [("file.py", 132)],
                    "user_comments": ["A test for metadata"],
                },
                "The key 'locations' is not a present key in the metadata dictionary",
            ),
            (
                (),
                {
                    "version": "0.1.0",
                    "language": "fr-FR",
                    "location": [("file.py", 132)],
                    "user_comments": ["A test for metadata"],
                },
                "The value (0.1.0) is already stored in the path '[version]'",
            ),
            (
                [],
                {
                    "language": "fr-FR",
                    "location": [("file.py", 132)],
                    "count": {"singular": 1},
                },
                "The value (1) is already stored in the path '['count', 'singular']'",
            ),
            (
                [[["count", "singular"], 1]],
                {
                    "language": "fr-FR",
                    "location": [("file.py", 132)],
                },
                "The value (1) is already stored in the path '['count', 'singular']'",
            ),
        ],
    )
    def test_message_update_metadata_failed(self, alist, dictionary, expected) -> None:
        message = Message("1001", "A test for metadata")
        with pytest.raises(
            (KeyError, TypeError, ValueError), match=re.escape(expected)
        ):
            message.update_metadata(*alist, **dictionary)


class TestMessageRemove:
    @pytest.mark.parametrize(
        "fixture_message, expected",
        [
            (
                "fr_message",
                [
                    ("default", ""),
                    ("default_plurals", {}),
                    (
                        "metadata",
                        StrictNestedDictionary(
                            {
                                "version": __version__,
                                "language": "",
                                "location": [],
                                "flags": ["python-format"],
                                "user_comments": [],
                                "auto_comments": [],
                                "count": {
                                    "singular": 0,
                                    "plurals": [],
                                },
                            },
                            default_setup={"indent": 2},
                        ),
                    ),
                ],
            ),
            (
                "en_message",
                [("options", {}), ("options_plurals", StrictNestedDictionary())],
            ),
            ("empty_message", [("default", ""), ("options", {})]),
        ],
    )
    def test_message_remove_message(self, fixture_message, expected, request) -> None:
        message = request.getfixturevalue(fixture_message)
        message.remove_message()
        for attribute, value in expected:
            assert message.__getattribute__(attribute) == value

    # 5.2 Testing main translations

    @pytest.mark.parametrize(
        "fixture_message, expected",
        [
            (
                "fr_message",
                [
                    ("default", ""),
                    ("default_plurals", {}),
                    (
                        "metadata",
                        StrictNestedDictionary(
                            {
                                "version": __version__,
                                "language": "fr-FR",
                                "location": [],
                                "flags": ["python-format"],
                                "user_comments": [
                                    "In French, Greeting message to one or more..."
                                ],
                                "auto_comments": ["1000_000", "1000_001", "1000_02"],
                                "count": {
                                    "singular": 2,
                                    "plurals": [0, 2, 2],
                                },
                            },
                            default_setup={"indent": 2},
                        ),
                    ),
                ],
            ),
            (
                "en_message",
                [
                    ("options", {1: "Hello {name}", 2: "Hello {name}"}),
                    (
                        "options_plurals",
                        StrictNestedDictionary(
                            {
                                1: {1: "Hi everybody", 2: "Ladies"},
                                2: {1: "Hi everyone", 2: "Gentlemen"},
                            }
                        ),
                    ),
                ],
            ),
            ("empty_message", [("default", ""), ("options", {})]),
        ],
    )
    def test_message_remove_main(self, fixture_message, expected, request) -> None:
        message = request.getfixturevalue(fixture_message)
        message.remove_principal()
        for attribute, value in expected:
            assert message.__getattribute__(attribute) == value

    @pytest.mark.parametrize(
        "fixture_message, expected",
        [
            (
                "fr_message",
                [
                    ("default", ""),
                    (
                        "default_plurals",
                        {1: "Bonjour à tous", 2: "Bonjour tout le monde"},
                    ),
                    (
                        "metadata",
                        StrictNestedDictionary(
                            {
                                "version": __version__,
                                "language": "fr-FR",
                                "location": [],
                                "flags": ["python-format"],
                                "user_comments": [
                                    "In French, Greeting message to one or more..."
                                ],
                                "auto_comments": ["1000_000", "1000_001", "1000_02"],
                                "count": {
                                    "singular": 2,
                                    "plurals": [2, 2, 2],
                                },
                            },
                            default_setup={"indent": 2},
                        ),
                    ),
                ],
            ),
            (
                "en_message",
                [
                    ("options", {1: "Hello {name}", 2: "Hello {name}"}),
                    (
                        "options_plurals",
                        StrictNestedDictionary(
                            {
                                1: {1: "Hi everybody", 2: "Ladies"},
                                2: {1: "Hi everyone", 2: "Gentlemen"},
                            }
                        ),
                    ),
                ],
            ),
            ("empty_message", [("default", ""), ("options", {})]),
        ],
    )
    def test_message_protected_remove_default_segment(
        self, fixture_message, expected, request
    ) -> None:
        message = request.getfixturevalue(fixture_message)
        message._remove_default_segment()
        for attribute, value in expected:
            assert message.__getattribute__(attribute) == value

    @pytest.mark.parametrize(
        "fixture_message, token, expected",
        [
            (
                "fr_message",
                2,
                [
                    ("default", "Bonjour"),
                    ("default_plurals", {1: "Bonjour à tous"}),
                    (
                        "metadata",
                        StrictNestedDictionary(
                            {
                                "version": __version__,
                                "language": "fr-FR",
                                "location": [],
                                "flags": ["python-format"],
                                "user_comments": [
                                    "In French, Greeting message to one or more..."
                                ],
                                "auto_comments": ["1000_000", "1000_001", "1000_02"],
                                "count": {
                                    "singular": 3,
                                    "plurals": [1, 2, 2],
                                },
                            },
                            default_setup={"indent": 2},
                        ),
                    ),
                ],
            ),
            (
                "en_message",
                1,
                [
                    ("options", {1: "Hello {name}", 2: "Hello {name}"}),
                    ("default_plurals", {1: "Hi everyone"}),
                    (
                        "options_plurals",
                        StrictNestedDictionary(
                            {
                                1: {1: "Hi everybody", 2: "Ladies"},
                                2: {1: "Hi everyone", 2: "Gentlemen"},
                            }
                        ),
                    ),
                ],
            ),
        ],
    )
    def test_message_protected_remove_default_plurals_segment(
        self, fixture_message, token, expected, request
    ) -> None:
        message = request.getfixturevalue(fixture_message)
        message._remove_default_plurals_segment(token)
        for attribute, value in expected:
            assert message.__getattribute__(attribute) == value

    @pytest.mark.parametrize(
        "fixture_message, token, expected",
        [
            (
                "fr_message",
                -1,
                "The location (-1) of the plural to be remove is out of range",
            ),
            (
                "en_message",
                3,
                "The location (3) of the plural to be remove is out of range",
            ),
        ],
    )
    def test_message_protected_remove_default_plurals_segment_failed(
        self, fixture_message, token, expected, request
    ) -> None:
        message = request.getfixturevalue(fixture_message)
        with pytest.raises(IndexError, match=re.escape(expected)):
            message._remove_default_plurals_segment(token)

    # 5.2 Testing variant translations

    @pytest.mark.parametrize(
        "fixture_message, option, expected",
        [
            (
                "fr_message",
                1,
                [
                    ("default", None, "Bonjour"),
                    ("options", 1, "Bonjour M. {name}"),
                    ("options", None, {1: "Bonjour M. {name}"}),
                    ("options_plurals", [1, 2], "Messieurs"),
                    ("metadata", ["count", "singular"], 2),
                    ("metadata", ["count", "plurals"], [2, 2]),
                ],
            ),
            (
                "en_message",
                2,
                [
                    ("default", None, "Hello"),
                    ("options", 1, "Hello {name}"),
                    ("options", None, {1: "Hello {name}"}),
                    ("options_plurals", [1, 2], "Ladies"),
                    (
                        "options_plurals",
                        None,
                        StrictNestedDictionary({1: {1: "Hi everybody", 2: "Ladies"}}),
                    ),
                    ("metadata", ["count", "singular"], 2),
                ],
            ),
        ],
    )
    def test_message_remove_variant(
        self, fixture_message, option, expected, request
    ) -> None:
        message = request.getfixturevalue(fixture_message)
        message.remove_variant(option)
        for attribute, keys, value in expected:
            if keys is None:
                assert message.__getattribute__(attribute) == value
            else:
                assert message.__getattribute__(attribute)[keys] == value

    @pytest.mark.parametrize(
        "fixture_message, option, expected",
        [
            ("empty_message", 1, "The variant location (1) is out of range"),
            ("fr_message", -1, "The variant location (-1) is out of range"),
            ("en_message", 3, "The variant location (3) is out of range"),
        ],
    )
    def test_message_remove_variant_failure(
        self, fixture_message, option, expected, request
    ) -> None:
        message = request.getfixturevalue(fixture_message)
        with pytest.raises(IndexError, match=re.escape(expected)):
            message.remove_variant(option)

    # 5.4 Testing components

    @pytest.mark.parametrize(
        "fixture_message, option, expected",
        [
            (
                "fr_message",
                1,
                [
                    ("default", None, "Bonjour"),
                    ("options", 1, "Bonjour M. {name}"),
                    ("options", None, {1: "Bonjour M. {name}"}),
                    ("options_plurals", [2, 2], "Messieurs"),
                ],
            ),
            (
                "en_message",
                2,
                [
                    ("default", None, "Hello"),
                    ("options", 1, "Hello {name}"),
                    ("options", None, {1: "Hello {name}"}),
                    ("options_plurals", [1, 2], "Ladies"),
                    (
                        "options_plurals",
                        None,
                        StrictNestedDictionary(
                            {
                                1: {1: "Hi everybody", 2: "Ladies"},
                                2: {1: "Hi everyone", 2: "Gentlemen"},
                            }
                        ),
                    ),
                ],
            ),
        ],
    )
    def test_message_protected_remove_options_segment(
        self, fixture_message, option, expected, request
    ) -> None:
        message = request.getfixturevalue(fixture_message)
        message._remove_options_segment(option)
        for attribute, keys, value in expected:
            if keys is None:
                assert message.__getattribute__(attribute) == value
            else:
                assert message.__getattribute__(attribute)[keys] == value

    @pytest.mark.parametrize(
        "fixture_message, option, expected",
        [
            ("empty_message", 1, "The variant location (1) is out of range"),
            ("fr_message", -1, "The variant location (-1) is out of range"),
            ("en_message", 3, "The variant location (3) is out of range"),
        ],
    )
    def test_message_protected_remove_options_segment_failure(
        self, fixture_message, option, expected, request
    ) -> None:
        message = request.getfixturevalue(fixture_message)
        with pytest.raises(IndexError, match=re.escape(expected)):
            message._remove_options_segment(option)

    @pytest.mark.parametrize(
        "fixture_message, option, token, expected",
        [
            (
                "fr_message",
                1,
                2,
                [
                    ("default", None, "Bonjour"),
                    ("options", 2, "Bonjour M. {name}"),
                    (
                        "options",
                        None,
                        {1: "Bonjour Mme {name}", 2: "Bonjour M. {name}"},
                    ),
                    ("options_plurals", [1, 1], "Bonjour Mesdames"),
                    ("options_plurals", [2, 2], "Messieurs"),
                    ("metadata", ["count", "singular"], 3),
                ],
            ),
            (
                "en_message",
                2,
                1,
                [
                    ("default", None, "Hello"),
                    ("options", 1, "Hello {name}"),
                    ("options", None, {1: "Hello {name}", 2: "Hello {name}"}),
                    ("options_plurals", [1, 2], "Ladies"),
                    (
                        "options_plurals",
                        None,
                        StrictNestedDictionary(
                            {1: {1: "Hi everybody", 2: "Ladies"}, 2: {1: "Gentlemen"}}
                        ),
                    ),
                    ("metadata", ["count", "singular"], 3),
                ],
            ),
            (
                "fr_message",
                1,
                None,
                [
                    ("default", None, "Bonjour"),
                    ("options", 1, "Bonjour M. {name}"),
                    ("options", None, {1: "Bonjour M. {name}"}),
                    ("options_plurals", [1, 1], "Bonjour Mesdames"),
                    ("options_plurals", [2, 2], "Messieurs"),
                    ("metadata", ["count", "singular"], 2),
                    ("metadata", ["count", "plurals"], [2, 2, 2]),
                ],
            ),
        ],
    )
    def test_message_protected_remove_options_plurals_segment(
        self, fixture_message, option, token, expected, request
    ) -> None:
        message = request.getfixturevalue(fixture_message)
        message._remove_options_plurals_segment(option, token)
        for attribute, keys, value in expected:
            if keys is None:
                assert message.__getattribute__(attribute) == value
            else:
                assert message.__getattribute__(attribute)[keys] == value

    @pytest.mark.parametrize(
        "fixture_message, option, token, expected",
        [
            ("empty_message", 1, 0, "The variant location (1) is out of range"),
            ("fr_message", -1, 4, "The variant location (-1) is out of range"),
            ("en_message", 3, 6, "The variant location (3) is out of range"),
            ("fr_message", 1, -1, "The plural path [1, -1] is out of range"),
            ("en_message", 2, 6, "The plural path [2, 6] is out of range"),
        ],
    )
    def test_message_protected_remove_options_plurals_failure(
        self, fixture_message, option, token, expected, request
    ) -> None:
        message = request.getfixturevalue(fixture_message)
        with pytest.raises(IndexError, match=re.escape(expected)):
            message._remove_options_plurals_segment(option, token)

    # 5.5 Testing metadata

    @pytest.mark.parametrize(
        "fixture_message, keys, expected",
        [
            ("fr_message", "language", [("language", "")]),
            ("en_message", "version", [("language", "en"), ("version", __version__)]),
            (
                "fr_message",
                None,
                [
                    ("version", __version__),
                    ("language", ""),
                    ("location", []),
                    ("flags", ["python-format"]),
                    ("user_comments", []),
                    ("auto_comments", []),
                    (["count", "singular"], 0),
                    (
                        ["count", "plurals"],
                        [],
                    ),
                ],
            ),
        ],
    )
    def test_message_remove_metadata(
        self, fixture_message, keys, expected, request
    ) -> None:
        message = request.getfixturevalue(fixture_message)
        message.remove_metadata(keys)
        for path, value in expected:
            assert message.metadata[path] == value

    @pytest.mark.parametrize(
        "fixture_message, keys, expected",
        [
            ("fr_message", "languages", "Metadata key 'languages' not found"),
            (
                "en_message",
                ["count", "plural"],
                "path '['count', 'plural']' is not a present key in the metadata dictionary",
            ),
        ],
    )
    def test_message_remove_metadata_failed(
        self, fixture_message, keys, expected, request
    ) -> None:
        message = request.getfixturevalue(fixture_message)
        with pytest.raises(KeyError, match=re.escape(expected)):
            message.remove_metadata(keys)


class TestMessageSwitchToggle:
    @pytest.mark.parametrize(
        "fixture_message, source, destination, expected",
        [
            (
                "fr_message",
                0,
                2,
                [
                    ["Bonjour M. {name}", "Bonjour Messieurs", "Messieurs"],
                    ["Bonjour Mme {name}", "Bonjour Mesdames", "Mesdames"],
                    ["Bonjour", "Bonjour à tous", "Bonjour tout le monde"],
                ],
            ),
            (
                "en_message",
                1,
                2,
                [
                    ["Hello", "Hi everybody", "Hi everyone"],
                    ["Hello {name}", "Hi everyone", "Gentlemen"],
                    ["Hello {name}", "Hi everybody", "Ladies"],
                ],
            ),
            (
                "fr_message",
                2,
                1,
                [
                    ["Bonjour", "Bonjour à tous", "Bonjour tout le monde"],
                    ["Bonjour M. {name}", "Bonjour Messieurs", "Messieurs"],
                    ["Bonjour Mme {name}", "Bonjour Mesdames", "Mesdames"],
                ],
            ),
            (
                "en_message",
                2,
                1,
                [
                    ["Hello", "Hi everybody", "Hi everyone"],
                    ["Hello {name}", "Hi everyone", "Gentlemen"],
                    ["Hello {name}", "Hi everybody", "Ladies"],
                ],
            ),
        ],
    )
    def test_message_switch(
        self, fixture_message, source, destination, expected, request
    ):
        message = request.getfixturevalue(fixture_message)
        message.switch(source, destination)
        assert message.get_principal() == expected[0]
        assert message.get_variant(1) == expected[1]
        assert message.get_variant(2) == expected[2]

    @pytest.mark.parametrize(
        "fixture_message, source, destination, expected",
        [
            ("fr_message", 0, 0, "source (0) and destination (0) must be different"),
            ("en_message", 3, 2, "The variant location (3) is out of range"),
            ("fr_message", 0, -1, "The variant location (-1) is out of range"),
            ("en_message", 2, 4, "The variant location (4) is out of range"),
        ],
    )
    def test_message_switch_failed(
        self, fixture_message, source, destination, expected, request
    ):
        message = request.getfixturevalue(fixture_message)
        with pytest.raises(IndexError, match=re.escape(expected)):
            message.switch(source, destination)

    @pytest.mark.parametrize(
        "fixture_message, orientations, expected",
        [
            (
                "fr_message",
                ["natural"],
                [
                    ["Bonjour M. {name}", "Bonjour Messieurs", "Messieurs"],
                    ["Bonjour", "Bonjour à tous", "Bonjour tout le monde"],
                    ["Bonjour Mme {name}", "Bonjour Mesdames", "Mesdames"],
                ],
            ),
            (
                "en_message",
                ["reverse"],
                [
                    ["Hello {name}", "Hi everybody", "Ladies"],
                    ["Hello {name}", "Hi everyone", "Gentlemen"],
                    ["Hello", "Hi everybody", "Hi everyone"],
                ],
            ),
            (
                "fr_message",
                ["natural", "natural"],
                [
                    ["Bonjour Mme {name}", "Bonjour Mesdames", "Mesdames"],
                    ["Bonjour M. {name}", "Bonjour Messieurs", "Messieurs"],
                    ["Bonjour", "Bonjour à tous", "Bonjour tout le monde"],
                ],
            ),
            (
                "en_message",
                ["reverse", "reverse"],
                [
                    ["Hello {name}", "Hi everyone", "Gentlemen"],
                    ["Hello", "Hi everybody", "Hi everyone"],
                    ["Hello {name}", "Hi everybody", "Ladies"],
                ],
            ),
            (
                "fr_message",
                ["natural", "natural", "natural"],
                [
                    ["Bonjour", "Bonjour à tous", "Bonjour tout le monde"],
                    ["Bonjour Mme {name}", "Bonjour Mesdames", "Mesdames"],
                    ["Bonjour M. {name}", "Bonjour Messieurs", "Messieurs"],
                ],
            ),
            (
                "en_message",
                ["reverse", "reverse", "reverse"],
                [
                    ["Hello", "Hi everybody", "Hi everyone"],
                    ["Hello {name}", "Hi everybody", "Ladies"],
                    ["Hello {name}", "Hi everyone", "Gentlemen"],
                ],
            ),
        ],
    )
    def test_message_toggle(self, fixture_message, orientations, expected, request):
        message = request.getfixturevalue(fixture_message)
        for orientation in orientations:
            message.toggle(orientation)
        assert message.get_principal() == expected[0]
        assert message.get_variant(1) == expected[1]
        assert message.get_variant(2) == expected[2]

    @pytest.mark.parametrize(
        "fixture_message, orientation, expected",
        [
            ("fr_message", "plus", "direction must be either 'natural' or 'reverse'"),
            ("en_message", "minus", "direction must be either 'natural' or 'reverse'"),
        ],
    )
    def test_message_toggle_failed(
        self, fixture_message, orientation, expected, request
    ):
        message = request.getfixturevalue(fixture_message)
        with pytest.raises(ValueError, match=re.escape(expected)):
            message.toggle(orientation)

    def test_message_toggle_none_natural(self, empty_message):
        empty_message.toggle("natural")
        assert empty_message.default == ""

    def test_message_toggle_none_reverse(self, empty_message):
        empty_message.toggle("reverse")
        assert empty_message.default == ""


class TestMessageFormat:
    @pytest.mark.parametrize(
        "params, expected",
        [
            ({"name": "John"}, "Hello, John!"),
            ({"option": 1, "name": "John"}, "Hi, John!"),
            ({"token": 1, "name": "user", "count": 5}, "Hello, 5 users!"),
            ({"option": 1, "token": 1, "name": "user", "count": 3}, "Hi, 3 users!"),
        ],
    )
    def test_message_format(self, params, expected) -> None:
        """Test formatting a message with variables."""
        message = Message(
            id="greeting",
            default="Hello, {name}!",
            options={1: "Hi, {name}!"},
            default_plurals={1: "Hello, {count} {name}s!"},
            options_plurals={1: {1: "Hi, {count} {name}s!"}},
        )

        # Test formatting the main translation
        assert message.format(**params) == expected

    @pytest.mark.parametrize(
        "params, expected",
        [
            ({}, "Missing variable 'name' for message 'greeting'"),
            (
                {"option": 1, "nom": "John"},
                "Missing variable 'name' for message 'greeting'",
            ),
            (
                {"option": 1, "token": 1, "name": "John", "compte": 3},
                "Missing variable 'count' for message 'greeting'",
            ),
        ],
    )
    def test_message_format_failed(self, params, expected) -> None:
        """Test formatting a message with variables."""

        message = Message(
            id="greeting",
            default="Hello, {name}!",
            options={1: "Hi, {name}!"},
            default_plurals={1: "Hello, {count} {name}s!"},
            options_plurals={1: {1: "Hi, {count} {name}s!"}},
        )

        # Test formatting the main translation
        with pytest.raises(KeyError, match=re.escape(expected)):
            message.format(**params)

    # 7 Testing conversions

    @pytest.mark.parametrize(
        "fixture_message, expected",
        [
            (
                "fr_message",
                {
                    "messages": [
                        ["Bonjour", "Bonjour Mme {name}", "Bonjour M. {name}"],
                        ["Bonjour à tous", "Bonjour Mesdames", "Bonjour Messieurs"],
                        ["Bonjour tout le monde", "Mesdames", "Messieurs"],
                    ],
                    "metadata": {
                        "version": "0.1.0",
                        "language": "fr-FR",
                        "locations": [],
                        "flags": ["python-format"],
                        "user_comments": [
                            "In French, Greeting message to one or more..."
                        ],
                        "auto_comments": ["1000_000", "1000_001", "1000_02"],
                        "singular_count": 3,
                        "plural_counts": [3, 3],
                    },
                },
            ),
            (
                "en_message",
                {
                    "messages": [
                        ["Hello", "Hello {name}", "Hello {name}"],
                        ["Hi everybody", "Hi everybody", "Hi everyone"],
                        ["Hi everyone", "Ladies", "Gentlemen"],
                    ],
                    "metadata": {
                        "version": "0.1.0",
                        "language": "en",
                        "locations": [],
                        "flags": ["python-format"],
                        "user_comments": ["Greeting message to one or more..."],
                        "auto_comments": ["1000_000", "1000_001", "1000_02"],
                        "singular_count": 3,
                        "plural_counts": [3, 3],
                    },
                },
            ),
        ],
    )
    def test_message_to_i18n_tools_format(self, fixture_message, expected, request):
        message = request.getfixturevalue(fixture_message)
        assert message.to_i18n_tools_format() == expected

    @pytest.mark.parametrize(
        "fixture_message, source, params",
        [
            (
                "fr_message",
                {
                    "messages": [
                        ["Bonjour", "Bonjour Mme {name}", "Bonjour M. {name}"],
                        ["Bonjour à tous", "Bonjour Mesdames", "Bonjour Messieurs"],
                        ["Bonjour tout le monde", "Mesdames", "Messieurs"],
                    ],
                    "metadata": {
                        "version": "0.1.0",
                        "locations": [],
                        "flags": ["python-format"],
                        "user_comments": [
                            "In French, Greeting message to one or more..."
                        ],
                        "singular_count": 3,
                        "plural_counts": [3, 3],
                    },
                },
                (["default", None], ["options", 1], ["options", 2]),
            ),
            (
                "en_message",
                {
                    "messages": [
                        ["Hello", "Hello {name}", "Hello {name}"],
                        ["Hi everybody", "Hi everybody", "Hi everyone"],
                        ["Hi everyone", "Ladies", "Gentlemen"],
                    ],
                    "metadata": {
                        "version": "0.1.0",
                        "locations": [],
                        "flags": ["python-format"],
                        "user_comments": ["Greeting message to one or more..."],
                        "singular_count": 3,
                        "plural_counts": [3, 3],
                    },
                },
                (["default", None], ["options", 1], ["options", 2]),
            ),
            (
                "fr_message",
                {
                    "messages": [
                        ["Bonjour", "Bonjour Mme {name}", "Bonjour M. {name}"],
                        ["Bonjour à tous", "Bonjour Mesdames", "Bonjour Messieurs"],
                        ["Bonjour tout le monde", "Mesdames", "Messieurs"],
                    ],
                    "metadata": {
                        "version": "0.1.0",
                        "language": "fr-FR",
                        "locations": [],
                        "flags": ["python-format"],
                        "user_comments": [
                            "In French, Greeting message to one or more..."
                        ],
                        "singular_count": 3,
                        "plural_counts": [3, 3],
                    },
                },
                (
                    ["default_plurals", 1],
                    ["options_plurals", [1, 2]],
                    ["metadata", "language"],
                ),
            ),
            (
                "en_message",
                {
                    "messages": [
                        ["Hello", "Hello {name}", "Hello {name}"],
                        ["Hi everybody", "Hi everybody", "Hi everyone"],
                        ["Hi everyone", "Ladies", "Gentlemen"],
                    ],
                    "metadata": {
                        "version": "0.1.0",
                        "language": "en",
                        "locations": [],
                        "flags": ["python-format"],
                        "user_comments": ["Greeting message to one or more..."],
                        "singular_count": 3,
                        "plural_counts": [3, 3],
                    },
                },
                (
                    ["default_plurals", 1],
                    ["options_plurals", [1, 2]],
                    ["metadata", "language"],
                ),
            ),
        ],
    )
    def test_message_class_from_i18n_tools(
        self, fixture_message, source, params, request
    ):
        verification = request.getfixturevalue(fixture_message)
        message = Message.from_i18n_tools("1000", source)
        for attr, path in params:
            if path is None:
                assert message.__getattribute__(attr) == verification.__getattribute__(
                    attr
                )
            else:
                assert (
                    message.__getattribute__(attr)[path]
                    == verification.__getattribute__(attr)[path]
                )

    @pytest.mark.parametrize(
        "option, result",
        [(1, [["name"], ["count", "name"]]), (0, [["name"], ["count", "name"]])],
    )
    def test_message_get_format_variables(self, option, result):
        message = message = Message(
            id="greeting",
            default="Hello, {name}!",
            options={1: "Hi, {name}!"},
            default_plurals={1: "Hello, {count} {name}s!"},
            options_plurals={1: {1: "Hi, {count} {name}s!"}},
        )
        assert message.get_format_variables(option) == result

    def test_message_get_format_variables_failed(self):
        message = message = Message(
            id="greeting",
            default="Hello, {name}!",
            options={1: "Hi, {name}!"},
            default_plurals={1: "Hello, {count} {name}s!"},
            options_plurals={1: {1: "Hi, {count} {name}s!"}},
        )
        with pytest.raises(
            IndexError, match=re.escape("The variant location (2) is out of range")
        ):
            message.get_format_variables(2)


class TestMessageProperties:
    def test_has_variants_properties(self, fr_message, empty_message):
        # Existing French message has options and options_plurals
        assert fr_message.has_variants is True
        # Empty message has no variants
        assert empty_message.has_variants is False
        # A message with only options should report variants
        m = Message(id="x1", default="Hi", options={1: "Hello {who}"})
        assert m.has_variants is True
        # A message with only options_plurals should also report variants
        m2 = Message(id="x2", default="Hi", options_plurals={1: {1: "Hellos"}})
        assert m2.has_variants is True

    def test_has_plurals_properties(self, fr_message, empty_message):
        # Existing French message has default_plurals and options_plurals
        assert fr_message.has_plurals is True
        # Empty message has no plurals
        assert empty_message.has_plurals is False
        # A message with only default_plurals should report plurals
        m = Message(id="x3", default="Hi", default_plurals={1: "Hellos"})
        assert m.has_plurals is True
        # A message with only options_plurals should report plurals
        m2 = Message(id="x4", default="Hi", options_plurals={1: {1: "Hellos"}})
        assert m2.has_plurals is True


class TestMessageEquality:
    def test_message_equality_true(self):
        m1 = Message(
            id="2000",
            default="Hello",
            options={1: "Hi {name}"},
            default_plurals={1: "Hellos"},
            options_plurals={1: {1: "Hi {name}s"}},
            context="greet",
            metadata={
                "version": "0.1.0",
                "language": "en",
                "location": [],
                "flags": ["python-format"],
                "user_comments": [],
                "count": {"singular": 1, "plurals": [1]},
            },
        )
        m2 = Message(
            id="2000",
            default="Hello",
            options={1: "Hi {name}"},
            default_plurals={1: "Hellos"},
            options_plurals={1: {1: "Hi {name}s"}},
            context="greet",
            metadata={
                "version": "0.1.0",
                "language": "en",
                "location": [],
                "flags": ["python-format"],
                "user_comments": [],
                "count": {"singular": 1, "plurals": [1]},
            },
        )
        assert m1 == m2
        assert m1.equals(m2) is True

    def test_message_equality_false_on_property_difference(self, fr_message):
        # Copy but with different default
        m_other = Message(
            id=fr_message.id,
            default=fr_message.default + "!",
            options=dict(fr_message.options),
            default_plurals=dict(fr_message.default_plurals),
            options_plurals=(
                {k: dict(v) for k, v in fr_message.options_plurals.items()}
                if isinstance(fr_message.options_plurals, dict)
                else fr_message.options_plurals.to_dict()
            ),
            context=fr_message.context,
            metadata=(
                fr_message.metadata.to_dict()
                if hasattr(fr_message.metadata, "to_dict")
                else dict(fr_message.metadata)
            ),
        )
        assert (fr_message == m_other) is False
        assert fr_message.equals(m_other) is False

    def test_message_equality_non_message(self):
        m = Message(id="x", default="a")
        assert (m == 1) is False or (m == 1) is NotImplemented  # ensure no crash
        assert m.equals(1) is False

        # --- Tests for similarity (is_similar) ---

    def test_message_similarity_same_set_different_arrangement(self):
        # m1: default has A, variant has B, plurals have C, variant plurals have D
        m1 = Message(
            id="s1",
            default="Hello",
            options={1: "Hi"},
            default_plurals={1: "Hellos"},
            options_plurals={1: {1: "His"}},
        )
        # m2: move strings around between default and variants but keep the same set
        m2 = Message(
            id="s2",
            default="Hi",  # moved from variant to default
            options={1: "Hello"},  # moved from default to variant
            default_plurals={1: "His"},  # moved from variant plurals to default plurals
            options_plurals={
                1: {1: "Hellos"}
            },  # moved from default plurals to variant plurals
        )
        # Exact equality should fail, but similarity should pass
        assert (m1 == m2) is False
        assert m1.is_similar(m2) is True

    def test_message_similarity_false_on_content_difference(self):
        m1 = Message(id="s3", default="Hello", options={1: "Hi"})
        m2 = Message(id="s4", default="Hello", options={1: "Hey"})
        assert m1.is_similar(m2) is False

    def test_message_similarity_non_message(self):
        m = Message(id="s5", default="Hello")
        assert m.is_similar(123) is False


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
        assert empty_message.options_plurals.isomorph({})

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

    def test_failed_init(self):
        with pytest.raises(ValueError):
            Message("1001", "A failed", options={2: "Failed index"})
