"""
Minimal test file for Book model using shared fixtures from tests/models/conftest.py
"""

import re

import pytest

from i18n_tools.models.corpus import Book, Message

# Using fixtures: fr_fr_book, en_us_book, en_gb_book, it_it_book from local conftest.py


# Testing books attributes


class TestBook:

    @pytest.mark.parametrize(
        "fixture_book", ["fr_fr_book", "en_us_book", "en_gb_book", "it_it_book"]
    )
    def test_book_id(self, fixture_book, request):
        book = request.getfixturevalue(fixture_book)
        for id, message in book.messages.items():
            assert id == message.id
        assert len(book.messages) == 10

    @pytest.mark.parametrize(
        "fixture_book, language",
        [
            ("fr_fr_book", "fr-FR"),
            ("en_us_book", "en-US"),
            ("en_gb_book", "en-GB"),
            ("it_it_book", "it-IT"),
        ],
    )
    def test_book_language(self, fixture_book, language, request):
        book = request.getfixturevalue(fixture_book)
        assert book.metadata["language"] == language
        assert book.messages["1100"].metadata["language"] == language

    # Be careful: messages created for books in the file conftest.py file have deliberately incorrect counters.
    @pytest.mark.parametrize(
        "fixture_book, message_id, c_singular, c_plurals",
        [
            ("fr_fr_book", "1100", 4, [2, 2, 3, 2]),
            ("en_us_book", "1108", 4, [2, 2, 2, 2]),
            ("en_gb_book", "1101", 4, [2, 2, 2, 3]),
            ("it_it_book", "1104", 4, [2, 2, 2, 2]),
        ],
    )
    def test_book_count(self, fixture_book, message_id, c_singular, c_plurals, request):
        book = request.getfixturevalue(fixture_book)
        assert book.messages[message_id].metadata[["count", "singular"]] == c_singular
        assert book.messages[message_id].metadata[["count", "plurals"]] == c_plurals

    @pytest.mark.parametrize(
        "fixture_book, message_id, option, variables",
        [
            ("fr_fr_book", "1100", 0, [[], [], []]),
            (
                "en_us_book",
                "1100",
                3,
                [["flower", "region"], ["flower", "region"], ["flower", "region"]],
            ),
            ("it_it_book", "1101", 2, [["location"], ["location"], ["location"]]),
            ("en_gb_book", "1103", 2, [["purpose"], ["purpose"], ["purpose"]]),
            ("en_gb_book", "1103", 1, [["automaton"], ["automaton"], ["automaton"]]),
            ("fr_fr_book", "1103", 2, [["purpose"], ["purpose"], ["purpose"]]),
            ("fr_fr_book", "1103", 1, [["automaton"], ["automaton"], ["automaton"]]),
            ("it_it_book", "1103", 2, [["purpose"], ["purpose"], ["purpose"]]),
            ("it_it_book", "1103", 1, [["automaton"], ["automaton"], ["automaton"]]),
            ("en_us_book", "1103", 2, [["purpose"], ["purpose"], ["purpose"]]),
            ("en_us_book", "1103", 1, [["automaton"], ["automaton"], ["automaton"]]),
        ],
    )
    def test_book_variables(self, fixture_book, message_id, option, variables, request):
        book = request.getfixturevalue(fixture_book)
        assert book.messages[message_id].get_format_variables(option) == variables

    def test_book_creation_domain_failed(self, fr_message):
        with pytest.raises(KeyError, match=re.escape("No domain specified")):
            Book(fr_message, language="fr-FR")

    def test_book_creation_language_failed(self, fr_message):
        with pytest.raises(KeyError, match=re.escape("No language specified")):
            Book(fr_message, domain="test")

    def test_book_creation_language_mismatch(self, fr_message):
        with pytest.raises(
            ValueError,
            match=re.escape(
                "Language of message 1000 is not compatible with this book language"
            ),
        ):
            Book(fr_message, domain="test", language="fr")


@pytest.mark.parametrize(
    "fixture_book, id, expected",
    [
        (
            "fr_fr_book",
            "1100",
            [
                ("default", None, None, "Voici une fleur"),
                ("default_plurals", 1, None, "Voici des fleurs"),
            ],
        ),
        (
            "fr_fr_book",
            "1100",
            [
                ("options", 2, None, "Voici une {flower} rare"),
                ("options_plurals", 2, 3, "Voici plusieurs {flower} rares"),
            ],
        ),
        ("fr_fr_book", "1000", None),
    ],
)
def test_book_get(fixture_book, id, expected, request):
    book = request.getfixturevalue(fixture_book)
    if expected is None:
        assert book.get(id) == None
    else:
        for attribute, opt, token, value in expected:
            if opt is None:
                assert getattr(book.get(id), attribute) == value
            elif token is None:
                assert getattr(book.get(id), attribute)[opt] == value
            else:
                assert getattr(book.get(id), attribute)[[opt, token]] == value


