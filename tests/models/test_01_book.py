"""
Minimal test file for Book model using shared fixtures from tests/models/conftest.py
"""

import re
import json
import pytest

from i18n_tools.converter import message_to_i18n_tools_format
from i18n_tools.models.corpus import Book, Message

# Using fixtures: fr_fr_book, en_us_book, en_gb_book, it_it_book from local conftest.py
@pytest.fixture
def fr_fr_i18t_directory(tmp_path, fr_fr_messages):
    """Écrit fr_fr_messages dans test.json.i18t et retourne le répertoire en str."""
    data = {
        msgid: message_to_i18n_tools_format(msg)["messages"]
        for msgid, msg in fr_fr_messages.items()
    }
    (tmp_path / "test.json.i18t").write_text(json.dumps(data), encoding="utf-8")
    return str(tmp_path)

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

    def test_book_is_iterable(self, fr_fr_book):
        # Ensure Book yields Message instances and order matches insertion order
        msgs = list(fr_fr_book)
        assert len(msgs) == len(fr_fr_book.messages)
        # All yielded elements are Message
        assert all(isinstance(m, Message) for m in msgs)
        # Order correspondence: ids in same order as dict values()
        ids_from_iter = [m.id for m in msgs]
        ids_from_dict = list(fr_fr_book.messages.keys())
        assert ids_from_iter == ids_from_dict

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
        assert book.language == language
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


class TestBookLoad:

    def test_book_load_nominal(self, fr_fr_i18t_directory):
        """Cas nominal : Book peuplé avec les 10 messages fr-FR."""
        book = Book(language="fr-FR", domain="test")
        book.load(fr_fr_i18t_directory)
        assert len(list(book)) == 10
        assert set(book.messages.keys()) == {
            "1100", "1101", "1102", "1103", "1104",
            "1105", "1106", "1107", "1108", "1109",
        }

    def test_book_load_language_assigned(self, fr_fr_i18t_directory):
        """Chaque message chargé porte la langue du Book."""
        book = Book(language="fr-FR", domain="test")
        book.load(fr_fr_i18t_directory)
        for msg in book:
            assert msg.metadata["language"] == "fr-FR"

    def test_book_load_file_not_found(self, tmp_path):
        """Répertoire sans fichier correspondant → FileNotFoundError."""
        book = Book(language="fr-FR", domain="test")
        with pytest.raises(FileNotFoundError):
            book.load(str(tmp_path))

    def test_book_load_integrity_error(self, tmp_path):
        """Fichier à matrice mal formée → ValueError."""
        (tmp_path / "test.json.i18t").write_text(
            json.dumps({"10001": "not-a-list"}), encoding="utf-8"
        )
        book = Book(language="fr-FR", domain="test")
        with pytest.raises(ValueError):
            book.load(str(tmp_path))


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
                        "user_comments": ["Message sur des chiots"],
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
                        "user_comments": ["Message sur des chattons"],
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
        assert book.get(msg_id).get_principal() == msg_main
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
                        "user_comments": ["Message sur des chiots"],
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
                        "user_comments": ["Message sur des chiots"],
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


# New tests for enhanced metadata and statistics in Book
@pytest.mark.parametrize(
    "fixture_book", ["fr_fr_book", "en_us_book", "en_gb_book", "it_it_book"]
)
def test_book_metadata_defaults_and_language_domain(fixture_book, request):
    book = request.getfixturevalue(fixture_book)
    # Core attributes now stored on instance
    assert isinstance(book.language, str)
    assert isinstance(book.domain, str)
    assert isinstance(book.format, str)
    # These keys should NOT be in metadata anymore
    assert not book.metadata.is_key("language")
    assert not book.metadata.is_key("domain")
    assert not book.metadata.is_key("format")
    # Default values for remaining metadata
    assert book.metadata.get("project_id_version", None) == "i18n-tools 1.0"
    assert book.metadata.get("report_msgid_bugs_to", None) == "bugs@example.com"
    assert book.metadata.get("pot_creation_date", None) == ""
    assert book.metadata.get("language_team", None) == ""
    assert book.metadata.get("header_comment", None) == ""
    # Statistics exist and initialized or computed
    assert book.metadata.dict_paths().__contains__(
        ["statistics", "total_messages"]
    ) and isinstance(book.metadata[["statistics", "total_messages"]], int)
    assert book.metadata.dict_paths().__contains__(
        ["statistics", "total_words"]
    ) and isinstance(book.metadata[["statistics", "total_words"]], int)
    # Count backward compatibility
    assert book.metadata[["count", "messages"]] == len(book.messages)


def _make_simple_message(lang: str) -> Message:
    return Message(
        id="tmp1",
        default="Hello world",
        options={1: "Hello {who}"},
        default_plurals={1: "Hello worlds"},
        options_plurals={1: {1: "Hello {who}s"}},
        metadata={
            "version": "0.1.0",
            "language": lang,
            "location": [],
            "flags": ["python-format"],
            "user_comments": [],
            "count": {"singular": 1, "plurals": [1]},
        },
    )


