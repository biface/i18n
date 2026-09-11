"""
Test module for core.py — load_book, save_book, load_corpus, save_corpus,
synchronize (DD-28).
"""

import pytest

from i18n_tools.core import (
    load_book,
    load_corpus,
    save_book,
    save_corpus,
    synchronize,
)
from i18n_tools.models.corpus import Message
from i18n_tools.models.repository import Repository


@pytest.fixture
def repository(tmp_path) -> Repository:
    """A Repository rooted at a fresh tmp_path, with one module/domain
    and a small language hierarchy, not yet synchronized on disk."""
    repo = Repository()
    repo[["paths", "repository"]] = str(tmp_path)
    repo.add_module("app")
    repo.domains = {"app": ["ui"]}
    repo.source = "en"
    repo.hierarchy = {"fr": ["fr-FR", "fr-BE"]}
    return repo


@pytest.fixture
def synchronized_repository(repository) -> Repository:
    synchronize(repository)
    return repository


class TestSynchronize:
    def test_creates_expected_directory_structure(self, repository, tmp_path):
        synchronize(repository)

        for lang in ("en", "fr", "fr-FR", "fr-BE"):
            lc_messages = tmp_path / "app" / "locales" / lang / "LC_MESSAGES"
            assert lc_messages.is_dir()

        templates = tmp_path / "app" / "locales" / "templates"
        assert templates.is_dir()

    def test_is_idempotent(self, repository):
        synchronize(repository)
        synchronize(repository)  # must not raise or duplicate anything


class TestLoadBook:
    def test_load_empty_book_after_synchronize(self, synchronized_repository):
        book = load_book(synchronized_repository, "app", "ui", "fr-FR")
        assert book.language == "fr-FR"
        assert book.domain == "ui"
        assert len(book.messages) == 0

    def test_raises_if_not_synchronized(self, repository):
        with pytest.raises(OSError):
            load_book(repository, "app", "ui", "fr-FR")


class TestSaveBook:
    def test_round_trip_a_message(self, synchronized_repository):
        book = load_book(synchronized_repository, "app", "ui", "fr-FR")
        msg = Message(id="greeting", default="Bonjour")
        msg.add_language("fr-FR")
        book.messages["greeting"] = msg

        save_book(book, synchronized_repository, "app")

        reloaded = load_book(synchronized_repository, "app", "ui", "fr-FR")
        assert list(reloaded.messages.keys()) == ["greeting"]
        assert reloaded.messages["greeting"].default == "Bonjour"

    def test_module_is_required_explicitly(self, synchronized_repository):
        """save_book takes module explicitly — Book itself never carries
        it (only Encyclopaedia and this orchestration layer do)."""
        book = load_book(synchronized_repository, "app", "ui", "en")
        assert not hasattr(book, "module")


class TestLoadCorpus:
    def test_loads_every_configured_language(self, synchronized_repository):
        corpus = load_corpus(synchronized_repository, "app", "ui")
        assert sorted(corpus.languages) == ["en", "fr", "fr-BE", "fr-FR"]

    def test_each_loaded_book_is_empty_and_matches_domain(
        self, synchronized_repository
    ):
        corpus = load_corpus(synchronized_repository, "app", "ui")
        for lang in corpus.languages:
            book = corpus.get_real_book(lang)
            assert book.domain == "ui"
            assert len(book.messages) == 0


class TestSaveCorpus:
    def test_round_trip_across_languages(self, synchronized_repository):
        corpus = load_corpus(synchronized_repository, "app", "ui")

        for lang in ("fr-FR", "en"):
            book = corpus.get_real_book(lang)
            msg = Message(id="greeting", default=f"hi-{lang}")
            msg.add_language(lang)
            book.messages["greeting"] = msg

        save_corpus(corpus, synchronized_repository, "app")

        reloaded = load_corpus(synchronized_repository, "app", "ui")
        assert reloaded.get_real_book("fr-FR").messages["greeting"].default == (
            "hi-fr-FR"
        )
        assert reloaded.get_real_book("en").messages["greeting"].default == "hi-en"
        # Untouched language stays empty
        assert len(reloaded.get_real_book("fr-BE").messages) == 0


class TestLoadCorpusThenGetBookWithRepository:
    """End-to-end: a Corpus loaded via core.load_corpus() resolves
    fallback correctly when queried with the same repository."""

    def test_get_book_resolves_through_declared_hierarchy(
        self, synchronized_repository
    ):
        corpus = load_corpus(synchronized_repository, "app", "ui")
        book = corpus.get_real_book("fr-FR")
        msg = Message(id="greeting", default="Bonjour")
        msg.add_language("fr-FR")
        book.messages["greeting"] = msg

        fallback_book = corpus.get_book("fr-CH", repository=synchronized_repository)
        assert fallback_book.get_message("greeting").default == "Bonjour"
