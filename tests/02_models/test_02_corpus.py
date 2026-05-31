"""
Tests for Corpus, FallbackBook and Encyclopaedia (DD-09, DD-09b, DD-07).

References
----------
- biface/i18n#43 : Corpus / FallbackBook design (DD-09, DD-09b)
- biface/i18n#42 : four-level model hierarchy (DD-07)
- biface/i18n#20 : MessageNotFoundError (DD-24)
"""

import pytest

from i18n_tools.exceptions import MessageNotFoundError
from i18n_tools.models.corpus import Book, Corpus, Encyclopaedia, FallbackBook

# ---------------------------------------------------------------------------
# TestCorpusInit
# ---------------------------------------------------------------------------


class TestCorpusInit:
    """Corpus initialisation and basic properties."""

    def test_init_with_domain(self):
        corpus = Corpus(domain="test")
        assert corpus.domain == "test"
        assert corpus.languages == []

    def test_init_wrong_type_raises(self):
        with pytest.raises(TypeError):
            Corpus(domain=42)

    def test_repr(self):
        corpus = Corpus(domain="test")
        assert "test" in repr(corpus)


# ---------------------------------------------------------------------------
# TestCorpusAddBook
# ---------------------------------------------------------------------------


class TestCorpusAddBook:
    """Corpus.add_book() — registration and error cases."""

    def test_add_book_registers_language(self, fr_fr_book):
        corpus = Corpus(domain="test")
        corpus.add_book(fr_fr_book)
        assert "fr-FR" in corpus.languages

    def test_add_multiple_books(self, fr_fr_book, en_us_book):
        corpus = Corpus(domain="test")
        corpus.add_book(fr_fr_book)
        corpus.add_book(en_us_book)
        assert set(corpus.languages) == {"fr-FR", "en-US"}

    def test_add_book_wrong_type_raises(self):
        corpus = Corpus(domain="test")
        with pytest.raises(TypeError):
            corpus.add_book("not a book")

    def test_add_book_wrong_domain_raises(self, fr_fr_book):
        corpus = Corpus(domain="other_domain")
        with pytest.raises(ValueError, match="domain"):
            corpus.add_book(fr_fr_book)

    def test_add_duplicate_language_raises(self, fr_fr_book):
        corpus = Corpus(domain="test")
        corpus.add_book(fr_fr_book)
        with pytest.raises(ValueError, match="already registered"):
            corpus.add_book(fr_fr_book)


# ---------------------------------------------------------------------------
# TestCorpusGetBook
# ---------------------------------------------------------------------------


class TestCorpusGetBook:
    """Corpus.get_book() — FallbackBook construction and chain resolution."""

    def test_get_exact_language(self, fr_fr_book):
        corpus = Corpus(domain="test")
        corpus.add_book(fr_fr_book)
        fb = corpus.get_book("fr-FR")
        assert isinstance(fb, FallbackBook)
        assert fb.language == "fr-FR"

    def test_get_book_fallback_to_parent(self, fr_fr_book):
        """fr-CH not loaded — should fall back to fr-FR (same IETF parent 'fr')."""
        corpus = Corpus(domain="test")
        corpus.add_book(fr_fr_book)
        fb = corpus.get_book("fr-CH")
        assert isinstance(fb, FallbackBook)
        assert fb.language == "fr-CH"
        # fr-FR must be in the chain
        assert any(b.language == "fr-FR" for b in fb._chain)

    def test_get_book_no_match_raises(self):
        """Requesting any language from an empty Corpus raises MessageNotFoundError."""
        corpus = Corpus(domain="test")
        with pytest.raises(MessageNotFoundError):
            corpus.get_book("de-DE")

    def test_get_book_empty_corpus_raises(self):
        corpus = Corpus(domain="test")
        with pytest.raises(MessageNotFoundError):
            corpus.get_book("fr-FR")

    def test_get_book_returns_fallback_book(self, fr_fr_book, en_us_book):
        corpus = Corpus(domain="test")
        corpus.add_book(fr_fr_book)
        corpus.add_book(en_us_book)
        fb = corpus.get_book("fr-FR")
        assert isinstance(fb, FallbackBook)


# ---------------------------------------------------------------------------
# TestCorpusCoverage
# ---------------------------------------------------------------------------


