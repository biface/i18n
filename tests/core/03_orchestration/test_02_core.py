"""
Test module for core.py — load_book, save_book, load_corpus, save_corpus,
synchronize (DD-28).
"""

import json
import warnings
from pathlib import Path

import pytest

from i18n_tools._finding import Finding
from i18n_tools.core import (
    inspect_corpus,
    load_book,
    load_corpus,
    save_book,
    save_corpus,
    synchronize,
)
from i18n_tools.exceptions import BookError, I18nToolsWarning
from i18n_tools.models.message import Declension, Message
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
        msg = Message(id="greeting", principal=Declension("Bonjour"))
        msg.add_language("fr-FR")
        book.messages["greeting"] = msg

        save_book(book, synchronized_repository, "app")

        reloaded = load_book(synchronized_repository, "app", "ui", "fr-FR")
        assert list(reloaded.messages.keys()) == ["greeting"]
        assert reloaded.messages["greeting"].principal.singular == "Bonjour"

    def test_raises_if_book_has_no_language(self, synchronized_repository):
        """Book.language may stay unset while the Book is being built,
        but the target directory depends on it: save_book must refuse."""
        book = load_book(synchronized_repository, "app", "ui", "fr-FR")
        book.remove_language()

        with pytest.raises(BookError, match="no language set"):
            save_book(book, synchronized_repository, "app")

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
            msg = Message(id="greeting", principal=Declension(f"hi-{lang}"))
            msg.add_language(lang)
            book.messages["greeting"] = msg

        save_corpus(corpus, synchronized_repository, "app")

        reloaded = load_corpus(synchronized_repository, "app", "ui")
        for lang in ("fr-FR", "en"):
            greeting = reloaded.get_real_book(lang).messages["greeting"]
            assert greeting.principal.singular == f"hi-{lang}"
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
        msg = Message(id="greeting", principal=Declension("Bonjour"))
        msg.add_language("fr-FR")
        book.messages["greeting"] = msg

        fallback_book = corpus.get_book("fr-CH", repository=synchronized_repository)
        assert fallback_book.get_message("greeting").principal.singular == "Bonjour"


def _book_file(repository, lang):
    """Path of the ui.json.i18t file of ``lang`` in module app."""
    root = repository[["paths", "repository"]]
    return Path(root, "app", "locales", lang, "LC_MESSAGES", "ui.json.i18t")


def _save_complete(repository, lang, matrix):
    """Save one complete message "items" in the Book of ``lang``."""
    book = load_book(repository, "app", "ui", lang)
    message = Message.from_matrix("items", matrix, metadata={"language": lang})
    message.mark_complete()
    book.messages["items"] = message
    save_book(book, repository, "app")


class TestInspectCorpus:
    def test_sound_repository(self, synchronized_repository):
        assert inspect_corpus(synchronized_repository, "app", "ui") == []

    def test_missing_directories(self, repository):
        findings = inspect_corpus(repository, "app", "ui")
        assert [(f.severity, f.where, f.language) for f in findings] == [
            ("error", "root", lang) for lang in ("en", "fr", "fr-BE", "fr-FR")
        ]

    def test_missing_file(self, synchronized_repository):
        path = _book_file(synchronized_repository, "fr-BE")
        path.unlink()
        assert inspect_corpus(synchronized_repository, "app", "ui") == [
            Finding("error", "root", f"file not found: {path}", "fr-BE")
        ]

    def test_file_findings_carry_their_language(self, synchronized_repository):
        path = _book_file(synchronized_repository, "fr-FR")
        data = json.loads(path.read_text(encoding="utf-8"))
        data["broken"] = "not-a-list"
        data["odd"] = {"messages": [["Un"]], "metadata": {"colour": "red"}}
        path.write_text(json.dumps(data), encoding="utf-8")
        findings = inspect_corpus(synchronized_repository, "app", "ui")
        assert [(f.severity, f.where, f.language) for f in findings] == [
            ("error", "broken", "fr-FR"),
            ("warning", "odd", "fr-FR"),
        ]

    def test_file_checked_against_its_language(self, synchronized_repository):
        path = _book_file(synchronized_repository, "fr-FR")
        data = json.loads(path.read_text(encoding="utf-8"))
        data["metadata"] = {**data.get("metadata", {}), "language": "en-US"}
        path.write_text(json.dumps(data), encoding="utf-8")
        findings = inspect_corpus(synchronized_repository, "app", "ui")
        assert [(f.severity, f.where, f.language) for f in findings] == [
            ("error", "root", "fr-FR")
        ]

    def test_warnings_listed_not_issued(self, synchronized_repository):
        path = _book_file(synchronized_repository, "fr-FR")
        data = json.loads(path.read_text(encoding="utf-8"))
        data["odd"] = {"messages": [["Un"]], "metadata": {"colour": "red"}}
        path.write_text(json.dumps(data), encoding="utf-8")
        with warnings.catch_warnings(record=True) as record:
            warnings.simplefilter("always", I18nToolsWarning)
            findings = inspect_corpus(synchronized_repository, "app", "ui")
        assert [w for w in record if issubclass(w.category, I18nToolsWarning)] == []
        assert [(f.severity, f.language) for f in findings] == [("warning", "fr-FR")]

    def test_corpus_findings_follow(self, synchronized_repository):
        _save_complete(synchronized_repository, "en", [["{n} item"]])
        _save_complete(synchronized_repository, "fr-FR", [["{count} article"]])
        findings = inspect_corpus(synchronized_repository, "app", "ui")
        assert [(f.where, f.language) for f in findings] == [("items", None)]
        assert findings[0].message.startswith("tokens of cell (variant 0, segment 0)")

    def test_defective_file_left_out_of_corpus_check(self, synchronized_repository):
        _save_complete(synchronized_repository, "en", [["{n} item"]])
        _save_complete(synchronized_repository, "fr-FR", [["{count} article"]])
        path = _book_file(synchronized_repository, "fr-FR")
        data = json.loads(path.read_text(encoding="utf-8"))
        data["broken"] = "not-a-list"
        path.write_text(json.dumps(data), encoding="utf-8")
        findings = inspect_corpus(synchronized_repository, "app", "ui")
        # Only the findings of the fr-FR file (the broken entry, and the
        # root statistics it no longer matches): no corpus finding.
        assert ("error", "broken") in [(f.severity, f.where) for f in findings]
        assert {f.language for f in findings} == {"fr-FR"}

    def test_files_left_unchanged(self, synchronized_repository):
        _save_complete(synchronized_repository, "en", [["{n} item"]])
        path = _book_file(synchronized_repository, "en")
        before = path.read_bytes()
        _ = inspect_corpus(synchronized_repository, "app", "ui")
        assert path.read_bytes() == before

    @pytest.mark.parametrize(
        "args",
        [("not a repository", "app", "ui"), (None, 1, "ui"), (None, "app", 1)],
        ids=["repository", "module", "domain"],
    )
    def test_argument_guards(self, synchronized_repository, args):
        repository = args[0] if args[0] is not None else synchronized_repository
        with pytest.raises(TypeError, match="inspect_corpus"):
            inspect_corpus(repository, *args[1:])
