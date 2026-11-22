"""
Minimal test file for Book model using shared fixtures from tests/models/conftest.py
"""

import json
import re
from datetime import datetime

import pytest
from ndict_tools import StrictNestedDictionary

from i18n_tools._finding import Finding
from i18n_tools.converter import message_to_i18n_tools_format
from i18n_tools.exceptions import FormatError, I18nToolsWarning, MessageError
from i18n_tools.models.book import Book
from i18n_tools.models.message import Message

GETTEXT_KEYS = [
    "project_id_version",
    "report_msgid_bugs_to",
    "pot_creation_date",
    "po_revision_date",
    "last_translator",
    "language_team",
    "header_comment",
]


# Using fixtures: fr_fr_book, en_us_book, en_gb_book, it_it_book from local conftest.py
@pytest.fixture
def fr_fr_i18t_directory(tmp_path, fr_fr_book):
    """fr_fr_book written to test.json.i18t; the directory, as a string."""
    fr_fr_book.save(str(tmp_path))
    return str(tmp_path)


def _as_read(message: Message, status: str, record=None) -> Message:
    """
    ``message`` with the status and the record a file could hold, as
    Book.load() sets them, without the checks of mark_complete().
    """
    message.metadata["status"] = status
    for key, value in (record or {}).items():
        message.metadata[key] = StrictNestedDictionary(
            value, default_setup=message.metadata.default_setup
        )
    return message


