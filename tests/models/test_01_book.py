"""
Minimal test file for Book model using shared fixtures from tests/models/conftest.py
"""

import re
import pytest

from i18n_tools.models.corpus import Book

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
