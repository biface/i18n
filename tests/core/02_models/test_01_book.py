"""
Minimal test file for Book model using shared fixtures from tests/models/conftest.py
"""

import json
import re

import pytest
from helpers import as_plain

from i18n_tools import __version__
from i18n_tools._finding import Finding
from i18n_tools.converter import message_to_i18n_tools_format
from i18n_tools.exceptions import FormatError, I18nToolsWarning, MessageError
from i18n_tools.models.book import Book
from i18n_tools.models.message import Declension, Location, Message


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


def _make_simple_message(lang: str) -> Message:
    return Message(
        id="tmp1",
        principal=Declension("Hello world", ("Hello worlds",)),
        variants=[Declension("Hello {who}", ("Hello {who}s",))],
        metadata={
            "version": __version__,
            "language": lang,
            "locations": [],
            "flags": ["python-format"],
            "user_comments": [],
        },
    )


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

    @pytest.mark.parametrize(
        "fixture_book, message_id, declensions, plurals",
        [
            ("fr_fr_book", "1100", 4, [2, 2, 3, 2]),
            ("en_us_book", "1108", 4, [2, 2, 2, 2]),
            ("en_gb_book", "1101", 4, [2, 2, 2, 3]),
            ("it_it_book", "1104", 4, [2, 2, 2, 2]),
        ],
    )
    def test_book_message_structure(
        self, fixture_book, message_id, declensions, plurals, request
    ):
        message = request.getfixturevalue(fixture_book).messages[message_id]
        all_declensions = (message.principal, *message.variants)
        assert len(all_declensions) == declensions
        assert [len(declension.plurals) for declension in all_declensions] == plurals

    @pytest.mark.parametrize(
        "fixture_book, message_id, variant, tokens",
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
    def test_book_tokens(self, fixture_book, message_id, variant, tokens, request):
        book = request.getfixturevalue(fixture_book)
        assert book.messages[message_id].get_tokens(variant) == tokens

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


class TestBookGet:
    @pytest.mark.parametrize(
        "fixture_book, id, expected",
        [
            (
                "fr_fr_book",
                "1100",
                [(0, 0, "Voici une fleur"), (1, 0, "Voici des fleurs")],
            ),
            (
                "fr_fr_book",
                "1100",
                [
                    (0, 2, "Voici une {flower} rare"),
                    (3, 2, "Voici plusieurs {flower} rares"),
                ],
            ),
            ("fr_fr_book", "1000", None),
        ],
    )
    def test_book_get(self, fixture_book, id, expected, request):
        book = request.getfixturevalue(fixture_book)
        if expected is None:
            assert book.get(id) == None
        else:
            for segment, variant, value in expected:
                assert book.get(id).get_segment(segment, variant) == value


class TestBookAdd:
    @pytest.mark.parametrize(
        "fixture_book, messages, expected",
        [
            (
                "fr_fr_book",
                [
                    Message(
                        id="1000",
                        principal=Declension(
                            "Voici un chiot", ("Voici des chiots", "Voici deux chiots")
                        ),
                        variants=[
                            Declension(
                                "Voici un joli {puppy}",
                                (
                                    "Voici de jolis chiots {puppy}",
                                    "Voici deux beaux chiots {puppy}",
                                ),
                            ),
                            Declension(
                                "Voici un chiot {puppy} rare",
                                (
                                    "Voici des chiots {puppy} rares",
                                    "Voici deux chiots {puppy} rares",
                                    "Voici plusieurs chiots {puppy} rares",
                                ),
                            ),
                            Declension(
                                "Voici un chiot {puppy} de la région {region}",
                                (
                                    "Voici des chiots {puppy} de la région {region}",
                                    "Voici deux chiots {puppy} de la région {region}",
                                ),
                            ),
                        ],
                        metadata={
                            "version": __version__,
                            "language": "fr-FR",
                            "locations": [],
                            "flags": ["python-format"],
                            "user_comments": ["Message sur des chiots"],
                        },
                    ),
                    Message(
                        id="1001",
                        principal=Declension(
                            "Voici un chatton",
                            ("Voici des chattons", "Voici deux chattons"),
                        ),
                        variants=[
                            Declension(
                                "Voici un joli {kitten}",
                                (
                                    "Voici de jolis chattons {kitten}",
                                    "Voici deux beaux chattons {kitten}",
                                ),
                            ),
                            Declension(
                                "Voici un chatton {kitten} rare",
                                (
                                    "Voici des chattons {kitten} rares",
                                    "Voici deux chattons {kitten} rares",
                                    "Voici plusieurs chattons {kitten} rares",
                                ),
                            ),
                            Declension(
                                "Voici un chatton {kitten} de la région {region}",
                                (
                                    "Voici des chattons {kitten} de la région {region}",
                                    "Voici deux chattons {kitten} de la région {region}",
                                ),
                            ),
                        ],
                        metadata={
                            "version": __version__,
                            "language": "fr-FR",
                            "locations": [],
                            "flags": ["python-format"],
                            "user_comments": ["Message sur des chattons"],
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
                        [
                            "Voici un chatton",
                            "Voici des chattons",
                            "Voici deux chattons",
                        ],
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
    def test_book_add(self, fixture_book, messages, expected, request):
        book = request.getfixturevalue(fixture_book)
        book.add("test", messages)
        for msg_id, msg_main, msg_variants in expected:
            assert list(book.get(msg_id).principal.segments) == msg_main
            for index, msg_variant in enumerate(msg_variants):
                assert list(book.get(msg_id).get_variant(index + 1).segments) == (
                    msg_variant
                )

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
                        principal=Declension(
                            "Voici un chiot", ("Voici des chiots", "Voici deux chiots")
                        ),
                        variants=[
                            Declension(
                                "Voici un joli {puppy}",
                                (
                                    "Voici de jolis chiots {puppy}",
                                    "Voici deux beaux chiots {puppy}",
                                ),
                            ),
                            Declension(
                                "Voici un chiot {puppy} rare",
                                (
                                    "Voici des chiots {puppy} rares",
                                    "Voici deux chiots {puppy} rares",
                                    "Voici plusieurs chiots {puppy} rares",
                                ),
                            ),
                            Declension(
                                "Voici un chiot {puppy} de la région {region}",
                                (
                                    "Voici des chiots {puppy} de la région {region}",
                                    "Voici deux chiots {puppy} de la région {region}",
                                ),
                            ),
                        ],
                        metadata={
                            "version": __version__,
                            "language": "fr-BE",
                            "locations": [],
                            "flags": ["python-format"],
                            "user_comments": ["Message sur des chiots"],
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
                        principal=Declension(
                            "Voici un chiot", ("Voici des chiots", "Voici deux chiots")
                        ),
                        variants=[
                            Declension(
                                "Voici un joli {puppy}",
                                (
                                    "Voici de jolis chiots {puppy}",
                                    "Voici deux beaux chiots {puppy}",
                                ),
                            ),
                            Declension(
                                "Voici un chiot {puppy} rare",
                                (
                                    "Voici des chiots {puppy} rares",
                                    "Voici deux chiots {puppy} rares",
                                    "Voici plusieurs chiots {puppy} rares",
                                ),
                            ),
                            Declension(
                                "Voici un chiot {puppy} de la région {region}",
                                (
                                    "Voici des chiots {puppy} de la région {region}",
                                    "Voici deux chiots {puppy} de la région {region}",
                                ),
                            ),
                        ],
                        metadata={
                            "version": __version__,
                            "language": "fr-FR",
                            "locations": [],
                            "flags": ["python-format"],
                            "user_comments": ["Message sur des chiots"],
                        },
                    )
                ],
                "Message with id (1100) is already present in this book",
            ),
        ],
    )
    def test_book_add_failed(self, fixture_book, domain, messages, expected, request):
        book = request.getfixturevalue(fixture_book)
        with pytest.raises(ValueError, match=re.escape(expected)):
            book.add(domain, messages)


class TestBookRemove:
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
    def test_book_remove(self, fixture_book, messages_id, expected, request):
        book = request.getfixturevalue(fixture_book)
        for message_id in messages_id:
            book.remove(message_id)
            assert book.get(message_id) is None
        assert book.metadata[["count", "messages"]] == expected

    def test_book_remove_failed(self, fr_fr_book):
        with pytest.raises(
            ValueError, match=re.escape("Message identifier 1000 is not in this book")
        ):
            fr_fr_book.remove("1000")


class TestBookMetadata:
    @pytest.mark.parametrize(
        "fixture_book", ["fr_fr_book", "en_us_book", "en_gb_book", "it_it_book"]
    )
    def test_book_metadata_defaults_and_language_domain(self, fixture_book, request):
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
        assert book.metadata.paths().__contains__(
            ["statistics", "total_messages"]
        ) and isinstance(book.metadata[["statistics", "total_messages"]], int)
        assert book.metadata.paths().__contains__(
            ["statistics", "total_words"]
        ) and isinstance(book.metadata[["statistics", "total_words"]], int)
        # Count backward compatibility
        assert book.metadata[["count", "messages"]] == len(book.messages)

    @pytest.mark.parametrize(
        "fixture_book,lang",
        [
            ("fr_fr_book", "fr-FR"),
            ("en_us_book", "en-US"),
            ("en_gb_book", "en-GB"),
            ("it_it_book", "it-IT"),
        ],
    )
    def test_book_statistics_update_on_add_and_remove(
        self, fixture_book, lang, request
    ):
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
    @pytest.mark.parametrize(
        "fixture_book", ["fr_fr_book"]
    )  # one is enough for API checks
    def test_book_set_metadata_update_and_reset(
        self, fixture_book, key, value, expected_path, expected_value, request
    ):
        book = request.getfixturevalue(fixture_book)
        book.set_metadata(key, value)
        # Access metadata using path semantics supported by StrictNestedDictionary
        # For top-level keys, expected_path is [key]
        if len(expected_path) == 1:
            assert as_plain(book.metadata[expected_path[0]]) == expected_value
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
        self, fixture_book, key, value, expected_exception, request
    ):
        book = request.getfixturevalue(fixture_book)
        with pytest.raises(expected_exception):
            book.set_metadata(key, value)


class TestBookAttributes:
    @pytest.mark.parametrize(
        "fixture_book, expected_lang, expected_domain, expected_format",
        [
            ("fr_fr_book", "fr-FR", "test", "json"),
            ("en_us_book", "en-US", "test", "json"),
        ],
    )
    def test_attribute_getters(
        self, fixture_book, expected_lang, expected_domain, expected_format, request
    ):
        book = request.getfixturevalue(fixture_book)
        assert book.get_language() == expected_lang
        assert book.get_domain() == expected_domain
        assert book.get_format() == expected_format

    def test_add_attribute_methods_fail_when_already_set(self, fr_fr_book):
        # add_language when already set
        with pytest.raises(ValueError, match="Language is already set for this book"):
            fr_fr_book.add_language("fr")
        # add_domain when already set
        with pytest.raises(ValueError, match="Domain is already set for this book"):
            fr_fr_book.add_domain("test")
        # add_format when already set
        with pytest.raises(ValueError, match="Format is already set for this book"):
            fr_fr_book.add_format("json")

    def test_remove_attributes_then_add_again(self):
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

    def test_constructor_and_setters_validate_format_consistently(self):
        """biface/i18n#66 — before this fix, Book(format=...) accepted any
        value silently (no call to the format validator), while
        add_format()/update_format() raised ValueError on the same input.
        All three now go through build_book_filename() and must behave
        identically."""
        with pytest.raises(ValueError, match="Unknown format 'banana'"):
            Book(domain="d", language="fr-FR", format="banana")

        book = Book(domain="d", language="fr-FR")
        with pytest.raises(ValueError, match="Unknown format 'banana'"):
            book.update_format("banana")

        book.remove_format()
        with pytest.raises(ValueError, match="Unknown format 'banana'"):
            book.add_format("banana")


class TestBookUpdate:
    def test_update_language_success_on_empty_book(self):
        book = Book(domain="d", language="fr-FR")
        # No messages: update freely
        book.update_language("fr")
        assert book.language == "fr"  # normalization and same
        book.update_language("en-us")
        assert book.language == "en-US"

    def test_update_language_failure_on_mismatch(self, fr_fr_book, en_message):
        # ensure en_message language mismatches fr-FR after normalization
        assert en_message.metadata["language"] in ("en", "en-US", "en-GB")
        # Try to update the book language to en-US while it contains fr-FR messages -> should fail
        with pytest.raises(
            ValueError,
            match=r"Language of message \(.*\) is not compatible with updated book language \('en-US'\)",
        ):
            fr_fr_book.update_language("en-US")

    def test_update_domain_and_format_success(self, fr_fr_book):
        fr_fr_book.update_domain("animals")
        assert fr_fr_book.domain == "animals"
        assert fr_fr_book.format == "json"
        assert fr_fr_book.filename == "animals.json.i18t"
        fr_fr_book.update_format("yaml")
        assert fr_fr_book.format == "yaml"
        assert fr_fr_book.filename == "animals.yaml.i18t"


class TestBookLoad:

    def test_book_load_nominal(self, fr_fr_i18t_directory):
        """Cas nominal : Book peuplé avec les 10 messages fr-FR."""
        book = Book(language="fr-FR", domain="test")
        book.load(fr_fr_i18t_directory)
        assert len(list(book)) == 10
        assert set(book.messages.keys()) == {
            "1100",
            "1101",
            "1102",
            "1103",
            "1104",
            "1105",
            "1106",
            "1107",
            "1108",
            "1109",
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
        """Fichier à matrice mal formée → FormatError."""
        (tmp_path / "test.json.i18t").write_text(
            json.dumps({"10001": "not-a-list"}), encoding="utf-8"
        )
        book = Book(language="fr-FR", domain="test")
        with pytest.raises(FormatError):
            book.load(str(tmp_path))


class TestBookSave:
    def test_save(self, fr_fr_book, tmp_path):
        """Book.save() writes a readable .i18t file (round-trip check).

        References
        ----------
        - biface/i18n#57 : Book.save() persistence (DD-06, DD-15, DD-16)
        """
        fr_fr_book.save(str(tmp_path))
        saved_file = tmp_path / fr_fr_book.filename
        assert saved_file.exists()

    def test_save_file_not_found(self, fr_fr_book):
        """Book.save() raises FileNotFoundError if the directory does not exist.

        References
        ----------
        - biface/i18n#57 : Book.save() persistence
        """
        with pytest.raises(FileNotFoundError):
            fr_fr_book.save("/nonexistent/directory")

    def test_save_round_trip(self, fr_fr_book, tmp_path):
        """load() after save() produces a Book with the same message ids.

        References
        ----------
        - biface/i18n#57 : Book.save() persistence (DD-06, DD-15, DD-16)
        """
        from i18n_tools.models.book import Book

        fr_fr_book.save(str(tmp_path))

        reloaded = Book(
            domain=fr_fr_book.domain,
            language=fr_fr_book.language,
            format=fr_fr_book.format,
        )
        reloaded.load(str(tmp_path))

        assert set(reloaded.messages.keys()) == set(fr_fr_book.messages.keys())

    def test_save_writes_native_entries(self, fr_fr_book, tmp_path):
        """Book.save() writes each message as a messages/metadata entry."""
        fr_fr_book.save(str(tmp_path))
        data = json.loads((tmp_path / fr_fr_book.filename).read_text("utf-8"))
        for msgid in fr_fr_book.messages.keys():
            assert set(data[msgid].keys()) == {"messages", "metadata"}

    def test_save_round_trip_keeps_message_metadata(self, tmp_path):
        """Locations, flags and comments survive a save/load round trip."""
        message = Message(
            id="10001",
            principal=Declension("Un message", ("Des messages",)),
            variants=[Declension("Une variante")],
            metadata={"language": "fr-FR"},
        )
        message.add_location("app.py", 12)
        message.add_location("cli.py", 40, variant=1, segment=0)
        message.add_comment("user", "Shown in the status bar")
        message.add_comment("auto", "Extracted from app.py")
        message.metadata["flags"] = ["fuzzy"]
        book = Book([message], domain="test", language="fr-FR")
        book.save(str(tmp_path))

        reloaded = Book(domain="test", language="fr-FR")
        reloaded.load(str(tmp_path))
        loaded = reloaded.get("10001")

        assert loaded is not None
        assert loaded.locations == (
            Location("app.py", 12),
            Location("cli.py", 40, variant=1, segment=0),
        )
        data = json.loads((tmp_path / book.filename).read_text("utf-8"))
        assert data["10001"]["metadata"]["locations"] == [
            ["app.py", 12],
            ["cli.py", 40, 1, 0],
        ]
        assert loaded.metadata["user_comments"] == ["Shown in the status bar"]
        assert loaded.metadata["auto_comments"] == ["Extracted from app.py"]
        assert loaded.metadata["flags"] == ["fuzzy"]
        assert loaded.matrix == message.matrix

    def test_load_keeps_an_empty_variant_before_a_filled_one(self, tmp_path):
        """An empty singular in a variant column keeps its column on load."""
        data = {
            "10001": {
                "messages": [
                    ["Fichier", "", "Document"],
                    ["Fichiers", "", "Documents"],
                ],
                "metadata": {},
            }
        }
        (tmp_path / "test.json.i18t").write_text(json.dumps(data), encoding="utf-8")
        book = Book(domain="test", language="fr-FR")
        book.load(str(tmp_path))
        loaded = book.get("10001")

        assert loaded is not None
        assert loaded.matrix == data["10001"]["messages"]

    def test_save_round_trip_keeps_the_matrix(self, tmp_path):
        """Empty cells, padding rows included, survive a save/load round trip."""
        matrix = [["Un", "Une", ""], ["Des", "", "Plusieurs"], ["", "", ""]]
        message = Message.from_matrix("10001", matrix, metadata={"language": "fr-FR"})
        book = Book([message], domain="test", language="fr-FR")
        book.save(str(tmp_path))

        reloaded = Book(domain="test", language="fr-FR")
        reloaded.load(str(tmp_path))
        loaded = reloaded.get("10001")

        assert loaded is not None
        assert loaded.matrix == matrix

    def test_save_writes_language_and_domain_at_root(self, tmp_path):
        """The root metadata carries the book's language and domain."""
        book = Book([_make_simple_message("fr-FR")], domain="test", language="fr-FR")
        book.save(str(tmp_path))
        data = json.loads((tmp_path / book.filename).read_text("utf-8"))
        assert data["metadata"]["language"] == "fr-FR"
        assert data["metadata"]["domain"] == "test"

    def test_save_round_trip_keeps_root_metadata(self, tmp_path):
        """Header fields and unknown root keys survive a save/load round trip."""
        book = Book(
            [_make_simple_message("fr-FR")],
            domain="test",
            language="fr-FR",
            language_team="Équipe FR",
            header_comment="Notes de l'équipe",
        )
        book.set_metadata("project_extra", "kept as is")
        book.save(str(tmp_path))

        reloaded = Book(domain="test", language="fr-FR")
        with pytest.warns(
            I18nToolsWarning, match="unknown metadata key 'project_extra' kept"
        ):
            reloaded.load(str(tmp_path))

        assert reloaded.metadata["language_team"] == "Équipe FR"
        assert reloaded.metadata["header_comment"] == "Notes de l'équipe"
        assert reloaded.metadata["project_extra"] == "kept as is"
        assert as_plain(reloaded.metadata) == as_plain(book.metadata)

    def test_load_keeps_language_and_domain_as_attributes(self, tmp_path):
        """Root language and domain are not copied into Book.metadata."""
        book = Book([_make_simple_message("fr-FR")], domain="test", language="fr-FR")
        book.save(str(tmp_path))

        reloaded = Book(domain="test", language="fr-FR")
        reloaded.load(str(tmp_path))

        assert "language" not in reloaded.metadata
        assert "domain" not in reloaded.metadata

    def test_load_recomputes_derived_root_metadata(self, tmp_path):
        """Statistics and message count are recomputed, not read from the file."""
        book = Book([_make_simple_message("fr-FR")], domain="test", language="fr-FR")
        book.save(str(tmp_path))
        file = tmp_path / book.filename
        data = json.loads(file.read_text("utf-8"))
        data["metadata"]["statistics"] = {"total_words": 999, "total_messages": 42}
        data["metadata"]["count"] = {"messages": 42}
        file.write_text(json.dumps(data), encoding="utf-8")

        reloaded = Book(domain="test", language="fr-FR")
        with pytest.warns(I18nToolsWarning) as record:
            reloaded.load(str(tmp_path))

        messages = [str(warning.message) for warning in record]
        assert any("root: statistics are" in m for m in messages)
        assert any("root: count is" in m for m in messages)
        assert as_plain(reloaded.metadata["statistics"]) == as_plain(
            book.metadata["statistics"]
        )
        assert reloaded.metadata[["count", "messages"]] == 1

    def test_save_round_trip_keeps_message_context(self, tmp_path):
        """The context of a message survives a save/load round trip."""
        message = Message(
            id="10001",
            principal=Declension("Enregistrer"),
            context="toolbar",
            metadata={"language": "fr-FR"},
        )
        book = Book([message], domain="test", language="fr-FR")
        book.save(str(tmp_path))
        data = json.loads((tmp_path / book.filename).read_text("utf-8"))
        assert data["10001"]["metadata"]["context"] == "toolbar"

        reloaded = Book(domain="test", language="fr-FR")
        reloaded.load(str(tmp_path))
        loaded = reloaded.get("10001")

        assert loaded is not None
        assert loaded.context == "toolbar"

    def test_save_round_trip_keeps_variant_plurals_beyond_principal(self, tmp_path):
        """A variant with more plurals than the principal loses none on save."""
        message = Message(
            id="10001",
            principal=Declension("Une fleur", ("Des fleurs",)),
            variants=[
                Declension(
                    "Une fleur rare", ("Des fleurs rares", "Plusieurs fleurs rares")
                )
            ],
            metadata={"language": "fr-FR"},
        )
        book = Book([message], domain="test", language="fr-FR")
        book.save(str(tmp_path))
        data = json.loads((tmp_path / book.filename).read_text("utf-8"))
        assert data["10001"]["messages"] == [
            ["Une fleur", "Une fleur rare"],
            ["Des fleurs", "Des fleurs rares"],
            ["", "Plusieurs fleurs rares"],
        ]

        reloaded = Book(domain="test", language="fr-FR")
        reloaded.load(str(tmp_path))
        loaded = reloaded.get("10001")

        assert loaded is not None
        assert loaded.get_variant(1).plurals == (
            "Des fleurs rares",
            "Plusieurs fleurs rares",
        )


class TestBookLoadIntegrity:
    """Book.load() checks the file against the Book's language and domain."""

    @staticmethod
    def _saved(tmp_path, language="fr-FR", domain="test"):
        book = Book([_make_simple_message(language)], domain=domain, language=language)
        book.save(str(tmp_path))
        return tmp_path / book.filename

    def test_load_own_file_issues_no_warning(self, tmp_path, recwarn):
        self._saved(tmp_path)
        Book(domain="test", language="fr-FR").load(str(tmp_path))
        assert not [w for w in recwarn if issubclass(w.category, I18nToolsWarning)]

    def test_load_same_family_language_warns(self, tmp_path):
        self._saved(tmp_path, language="fr-BE")
        book = Book(domain="test", language="fr-FR")
        with pytest.warns(I18nToolsWarning, match="'fr-BE' differs from 'fr-FR'"):
            book.load(str(tmp_path))
        assert book.language == "fr-FR"

    def test_load_other_family_language_fails(self, tmp_path):
        self._saved(tmp_path, language="en-US")
        book = Book(domain="test", language="fr-FR")
        with pytest.raises(FormatError, match="not of the family of 'fr-FR'"):
            book.load(str(tmp_path))

    def test_load_other_domain_fails(self, tmp_path):
        file = self._saved(tmp_path)
        data = json.loads(file.read_text("utf-8"))
        data["metadata"]["domain"] = "other"
        file.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(FormatError, match="domain 'other' is not 'test'"):
            Book(domain="test", language="fr-FR").load(str(tmp_path))


class TestBookCheck:
    @staticmethod
    def _book(*messages: Message) -> Book:
        for message in messages:
            message.add_language("fr-FR")
        return Book(list(messages), domain="test", language="fr-FR")

    @staticmethod
    def _message(identifier: str) -> Message:
        return Message(
            identifier,
            Declension("Un fichier", ("Des fichiers",)),
            [Declension("Un document", ("Des documents",))],
        )

    @staticmethod
    def _counters_of(text: str):
        return Message("x", Declension(text)).observed

    def test_sound_messages(self):
        complete = self._message("1")
        complete.mark_complete()
        assert self._book(complete, self._message("2")).check() == []

    def test_draft_findings_are_info(self):
        diverging = self._message("1")
        diverging.mark_complete()
        diverging.reopen()
        diverging.update_segment("", 1, 1)
        empty = Message("2", Declension("", ("Des fichiers",)))
        assert self._book(diverging, empty).check() == [
            Finding(
                "info",
                "1",
                "content differs from the recorded counters: text (1, 1) lost",
            ),
            Finding("info", "2", "the principal singular is empty"),
        ]

    def test_complete_findings_are_errors(self):
        recorded = self._message("0")
        recorded.mark_complete()
        assert recorded.recorded is not None
        lost = Message(
            "1",
            Declension("Un fichier", ("Des fichiers",)),
            [Declension("Un document", ("",))],
            status="complete",
            recorded=recorded.recorded,
        )
        unrecorded = Message("2", Declension("Un fichier"), status="complete")
        empty = Message(
            "3", Declension(""), status="complete", recorded=self._counters_of("")
        )
        assert self._book(lost, unrecorded, empty).check() == [
            Finding(
                "error",
                "1",
                "content differs from the recorded counters: text (1, 1) lost",
            ),
            Finding("error", "2", "complete without recorded counters"),
            Finding("error", "3", "the principal singular is empty"),
        ]

    def test_check_never_raises_nor_warns(self, recwarn):
        unrecorded = Message("1", Declension("Un fichier"), status="complete")
        findings = self._book(unrecorded).check()
        assert [finding.severity for finding in findings] == ["error"]
        assert len(recwarn) == 0

    def test_empty_book(self):
        assert Book(domain="test", language="fr-FR").check() == []


class TestBookCounters:
    """Status and content counters on disk (DD-45)."""

    @staticmethod
    def _message(identifier: str = "10001") -> Message:
        return Message(
            identifier,
            Declension("Un fichier", ("Des fichiers",)),
            [Declension("Un document", ("Des documents",))],
            metadata={"language": "fr-FR"},
        )

    @staticmethod
    def _entry(tmp_path, book: Book, identifier: str = "10001") -> dict:
        data = json.loads((tmp_path / book.filename).read_text("utf-8"))
        return data[identifier]

    @staticmethod
    def _reload(tmp_path) -> Book:
        book = Book(domain="test", language="fr-FR")
        book.load(str(tmp_path))
        return book

    def test_draft_round_trip(self, tmp_path):
        message = self._message()
        book = Book([message], domain="test", language="fr-FR")
        book.save(str(tmp_path))
        metadata = self._entry(tmp_path, book)["metadata"]
        assert metadata["status"] == "draft"
        assert metadata["singular_count"] == 2
        assert metadata["segment_count"] == 2
        assert metadata["fill_mask"] == [[True, True], [True, True]]
        assert "plural_counts" not in metadata
        assert message.recorded == message.observed
        loaded = self._reload(tmp_path).get("10001")
        assert loaded is not None
        assert loaded.status == "draft"
        assert loaded.recorded == message.recorded

    def test_complete_round_trip(self, tmp_path, recwarn):
        message = self._message()
        message.mark_complete()
        Book([message], domain="test", language="fr-FR").save(str(tmp_path))
        loaded = self._reload(tmp_path).get("10001")
        assert loaded is not None
        assert loaded.status == "complete"
        assert loaded.recorded == message.recorded
        assert not loaded.has_divergence
        assert not [w for w in recwarn if issubclass(w.category, I18nToolsWarning)]

    def test_saving_a_draft_records_it(self, tmp_path):
        message = self._message()
        message.record()
        message.update_segment("", 1, 1)
        assert message.has_divergence
        Book([message], domain="test", language="fr-FR").save(str(tmp_path))
        assert not message.has_divergence

    def test_padded_draft_round_trip(self, tmp_path):
        message = Message(
            "10001",
            Declension("Un fichier"),
            [Declension("Un document", ("Des documents",))],
            metadata={"language": "fr-FR"},
        )
        book = Book([message], domain="test", language="fr-FR")
        book.save(str(tmp_path))
        assert self._entry(tmp_path, book)["metadata"]["fill_mask"] == [
            [True, True],
            [False, True],
        ]
        loaded = self._reload(tmp_path).get("10001")
        assert loaded is not None
        assert not loaded.has_divergence

    @pytest.mark.parametrize("recorded", [True, False], ids=["diverging", "unrecorded"])
    def test_save_refuses_a_diverging_complete_message(self, tmp_path, recorded):
        sound = self._message("10000")
        sound.mark_complete()
        draft = self._message("10002")
        book = Book([sound, draft], domain="test", language="fr-FR")
        book.save(str(tmp_path))
        before = (tmp_path / book.filename).read_text("utf-8")
        draft.update_segment("", 1, 1)
        broken = Message(
            "10001",
            Declension("Un fichier", ("",)),
            status="complete",
            recorded=sound.recorded if recorded else None,
            metadata={"language": "fr-FR"},
        )
        book.add("test", [broken])
        with pytest.raises(MessageError, match="10001 diverge"):
            book.save(str(tmp_path))
        assert (tmp_path / book.filename).read_text("utf-8") == before
        assert draft.has_divergence

    def test_save_accepts_a_diverging_draft(self, tmp_path):
        message = self._message()
        message.record()
        message.update_segment("", 1, 1)
        Book([message], domain="test", language="fr-FR").save(str(tmp_path))
        loaded = self._reload(tmp_path).get("10001")
        assert loaded is not None
        assert loaded.matrix == message.matrix

    def test_load_a_diverging_complete_message(self, tmp_path):
        message = self._message()
        message.mark_complete()
        book = Book([message], domain="test", language="fr-FR")
        book.save(str(tmp_path))
        data = json.loads((tmp_path / book.filename).read_text("utf-8"))
        data["10001"]["messages"][1][1] = ""
        del data["metadata"]["statistics"]
        (tmp_path / book.filename).write_text(json.dumps(data), encoding="utf-8")
        reloaded = Book(domain="test", language="fr-FR")
        with pytest.warns(I18nToolsWarning, match=re.escape("text (1, 1) lost")):
            reloaded.load(str(tmp_path))
        loaded = reloaded.get("10001")
        assert loaded is not None
        assert loaded.has_divergence
        assert [finding.severity for finding in reloaded.check()] == ["error"]
        with pytest.raises(MessageError):
            reloaded.save(str(tmp_path))

    def test_writer_writes_the_record_of_a_complete_message(self):
        """The writer never replaces the record of a complete message."""
        reference = self._message()
        reference.mark_complete()
        diverging = Message(
            "10001",
            Declension("Un fichier", ("",)),
            [Declension("Un document", ("",))],
            status="complete",
            recorded=reference.recorded,
        )
        metadata = message_to_i18n_tools_format(diverging)["metadata"]
        assert metadata["fill_mask"] == [[True, True], [True, True]]