@pytest.mark.parametrize(
    "fixture_book, messages, expected",
    [
        (
            "fr_fr_book",
            [
                Message(
                    id="1000",
                    default="Voici un chiot",
                    options={
                        1: "Voici un joli {puppy}",
                        2: "Voici un chiot {puppy} rare",
                        3: "Voici un chiot {puppy} de la région {region}",
                    },
                    default_plurals={
                        1: "Voici des chiots",
                        2: "Voici deux chiots",
                    },
                    options_plurals={
                        1: {
                            1: "Voici de jolis chiots {puppy}",
                            2: "Voici deux beaux chiots {puppy}",
                        },
                        2: {
                            1: "Voici des chiots {puppy} rares",
                            2: "Voici deux chiots {puppy} rares",
                            3: "Voici plusieurs chiots {puppy} rares",
                        },
                        3: {
                            1: "Voici des chiots {puppy} de la région {region}",
                            2: "Voici deux chiots {puppy} de la région {region}",
                        },
                    },
                    metadata={
                        "version": "0.1.0",
                        "language": "fr-FR",
                        "location": [],
                        "flags": ["python-format"],
                        "comments": "Message sur des chiots",
                        "count": {"singular": 3, "plurals": [2, 3, 2]},
                    },
                ),
                Message(
                    id="1001",
                    default="Voici un chatton",
                    options={
                        1: "Voici un joli {kitten}",
                        2: "Voici un chatton {kitten} rare",
                        3: "Voici un chatton {kitten} de la région {region}",
                    },
                    default_plurals={
                        1: "Voici des chattons",
                        2: "Voici deux chattons",
                    },
                    options_plurals={
                        1: {
                            1: "Voici de jolis chattons {kitten}",
                            2: "Voici deux beaux chattons {kitten}",
                        },
                        2: {
                            1: "Voici des chattons {kitten} rares",
                            2: "Voici deux chattons {kitten} rares",
                            3: "Voici plusieurs chattons {kitten} rares",
                        },
                        3: {
                            1: "Voici des chattons {kitten} de la région {region}",
                            2: "Voici deux chattons {kitten} de la région {region}",
                        },
                    },
                    metadata={
                        "version": "0.1.0",
                        "language": "fr-FR",
                        "location": [],
                        "flags": ["python-format"],
                        "comments": "Message sur des chattons",
                        "count": {"singular": 3, "plurals": [2, 3, 2]},
                    },
                ),
            ],
            [
                [
                    "1000",
                    ["Voici un chiot", "Voici des chiots", "Voici deux chiots"],
                    [
                        [
                            "Voici un joli {puppy}",
                            "Voici de jolis chiots {puppy}",
                            "Voici deux beaux chiots {puppy}",
                        ],
                        [
                            "Voici un chiot {puppy} rare",
                            "Voici des chiots {puppy} rares",
                            "Voici deux chiots {puppy} rares",
                            "Voici plusieurs chiots {puppy} rares",
                        ],
                        [
                            "Voici un chiot {puppy} de la région {region}",
                            "Voici des chiots {puppy} de la région {region}",
                            "Voici deux chiots {puppy} de la région {region}",
                        ],
                    ],
                ],
                [
                    "1001",
                    ["Voici un chatton", "Voici des chattons", "Voici deux chattons"],
                    [
                        [
                            "Voici un joli {kitten}",
                            "Voici de jolis chattons {kitten}",
                            "Voici deux beaux chattons {kitten}",
                        ],
                        [
                            "Voici un chatton {kitten} rare",
                            "Voici des chattons {kitten} rares",
                            "Voici deux chattons {kitten} rares",
                            "Voici plusieurs chattons {kitten} rares",
                        ],
                    ],
                ],
            ],
        )
    ],
)
def test_book_add(fixture_book, messages, expected, request):
    book = request.getfixturevalue(fixture_book)
    book.add("test", messages)
    for msg_id, msg_main, msg_variants in expected:
        assert book.get(msg_id).get_main() == msg_main
        for index, msg_variant in enumerate(msg_variants):
            assert book.get(msg_id).get_variant(index + 1) == msg_variant