class TestCorpusCoverage:
    """Corpus.coverage() — coverage rate per language."""

    def test_full_coverage(self, fr_fr_book, en_us_book):
        """Both books have the same ids → coverage 1.0 each."""
        corpus = Corpus(domain="test")
        corpus.add_book(fr_fr_book)
        corpus.add_book(en_us_book)
        cov = corpus.coverage()
        assert cov["fr-FR"] == pytest.approx(1.0)
        assert cov["en-US"] == pytest.approx(1.0)

    def test_empty_corpus_returns_empty(self):
        corpus = Corpus(domain="test")
        assert corpus.coverage() == {}

    def test_single_book_full_coverage(self, fr_fr_book):
        corpus = Corpus(domain="test")
        corpus.add_book(fr_fr_book)
        cov = corpus.coverage()
        assert cov["fr-FR"] == pytest.approx(1.0)

    def test_partial_coverage(self, fr_fr_book, en_us_book, fr_fr_messages):
        """A book with a subset of ids has coverage < 1.0."""
        # Build a partial en-US book with only 5 of the 10 messages
        partial_ids = list(fr_fr_messages.keys())[:5]
        partial_messages = [
            msg for mid, msg in fr_fr_messages.items() if mid in partial_ids
        ]
        # Create a partial fr-FR-like book in en-US (reuse en_us_book fixture msgs)
        en_us_msg_list = list(en_us_book.messages.values())
        partial_book = Book(*en_us_msg_list[:5], domain="test", language="en-US")
        corpus = Corpus(domain="test")
        corpus.add_book(fr_fr_book)
        corpus.add_book(partial_book)
        cov = corpus.coverage()
        assert cov["fr-FR"] == pytest.approx(1.0)
        assert cov["en-US"] == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# TestCorpusMissing
# ---------------------------------------------------------------------------


class TestCorpusMissing:
    """Corpus.missing() — identifiers absent in a given language."""

    def test_no_missing_when_full(self, fr_fr_book, en_us_book):
        corpus = Corpus(domain="test")
        corpus.add_book(fr_fr_book)
        corpus.add_book(en_us_book)
        assert corpus.missing("fr-FR") == []
        assert corpus.missing("en-US") == []

    def test_missing_returns_sorted_ids(self, fr_fr_book, en_us_book):
        """Partial en-US book → missing returns sorted list of absent ids."""
        en_us_msg_list = list(en_us_book.messages.values())
        partial_book = Book(*en_us_msg_list[:5], domain="test", language="en-US")
        corpus = Corpus(domain="test")
        corpus.add_book(fr_fr_book)
        corpus.add_book(partial_book)
        missing = corpus.missing("en-US")
        assert missing == sorted(missing)
        assert len(missing) == 5

    def test_missing_unknown_language_raises(self, fr_fr_book):
        corpus = Corpus(domain="test")
        corpus.add_book(fr_fr_book)
        with pytest.raises(ValueError, match="not loaded"):
            corpus.missing("de-DE")


# ---------------------------------------------------------------------------
# TestFallbackBookInit
# ---------------------------------------------------------------------------


class TestFallbackBookInit:
    """FallbackBook initialisation."""

    def test_init_single_book(self, fr_fr_book):
        fb = FallbackBook([fr_fr_book], "fr-FR")
        assert fb.language == "fr-FR"
        assert fb.domain == "test"

    def test_init_empty_chain_raises(self):
        with pytest.raises(ValueError, match="at least one Book"):
            FallbackBook([], "fr-FR")

    def test_len(self, fr_fr_book):
        fb = FallbackBook([fr_fr_book], "fr-FR")
        assert len(fb) == len(fr_fr_book.messages)

    def test_contains_existing_id(self, fr_fr_book):
        fb = FallbackBook([fr_fr_book], "fr-FR")
        assert "1100" in fb

    def test_contains_missing_id(self, fr_fr_book):
        fb = FallbackBook([fr_fr_book], "fr-FR")
        assert "9999" not in fb

    def test_iter_yields_messages(self, fr_fr_book):
        fb = FallbackBook([fr_fr_book], "fr-FR")
        messages = list(fb)
        assert len(messages) == len(fr_fr_book.messages)

    def test_repr(self, fr_fr_book):
        fb = FallbackBook([fr_fr_book], "fr-FR")
        assert "fr-FR" in repr(fb)