@pytest.mark.parametrize(
    "fixture_book,lang",
    [
        ("fr_fr_book", "fr-FR"),
        ("en_us_book", "en-US"),
        ("en_gb_book", "en-GB"),
        ("it_it_book", "it-IT"),
    ],
)
def test_book_statistics_update_on_add_and_remove(fixture_book, lang, request):
    book = request.getfixturevalue(fixture_book)
    initial_msgs = book.metadata[["statistics", "total_messages"]]
    initial_words = book.metadata[["statistics", "total_words"]]

    # Add a simple message and verify stats updated
    msg = _make_simple_message(lang)
    book.add(book.domain, [msg])
    assert book.metadata[["statistics", "total_messages"]] == initial_msgs + 1
    # The delta words should equal counts from msg strings
    # default (2 words) + default_plural (2) + option(2) + option_plural(2) = 8 words
    assert book.metadata[["statistics", "total_words"]] == initial_words + 8

    # Remove and verify rollback
    book.remove(msg.id)
    assert book.metadata[["statistics", "total_messages"]] == initial_msgs
    assert book.metadata[["statistics", "total_words"]] == initial_words


@pytest.mark.parametrize(
    "key,value,expected_path,expected_value",
    [
        ("header_comment", "Global notes", ["header_comment"], "Global notes"),
        ("header_comment", None, ["header_comment"], ""),
        (["statistics", "total_words"], 1234, ["statistics", "total_words"], 1234),
        (["statistics", "total_words"], None, ["statistics", "total_words"], 0),
        ("custom_meta", {"a": 1}, ["custom_meta"], {"a": 1}),
    ],
)
@pytest.mark.skip(reason="ndict_tools equality has be rewieved")
@pytest.mark.parametrize("fixture_book", ["fr_fr_book"])  # one is enough for API checks
def test_book_set_metadata_update_and_reset(
    fixture_book, key, value, expected_path, expected_value, request
):
    book = request.getfixturevalue(fixture_book)
    book.set_metadata(key, value)
    # Access metadata using path semantics supported by StrictNestedDictionary
    # For top-level keys, expected_path is [key]
    if len(expected_path) == 1:
        assert book.metadata[expected_path[0]] == expected_value
    else:
        assert book.metadata[expected_path] == expected_value


@pytest.mark.parametrize(
    "key,value,expected_exception",
    [
        (None, "x", KeyError),
        ("does_not_exist", None, KeyError),
        (["not", "there"], 42, KeyError),
        (123, "x", TypeError),
        ({"a": 1}, "x", TypeError),
    ],
)
@pytest.mark.parametrize("fixture_book", ["fr_fr_book"])  # check failure scenarios
def test_book_set_metadata_update_and_reset_failed(
    fixture_book, key, value, expected_exception, request
):
    book = request.getfixturevalue(fixture_book)
    with pytest.raises(expected_exception):
        book.set_metadata(key, value)


# --- New tests: getters/add/update/remove for language, domain, format ---


@pytest.mark.parametrize(
    "fixture_book, expected_lang, expected_domain, expected_format",
    [
        ("fr_fr_book", "fr-FR", "test", "json"),
        ("en_us_book", "en-US", "test", "json"),
    ],
)
def test_attribute_getters(
    fixture_book, expected_lang, expected_domain, expected_format, request
):
    book = request.getfixturevalue(fixture_book)
    assert book.get_language() == expected_lang
    assert book.get_domain() == expected_domain
    assert book.get_format() == expected_format


def test_add_attribute_methods_fail_when_already_set(fr_fr_book):
    # add_language when already set
    with pytest.raises(ValueError, match="Language is already set for this book"):
        fr_fr_book.add_language("fr")
    # add_domain when already set
    with pytest.raises(ValueError, match="Domain is already set for this book"):
        fr_fr_book.add_domain("test")
    # add_format when already set
    with pytest.raises(ValueError, match="Format is already set for this book"):
        fr_fr_book.add_format("json")


def test_remove_attributes_then_add_again():
    # create a minimal empty book
    book = Book(domain="d", language="fr-FR")
    # remove then add
    book.remove_language()
    assert book.language is None
    book.add_language("fr")  # normalized to fr-FR
    assert book.language == "fr"

    book.remove_domain()
    assert book.domain is None
    book.add_domain("d2")
    assert book.domain == "d2"

    book.remove_format()
    assert book.format is None
    book.add_format("yaml")
    assert book.format == "yaml"


def test_update_language_success_on_empty_book():
    book = Book(domain="d", language="fr-FR")
    # No messages: update freely
    book.update_language("fr")
    assert book.language == "fr"  # normalization and same
    book.update_language("en-us")
    assert book.language == "en-US"


def test_update_language_failure_on_mismatch(fr_fr_book, en_message):
    # ensure en_message language mismatches fr-FR after normalization
    assert en_message.metadata["language"] in ("en", "en-US", "en-GB")
    # Try to update the book language to en-US while it contains fr-FR messages -> should fail
    with pytest.raises(
        ValueError,
        match=r"Language of message \(.*\) is not compatible with updated book language \('en-US'\)",
    ):
        fr_fr_book.update_language("en-US")


def test_update_domain_and_format_success(fr_fr_book):
    fr_fr_book.update_domain("animals")
    assert fr_fr_book.domain == "animals"
    assert fr_fr_book.format == "json"
    assert fr_fr_book.filename == "animals.json.i18t"
    fr_fr_book.update_format("yaml")
    assert fr_fr_book.format == "yaml"
    assert fr_fr_book.filename == "animals.yaml.i18t"


def test_save(fr_fr_book):
    fr_fr_book.save("tmp")