@pytest.mark.parametrize(
    "fixture_book, domain, messages, expected",
    [
        (
            "fr_fr_book",
            "animals",
            [],
            "Domain of message 'animals' is not compatible with this book domain 'test'",
        ),
        (
            "fr_fr_book",
            "test",
            [
                Message(
                    id="1000",
                    default="Voici un chiot",
                    options={
                        1: "Voici un joli {puppy}",
                        2: "Voici un chiot {puppy} rare",
                        3: "Voici un chiot {puppy} de la région {region}",
                    },
                    default_plurals={
                        1: "Voici des chiots",
                        2: "Voici deux chiots",
                    },
                    options_plurals={
                        1: {
                            1: "Voici de jolis chiots {puppy}",
                            2: "Voici deux beaux chiots {puppy}",
                        },
                        2: {
                            1: "Voici des chiots {puppy} rares",
                            2: "Voici deux chiots {puppy} rares",
                            3: "Voici plusieurs chiots {puppy} rares",
                        },
                        3: {
                            1: "Voici des chiots {puppy} de la région {region}",
                            2: "Voici deux chiots {puppy} de la région {region}",
                        },
                    },
                    metadata={
                        "version": "0.1.0",
                        "language": "fr-BE",
                        "location": [],
                        "flags": ["python-format"],
                        "comments": "Message sur des chiots",
                        "count": {"singular": 3, "plurals": [2, 3, 2]},
                    },
                )
            ],
            "Language of message (1000 : 'fr-BE') is not compatible with this book language ('fr-FR')",
        ),
        (
            "fr_fr_book",
            "test",
            [
                Message(
                    id="1100",
                    default="Voici un chiot",
                    options={
                        1: "Voici un joli {puppy}",
                        2: "Voici un chiot {puppy} rare",
                        3: "Voici un chiot {puppy} de la région {region}",
                    },
                    default_plurals={
                        1: "Voici des chiots",
                        2: "Voici deux chiots",
                    },
                    options_plurals={
                        1: {
                            1: "Voici de jolis chiots {puppy}",
                            2: "Voici deux beaux chiots {puppy}",
                        },
                        2: {
                            1: "Voici des chiots {puppy} rares",
                            2: "Voici deux chiots {puppy} rares",
                            3: "Voici plusieurs chiots {puppy} rares",
                        },
                        3: {
                            1: "Voici des chiots {puppy} de la région {region}",
                            2: "Voici deux chiots {puppy} de la région {region}",
                        },
                    },
                    metadata={
                        "version": "0.1.0",
                        "language": "fr-FR",
                        "location": [],
                        "flags": ["python-format"],
                        "comments": "Message sur des chiots",
                        "count": {"singular": 3, "plurals": [2, 3, 2]},
                    },
                )
            ],
            "Message with id (1100) is already present in this book",
        ),
    ],
)
def test_book_add_failed(fixture_book, domain, messages, expected, request):
    book = request.getfixturevalue(fixture_book)
    with pytest.raises(ValueError, match=re.escape(expected)):
        book.add(domain, messages)


@pytest.mark.parametrize(
    "fixture_book, messages_id, expected",
    [
        ("fr_fr_book", ["1100"], 9),
        ("fr_fr_book", ["1100", "1101"], 8),
        ("en_gb_book", ["1102"], 9),
        ("en_gb_book", ["1102", "1103"], 8),
        ("fr_fr_book", ["1100", "1101", "1104"], 7),
        ("en_us_book", ["1105"], 9),
        ("it_it_book", ["1106"], 9),
        ("it_it_book", ["1106", "1107"], 8),
        ("en_us_book", ["1105", "1108"], 8),
        ("en_us_book", ["1105", "1108", "1109"], 7),
        ("en_us_book", ["1105", "1100", "1108", "1104", "1109", "1102"], 4),
    ],
)
def test_book_remove(fixture_book, messages_id, expected, request):
    book = request.getfixturevalue(fixture_book)
    for message_id in messages_id:
        book.remove(message_id)
        assert book.get(message_id) is None
    assert book.metadata[["count", "messages"]] == expected


def test_book_remove_failed(fr_fr_book):
    with pytest.raises(
        ValueError, match=re.escape("Message identifier 1000 is not in this book")
    ):
        fr_fr_book.remove("1000")