def _make_simple_message(lang: str) -> Message:
    return Message(
        "tmp1",
        "Hello world",
        plurals=["Hello worlds"],
        alternatives=[["Hello {who}", "Hello {who}s"]],
        locations=[],
        flags=["python-format"],
        user_comments=[],
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
        assert book.metadata["language"] == language
        assert "language" not in book.messages["1100"].metadata

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

    def test_messages_held_without_a_language_check(self, fr_message):
        """The Book is the only holder of the language."""
        book = Book(fr_message, domain="test", language="it")
        assert book.get("1000") is fr_message


class TestBookOptions:
    """Keyword options of Book(): the closed BookOptions set."""

    def test_accepts_every_option(self):
        book = Book(language="fr-FR", domain="test", file_format="yaml")
        assert book.language == "fr-FR"
        assert book.domain == "test"
        assert book.file_format == "yaml"

    def test_gettext_fields_are_not_options(self):
        with pytest.raises(
            TypeError, match=re.escape("Unknown Book option(s): project_id_version")
        ):
            Book(language="fr-FR", domain="test", project_id_version="app 2.0")

    def test_refuses_an_unknown_option(self):
        with pytest.raises(
            TypeError, match=re.escape("Unknown Book option(s): format")
        ):
            Book(language="fr-FR", domain="test", format="yaml")

    def test_names_every_unknown_option(self):
        with pytest.raises(
            TypeError, match=re.escape("Unknown Book option(s): colour, format")
        ):
            Book(language="fr-FR", domain="test", format="yaml", colour="blue")

    def test_refuses_a_language_that_is_not_a_string(self):
        with pytest.raises(
            TypeError, match=re.escape("Book language must be a string.")
        ):
            Book(language=1, domain="test")


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
                        "1000",
                        "Voici un chiot",
                        plurals=["Voici des chiots", "Voici deux chiots"],
                        alternatives=[
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
                        locations=[],
                        flags=["python-format"],
                        user_comments=["Message sur des chiots"],
                    ),
                    Message(
                        "1001",
                        "Voici un chatton",
                        plurals=["Voici des chattons", "Voici deux chattons"],
                        alternatives=[
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
                            [
                                "Voici un chatton {kitten} de la région {region}",
                                "Voici des chattons {kitten} de la région {region}",
                                "Voici deux chattons {kitten} de la région {region}",
                            ],
                        ],
                        locations=[],
                        flags=["python-format"],
                        user_comments=["Message sur des chattons"],
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
        for message in messages:
            book.add(message)
        assert book.get("1000") is messages[0]
        for msg_id, msg_main, msg_variants in expected:
            assert list(book.get(msg_id).principal.segments) == msg_main
            for index, msg_variant in enumerate(msg_variants):
                assert list(book.get(msg_id).get_variant(index + 1).segments) == (
                    msg_variant
                )

    def test_add_refuses_an_identifier_already_present(self, fr_fr_book):
        other = Message("1100", "Voici un chiot")
        before = fr_fr_book.get("1100")
        with pytest.raises(
            ValueError,
            match=re.escape("Message with id (1100) is already present in this book"),
        ):
            fr_fr_book.add(other)
        assert fr_fr_book.get("1100") is before

    @pytest.mark.parametrize("identifier", ["metadata", ".pyi18t_tools", ".i18n_tools"])
    def test_add_refuses_a_reserved_key(self, fr_fr_book, identifier):
        with pytest.raises(
            ValueError,
            match=re.escape(
                f"'{identifier}' is reserved and cannot be a message identifier"
            ),
        ):
            fr_fr_book.add(Message(identifier, "Texte"))
        assert identifier not in fr_fr_book.messages
        assert len(fr_fr_book.messages) == 10

    def test_add_refuses_what_is_not_a_message(self, fr_fr_book):
        with pytest.raises(TypeError, match="Book.add\\(\\) takes a Message"):
            fr_fr_book.add("1000")  # pyright: ignore[reportArgumentType]

    def test_constructor_adds_as_add_does(self):
        with pytest.raises(ValueError, match="is already present in this book"):
            Book(Message("1", "a"), [Message("1", "b")], domain="d", language="fr")
        with pytest.raises(ValueError, match="'metadata' is reserved"):
            Book(Message("metadata", "a"), domain="d", language="fr")

    def test_int_identifier_held_as_a_string(self, fr_fr_book):
        fr_fr_book.add(Message(42, "Texte"))
        assert fr_fr_book.get("42").id == "42"


class TestBookRename:
    def test_rename_changes_the_key_and_the_id(self, fr_fr_book):
        message = fr_fr_book.get("1101")
        order = list(fr_fr_book.messages.keys())
        fr_fr_book.rename("1101", "mountain.like")
        assert fr_fr_book.get("1101") is None
        assert fr_fr_book.get("mountain.like") is message
        assert message.id == "mountain.like"
        assert list(fr_fr_book.messages.keys()) == [
            "mountain.like" if key == "1101" else key for key in order
        ]

    def test_rename_to_an_int(self, fr_fr_book):
        fr_fr_book.rename("1101", 2101)
        assert fr_fr_book.get("2101").id == "2101"

    def test_rename_to_itself(self, fr_fr_book):
        fr_fr_book.rename("1101", "1101")
        assert fr_fr_book.get("1101").id == "1101"

    def test_renamed_message_saved_under_its_new_key(self, fr_fr_book, tmp_path):
        fr_fr_book.rename("1101", "mountain.like")
        fr_fr_book.save(str(tmp_path))
        data = json.loads((tmp_path / fr_fr_book.filename).read_text("utf-8"))
        assert data["mountain.like"]["metadata"]["id"] == "mountain.like"
        assert "1101" not in data

    @pytest.mark.parametrize(
        "old, new, error, expected",
        [
            ("9999", "x", KeyError, "Message identifier '9999' is not in this book"),
            ("1101", "1102", ValueError, "Message with id (1102) is already present"),
            ("1101", "metadata", ValueError, "'metadata' is reserved"),
            ("1101", ".pyi18t_tools", ValueError, "'.pyi18t_tools' is reserved"),
            ("1101", "", ValueError, "Message identifier must not be empty"),
            ("1101", True, TypeError, "Message identifier must be a str or an int"),
        ],
        ids=["absent", "present", "reserved", "reserved-tool", "empty", "bool"],
    )
    def test_rename_refused_state_unchanged(
        self, fr_fr_book, old, new, error, expected
    ):
        keys = list(fr_fr_book.messages.keys())
        ids = [message.id for message in fr_fr_book]
        with pytest.raises(error, match=re.escape(expected)):
            fr_fr_book.rename(old, new)
        assert list(fr_fr_book.messages.keys()) == keys
        assert [message.id for message in fr_fr_book] == ids


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
        assert len(book.messages) == expected

    def test_book_remove_failed(self, fr_fr_book):
        with pytest.raises(
            ValueError, match=re.escape("Message identifier 1000 is not in this book")
        ):
            fr_fr_book.remove("1000")


class TestBookMetadata:
    def test_root_metadata_of_a_new_book(self):
        book = Book(domain="test", language="fr-fr")
        assert book.metadata.to_dict() == {
            "format_version": "1.0.0",
            "version": "0.0.1",
            "language": "fr-FR",
            "domain": "test",
            "gettext": dict.fromkeys(GETTEXT_KEYS, ""),
            "rules": {},
        }
        assert (book.format_version, book.version) == ("1.0.0", "0.0.1")

    def test_properties_read_the_keys(self, fr_fr_book):
        fr_fr_book.metadata["language"] = "fr-BE"
        fr_fr_book.metadata["domain"] = "other"
        assert (fr_fr_book.language, fr_fr_book.domain) == ("fr-BE", "other")

    def test_language_setter_normalises(self, fr_fr_book):
        fr_fr_book.language = "fr-be"
        assert fr_fr_book.metadata["language"] == "fr-BE"

    def test_version(self, fr_fr_book):
        fr_fr_book.version = "1.2.0"
        assert fr_fr_book.metadata["version"] == "1.2.0"
        fr_fr_book.set_version("1.3.0")
        assert fr_fr_book.version == "1.3.0"

    @pytest.mark.parametrize(
        "value, error, expected",
        [
            ("1.2", ValueError, "Book version '1.2' is not a strict semantic version"),
            ("1.0.0-rc.1", ValueError, "is not a strict semantic version"),
            ("01.0.0", ValueError, "is not a strict semantic version"),
            (1, TypeError, "Book version must be a str"),
        ],
    )
    def test_version_refused(self, fr_fr_book, value, error, expected):
        with pytest.raises(error, match=re.escape(expected)):
            fr_fr_book.version = value
        assert fr_fr_book.version == "0.0.1"

    def test_format_version_is_read_only(self, fr_fr_book):
        with pytest.raises(AttributeError):
            fr_fr_book.format_version = (
                "1.0.0"  # pyright: ignore[reportAttributeAccessIssue]
            )

    def test_set_gettext(self, fr_fr_book):
        fr_fr_book.set_gettext(project_id_version="app 2.0", language_team="FR")
        assert fr_fr_book.metadata[["gettext", "project_id_version"]] == "app 2.0"
        assert fr_fr_book.metadata[["gettext", "language_team"]] == "FR"

    @pytest.mark.parametrize(
        "fields, expected",
        [
            ({"plural_forms": "x"}, "Unknown gettext key(s): plural_forms"),
            ({"language_team": 1}, "gettext language_team must be a str"),
        ],
    )
    def test_set_gettext_refused(self, fr_fr_book, fields, expected):
        with pytest.raises(TypeError, match=re.escape(expected)):
            fr_fr_book.set_gettext(**fields)
        assert set(fr_fr_book.metadata["gettext"].values()) == {""}

    @pytest.mark.parametrize(
        "key, value, path, expected",
        [
            (
                ["gettext", "header_comment"],
                "Global notes",
                ["gettext", "header_comment"],
                "Global notes",
            ),
            (["gettext", "header_comment"], None, ["gettext", "header_comment"], ""),
            ("version", "2.0.0", ["version"], "2.0.0"),
            ("version", None, ["version"], "0.0.1"),
            ("language", "en-us", ["language"], "en-US"),
            ("rules", {"opaque": True}, ["rules", "opaque"], True),
            (["rules", "thresholds"], {"2": 1}, ["rules", "thresholds", "2"], 1),
        ],
    )
    def test_set_metadata(self, fr_fr_book, key, value, path, expected):
        fr_fr_book.set_metadata(key, value)
        assert fr_fr_book.metadata[path] == expected

    def test_set_metadata_resets_rules(self, fr_fr_book):
        fr_fr_book.set_metadata("rules", {"opaque": True, "kept": 1})
        fr_fr_book.set_metadata(["rules", "opaque"], None)
        assert fr_fr_book.metadata["rules"].to_dict() == {"kept": 1}
        fr_fr_book.set_metadata("rules", None)
        assert fr_fr_book.metadata["rules"].to_dict() == {}

    @pytest.mark.parametrize(
        "key, value, error, expected",
        [
            (None, "x", KeyError, "A metadata key or path must be provided"),
            ([], "x", KeyError, "A metadata key or path must be provided"),
            (
                "plural_rule",
                "x",
                KeyError,
                '["metadata", "plural_rule"] is not a key of the Book metadata',
            ),
            (
                ["gettext", "plural_forms"],
                "x",
                KeyError,
                '["metadata", "gettext", "plural_forms"] is not a key of the Book metadata',
            ),
            (
                "format_version",
                "1.0.0",
                KeyError,
                '["metadata", "format_version"] cannot be set',
            ),
            (
                ["count", "messages"],
                1,
                KeyError,
                '["metadata", "count", "messages"] cannot be set',
            ),
            ("statistics", {}, KeyError, '["metadata", "statistics"] cannot be set'),
            ("version", "1.0", ValueError, "is not a strict semantic version"),
            ("rules", [], TypeError, "Book rules must be a mapping"),
            (123, "x", TypeError, "key must be a str or a list of str"),
            ({"a": 1}, "x", TypeError, "key must be a str or a list of str"),
        ],
    )
    def test_set_metadata_refused(self, fr_fr_book, key, value, error, expected):
        before = fr_fr_book.metadata.to_dict()
        with pytest.raises(error, match=re.escape(expected)):
            fr_fr_book.set_metadata(key, value)
        assert fr_fr_book.metadata.to_dict() == before


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
        assert book.get_file_format() == expected_format

    def test_add_attribute_methods_fail_when_already_set(self, fr_fr_book):
        # add_language when already set
        with pytest.raises(ValueError, match="Language is already set for this book"):
            fr_fr_book.add_language("fr")
        # add_domain when already set
        with pytest.raises(ValueError, match="Domain is already set for this book"):
            fr_fr_book.add_domain("test")
        # add_file_format when already set
        with pytest.raises(
            ValueError, match="File format is already set for this book"
        ):
            fr_fr_book.add_file_format("json")

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

        book.remove_file_format()
        assert book.file_format is None
        book.add_file_format("yaml")
        assert book.file_format == "yaml"

    def test_constructor_and_setters_validate_format_consistently(self):
        """biface/i18n#66 — before this fix, Book(file_format=...) accepted
        any value silently (no call to the format validator), while
        add_file_format()/update_file_format() raised ValueError on the same
        input.
        All three now go through build_book_filename() and must behave
        identically."""
        with pytest.raises(ValueError, match="Unknown format 'banana'"):
            Book(domain="d", language="fr-FR", file_format="banana")

        book = Book(domain="d", language="fr-FR")
        with pytest.raises(ValueError, match="Unknown format 'banana'"):
            book.update_file_format("banana")

        book.remove_file_format()
        with pytest.raises(ValueError, match="Unknown format 'banana'"):
            book.add_file_format("banana")

    def test_constructor_sets_file_format(self):
        """Book(file_format=...) sets the attribute and the filename."""
        book = Book(domain="d", language="fr-FR", file_format="yaml")
        assert book.file_format == "yaml"
        assert book.get_file_format() == "yaml"
        assert book.filename == "d.yaml.i18t"


class TestBookUpdate:
    def test_update_language_success_on_empty_book(self):
        book = Book(domain="d", language="fr-FR")
        # No messages: update freely
        book.update_language("fr")
        assert book.language == "fr"  # normalization and same
        book.update_language("en-us")
        assert book.language == "en-US"

    def test_update_language_without_a_message_check(self, fr_fr_book):
        """The messages do not carry a language: nothing to compare."""
        fr_fr_book.update_language("en-US")
        assert fr_fr_book.language == "en-US"

    def test_update_domain_and_format_success(self, fr_fr_book):
        fr_fr_book.update_domain("animals")
        assert fr_fr_book.domain == "animals"
        assert fr_fr_book.file_format == "json"
        assert fr_fr_book.filename == "animals.json.i18t"
        fr_fr_book.update_file_format("yaml")
        assert fr_fr_book.file_format == "yaml"
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

    def test_book_load_root_metadata(self, fr_fr_i18t_directory):
        """The root metadata of the file replaces that of the Book."""
        book = Book(language="fr-FR", domain="test")
        book.load(fr_fr_i18t_directory)
        assert book.language == "fr-FR"
        assert book.metadata[["gettext", "po_revision_date"]] != ""
        for message in book:
            assert "language" not in message.metadata
            assert message.metadata["id"] == message.id

    def test_book_load_file_not_found(self, tmp_path):
        """Répertoire sans fichier correspondant → FileNotFoundError."""
        book = Book(language="fr-FR", domain="test")
        with pytest.raises(FileNotFoundError):
            book.load(str(tmp_path))

    def test_book_load_integrity_error(self, tmp_path):
        """A file of format 0.10.0 (no root metadata, a matrix) → FormatError."""
        (tmp_path / "test.json.i18t").write_text(
            json.dumps({"10001": [["Un message"]]}), encoding="utf-8"
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
            file_format=fr_fr_book.file_format,
        )
        reloaded.load(str(tmp_path))

        assert set(reloaded.messages.keys()) == set(fr_fr_book.messages.keys())

    def test_save_writes_entries_of_format_1_0_0(self, fr_fr_book, tmp_path):
        fr_fr_book.save(str(tmp_path))
        data = json.loads((tmp_path / fr_fr_book.filename).read_text("utf-8"))
        assert list(data) == ["metadata", *fr_fr_book.messages.keys()]
        assert list(data["metadata"]) == [
            "format_version",
            "version",
            "language",
            "domain",
            "gettext",
            "rules",
            "count",
            "statistics",
        ]
        for msgid in fr_fr_book.messages.keys():
            assert list(data[msgid]) == ["messages", "metadata"]
            assert list(data[msgid]["messages"]) == ["principal", "alternatives"]
            assert list(data[msgid]["metadata"]) == [
                "id",
                "context",
                "locations",
                "flags",
                "user_comments",
                "auto_comments",
                "status",
                "rules",
                "count",
                "fill_mask",
                "statistics",
            ]
            assert data[msgid]["metadata"]["id"] == msgid

    def test_save_writes_the_key_of_the_book_as_id(self, tmp_path):
        """The Book is the master of the keys."""
        message = Message("10001", "Un message")
        book = Book([message], domain="test", language="fr-FR")
        message.metadata["id"] = "changed"
        book.save(str(tmp_path))
        data = json.loads((tmp_path / book.filename).read_text("utf-8"))
        assert data["10001"]["metadata"]["id"] == "10001"

    def test_save_writes_the_revision_date(self, fr_fr_book, tmp_path):
        before = datetime.now().astimezone().replace(second=0, microsecond=0)
        fr_fr_book.save(str(tmp_path))
        data = json.loads((tmp_path / fr_fr_book.filename).read_text("utf-8"))
        written = data["metadata"]["gettext"]["po_revision_date"]
        assert re.fullmatch(r"\d{4}-\d\d-\d\d \d\d:\d\d[+-]\d{4}", written)
        assert datetime.strptime(written, "%Y-%m-%d %H:%M%z") >= before
        assert fr_fr_book.metadata[["gettext", "po_revision_date"]] == written

    def test_save_round_trip_keeps_message_metadata(self, tmp_path):
        """Locations, flags, comments and rules survive a save/load round trip."""
        message = Message(
            "10001",
            "Un message",
            plurals=["Des messages"],
            alternatives=[["Une variante", ""]],
            flags=["fuzzy"],
            rules={"opaque": {"kept": [1, 2]}},
        )
        message.add_location("app.py", 12)
        message.add_location("cli.py", 40, variant=1, segment=0)
        message.add_comment("user", "Shown in the status bar")
        message.add_comment("auto", "Extracted from app.py")
        book = Book([message], domain="test", language="fr-FR")
        book.save(str(tmp_path))

        reloaded = Book(domain="test", language="fr-FR")
        reloaded.load(str(tmp_path))
        loaded = reloaded.get("10001")

        assert loaded is not None
        assert loaded == message
        assert loaded.locations == [
            {"file": "app.py", "line": 12, "declension": None, "segment": None},
            {"file": "cli.py", "line": 40, "declension": 1, "segment": 0},
        ]
        assert loaded.rules.to_dict() == {"opaque": {"kept": [1, 2]}}

    def test_save_round_trip_keeps_the_matrix(self, tmp_path):
        """Empty cells, padding rows included, survive a save/load round trip."""
        matrix = [["Un", "Une", ""], ["Des", "", "Plusieurs"], ["", "", ""]]
        message = Message.from_matrix("10001", matrix)
        book = Book([message], domain="test", language="fr-FR")
        book.save(str(tmp_path))

        reloaded = Book(domain="test", language="fr-FR")
        reloaded.load(str(tmp_path))
        loaded = reloaded.get("10001")

        assert loaded is not None
        assert loaded.matrix == matrix

    def test_save_round_trip_keeps_root_metadata(self, tmp_path):
        book = Book([_make_simple_message("fr-FR")], domain="test", language="fr-FR")
        book.set_gettext(language_team="Équipe FR", header_comment="Notes de l'équipe")
        book.version = "1.4.2"
        book.set_metadata("rules", {"opaque": True})
        book.save(str(tmp_path))

        reloaded = Book(domain="test", language="fr-FR")
        reloaded.load(str(tmp_path))
        assert reloaded.metadata.to_dict() == book.metadata.to_dict()

    def test_save_computes_count_and_statistics(self, tmp_path):
        book = Book([_make_simple_message("fr-FR")], domain="test", language="fr-FR")
        book.save(str(tmp_path))
        root = json.loads((tmp_path / book.filename).read_text("utf-8"))["metadata"]
        assert root["count"] == {
            "messages": 1,
            "draft": 1,
            "complete": 0,
            "declensions": 2,
            "alternatives": 1,
            "singulars": 2,
            "plurals": 2,
            "segments": 4,
            "filled": 4,
            "empty": 0,
        }
        assert root["statistics"] == {
            "words": 8,
            "characters": 46,
            "messages_with_alternatives": 1,
            "messages_with_plurals": 1,
            "messages_with_rules": 0,
            "locations": 0,
            "flags": {"python-format": 1},
            "tokens": ["who"],
        }
        assert "count" not in book.metadata and "statistics" not in book.metadata

    def test_save_round_trip_keeps_message_context(self, tmp_path):
        """The context of a message survives a save/load round trip."""
        message = Message("10001", "Enregistrer", context="toolbar")
        book = Book([message], domain="test", language="fr-FR")
        book.save(str(tmp_path))
        data = json.loads((tmp_path / book.filename).read_text("utf-8"))
        assert data["10001"]["metadata"]["context"] == "toolbar"

        reloaded = Book(domain="test", language="fr-FR")
        reloaded.load(str(tmp_path))
        loaded = reloaded.get("10001")

        assert loaded is not None
        assert loaded.context == "toolbar"

    def test_save_pads_the_declensions(self, tmp_path):
        """A declension with fewer segments than another is written padded."""
        message = Message(
            "10001",
            "Une fleur",
            plurals=["Des fleurs"],
            alternatives=[
                ["Une fleur rare", "Des fleurs rares", "Plusieurs fleurs rares"]
            ],
        )
        book = Book([message], domain="test", language="fr-FR")
        book.save(str(tmp_path))
        data = json.loads((tmp_path / book.filename).read_text("utf-8"))
        assert data["10001"]["messages"] == {
            "principal": ["Une fleur", "Des fleurs", ""],
            "alternatives": [
                ["Une fleur rare", "Des fleurs rares", "Plusieurs fleurs rares"]
            ],
        }

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

    @pytest.mark.parametrize(
        "language", ["fr-BE", "en-US"], ids=["same-family", "other"]
    )
    def test_load_other_language_fails(self, tmp_path, language):
        self._saved(tmp_path, language=language)
        book = Book(domain="test", language="fr-FR")
        with pytest.raises(
            FormatError,
            match=re.escape(
                f"[\"metadata\", \"language\"] '{language}' is not 'fr-FR'"
            ),
        ):
            book.load(str(tmp_path))
        assert len(book.messages) == 0

    def test_load_other_domain_fails(self, tmp_path):
        file = self._saved(tmp_path)
        data = json.loads(file.read_text("utf-8"))
        data["metadata"]["domain"] = "other"
        file.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(
            FormatError,
            match=re.escape("[\"metadata\", \"domain\"] 'other' is not 'test'"),
        ):
            Book(domain="test", language="fr-FR").load(str(tmp_path))


class TestBookCheck:
    @staticmethod
    def _book(*messages: Message) -> Book:
        return Book(list(messages), domain="test", language="fr-FR")

    @staticmethod
    def _message(identifier: str) -> Message:
        return Message(
            identifier,
            "Un fichier",
            plurals=["Des fichiers"],
            alternatives=[["Un document", "Des documents"]],
        )

    @staticmethod
    def _counters_of(text: str):
        return Message("x", text).observed

    def test_sound_messages(self):
        complete = self._message("1")
        complete.mark_complete()
        assert self._book(complete, self._message("2")).check() == []

    def test_draft_findings_are_info(self):
        diverging = self._message("1")
        diverging.mark_complete()
        diverging.reopen()
        diverging.update_segment("", 1, 1)
        empty = Message("2", "", plurals=["Des fichiers"])
        assert self._book(diverging, empty).check() == [
            Finding(
                "info",
                "1",
                "content differs from the recorded counters: text (1, 1) lost",
            ),
            Finding("info", "2", "the principal singular is empty"),
        ]

    def test_complete_findings_are_errors(self):
        reference = self._message("0")
        reference.mark_complete()
        record = reference.recorded.to_dict()
        lost = _as_read(
            Message(
                "1",
                "Un fichier",
                plurals=["Des fichiers"],
                alternatives=[["Un document", ""]],
            ),
            "complete",
            record,
        )
        unrecorded = _as_read(Message("2", "Un fichier"), "complete")
        empty = _as_read(Message("3"), "complete", Message("x").observed.to_dict())
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
        unrecorded = _as_read(Message("1", "Un fichier"), "complete")
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
            "Un fichier",
            plurals=["Des fichiers"],
            alternatives=[["Un document", "Des documents"]],
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
        assert metadata["count"] == message.observed["count"].to_dict()
        assert metadata["fill_mask"] == {
            "principal": [True, True],
            "alternatives": [[True, True]],
        }
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
            "10001", "Un fichier", alternatives=[["Un document", "Des documents"]]
        )
        book = Book([message], domain="test", language="fr-FR")
        book.save(str(tmp_path))
        assert self._entry(tmp_path, book)["metadata"]["fill_mask"] == {
            "principal": [True, False],
            "alternatives": [[True, True]],
        }
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
        broken = _as_read(
            Message("10001", "Un fichier", plurals=[""]),
            "complete",
            sound.recorded.to_dict() if recorded else None,
        )
        book.add(broken)
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

    def test_load_a_broken_message_in_a_complete_book(self, tmp_path):
        """Read as draft with its Book, its record kept, with a warning."""
        message = self._message()
        message.mark_complete()
        book = Book([message], domain="test", language="fr-FR")
        book.save(str(tmp_path))
        data = json.loads((tmp_path / book.filename).read_text("utf-8"))
        data["10001"]["messages"]["alternatives"][0][1] = ""
        (tmp_path / book.filename).write_text(json.dumps(data), encoding="utf-8")
        reloaded = Book(domain="test", language="fr-FR")
        with pytest.warns(
            I18nToolsWarning,
            match=re.escape(
                "10001: complete message broken (the content differs from the "
                + "record: text (1, 1) lost): read as draft, and its Book with it"
            ),
        ):
            reloaded.load(str(tmp_path))
        loaded = reloaded.get("10001")
        assert loaded is not None
        assert loaded.status == "draft"
        assert loaded.recorded == message.recorded
        assert loaded.has_divergence
        assert [finding.severity for finding in reloaded.check()] == ["info"]
        reloaded.save(str(tmp_path))
        assert not loaded.has_divergence

    def test_writer_writes_the_record_of_a_complete_message(self):
        """The writer never replaces the record of a complete message."""
        reference = self._message()
        reference.mark_complete()
        diverging = _as_read(
            Message(
                "10001",
                "Un fichier",
                plurals=[""],
                alternatives=[["Un document", ""]],
            ),
            "complete",
            reference.recorded.to_dict(),
        )
        metadata = message_to_i18n_tools_format(diverging, "10001")["metadata"]
        assert metadata["fill_mask"] == {
            "principal": [True, True],
            "alternatives": [[True, True]],
        }