# ---------------------------------------------------------------------------
# TestFallbackBookGetMessage
# ---------------------------------------------------------------------------


class TestFallbackBookGetMessage:
    """FallbackBook.get_message() — chain resolution per message."""

    def test_get_message_from_first_book(self, fr_fr_book):
        fb = FallbackBook([fr_fr_book], "fr-FR")
        msg = fb.get_message("1100")
        assert msg.id == "1100"

    def test_get_message_falls_back_to_second_book(self, fr_fr_book, en_us_book):
        """Chain [partial_fr, en_us]: id absent in partial_fr is found in en_us."""
        # Build a partial fr-FR book missing "1109"
        fr_msgs = list(fr_fr_book.messages.values())
        partial_fr = Book(*fr_msgs[:-1], domain="test", language="fr-FR")
        fb = FallbackBook([partial_fr, en_us_book], "fr-FR")
        msg = fb.get_message("1109")
        # Must come from en_us_book since partial_fr doesn't have it
        assert msg.id == "1109"
        assert msg.metadata["language"] == "en-US"

    def test_get_message_not_found_raises(self, fr_fr_book):
        fb = FallbackBook([fr_fr_book], "fr-FR")
        with pytest.raises(MessageNotFoundError, match="9999"):
            fb.get_message("9999")

    def test_get_message_prefers_first_in_chain(self, fr_fr_book, en_us_book):
        """id present in both books → first book wins."""
        fb = FallbackBook([fr_fr_book, en_us_book], "fr-FR")
        msg = fb.get_message("1100")
        assert msg.metadata["language"] == "fr-FR"


# ---------------------------------------------------------------------------
# TestEncyclopaediaInit
# ---------------------------------------------------------------------------


class TestEncyclopaediaInit:
    """Encyclopaedia initialisation."""

    def test_init_empty(self):
        enc = Encyclopaedia()
        assert len(enc) == 0

    def test_repr(self):
        enc = Encyclopaedia()
        assert "Encyclopaedia" in repr(enc)


# ---------------------------------------------------------------------------
# TestEncyclopaediaAddGet
# ---------------------------------------------------------------------------


class TestEncyclopaediaAddGet:
    """Encyclopaedia.add_corpus() and get_corpus()."""

    def test_add_and_get_corpus(self, fr_fr_book):
        corpus = Corpus(domain="test")
        corpus.add_book(fr_fr_book)
        enc = Encyclopaedia()
        enc.add_corpus("src/app", corpus)
        retrieved = enc.get_corpus("src/app", "test")
        assert retrieved is corpus

    def test_contains(self, fr_fr_book):
        corpus = Corpus(domain="test")
        corpus.add_book(fr_fr_book)
        enc = Encyclopaedia()
        enc.add_corpus("src/app", corpus)
        assert ("src/app", "test") in enc
        assert ("src/app", "other") not in enc

    def test_add_wrong_type_module_raises(self, fr_fr_book):
        corpus = Corpus(domain="test")
        enc = Encyclopaedia()
        with pytest.raises(TypeError):
            enc.add_corpus(42, corpus)

    def test_add_wrong_type_corpus_raises(self):
        enc = Encyclopaedia()
        with pytest.raises(TypeError):
            enc.add_corpus("src/app", "not a corpus")

    def test_add_duplicate_raises(self, fr_fr_book):
        corpus = Corpus(domain="test")
        corpus.add_book(fr_fr_book)
        enc = Encyclopaedia()
        enc.add_corpus("src/app", corpus)
        with pytest.raises(ValueError, match="already registered"):
            enc.add_corpus("src/app", corpus)

    def test_get_nonexistent_raises(self):
        enc = Encyclopaedia()
        with pytest.raises(KeyError):
            enc.get_corpus("src/app", "test")

    def test_len(self, fr_fr_book, en_us_book):
        corpus1 = Corpus(domain="test")
        corpus1.add_book(fr_fr_book)
        corpus2 = Corpus(domain="test")
        corpus2.add_book(en_us_book)
        enc = Encyclopaedia()
        enc.add_corpus("src/app", corpus1)
        enc.add_corpus("src/other", corpus2)
        assert len(enc) == 2
