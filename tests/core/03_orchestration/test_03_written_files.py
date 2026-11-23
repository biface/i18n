"""
Files written by the package against format 1.0.0.

The files written by ``Book.save()`` and by ``sync`` are validated against
the JSON Schema of the package, then compared with the valid fixtures of
``tests/mock/format/1.0.0/valid``, which were written by a generator and
not by the code. ``po_revision_date``, the date of the write, is the only
value set apart.
"""

import json
import shutil
from importlib import resources
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

from i18n_tools.models.book import Book
from i18n_tools.models.message import Message
from i18n_tools.sync import check_repository

VALID = Path(__file__).resolve().parents[2] / "mock" / "format" / "1.0.0" / "valid"


@pytest.fixture(scope="module")
def validator() -> Draft202012Validator:
    path = resources.files("i18n_tools") / "schemas" / "i18t-1.0.0.schema.json"
    return Draft202012Validator(json.loads(path.read_text(encoding="utf-8")))


def _read(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if path.name.endswith(".yaml.i18t"):
        return yaml.safe_load(text)
    return json.loads(text)


def _without_revision_date(text: str) -> str:
    """The text of a file, its po_revision_date line set apart."""
    return "\n".join(
        "po_revision_date" if "po_revision_date" in line else line
        for line in text.splitlines()
    )


def _same_file(written: Path, fixture: Path) -> bool:
    """Same text, the date of the write apart."""
    return _without_revision_date(written.read_text(encoding="utf-8")) == (
        _without_revision_date(fixture.read_text(encoding="utf-8"))
    )


def _errors_book() -> Book:
    """The Book of errors.json.i18t, built with the API of the model."""
    missing = Message(
        "files.missing",
        "File {name} is missing.",
        plurals=["{n} files are missing."],
        alternatives=[["File {name} is missing from {repository}.", ""]],
        context="sync report",
        flags=["python-format"],
    )
    missing.add_location("src/app/sync.py", 42)
    missing.add_location("src/app/sync.py", 57, variant=1, segment=0)
    missing.mark_complete()
    alert = Message(
        "disk.alert",
        "Disk usage is normal.",
        plurals=[
            "Disk usage is high ({percent} %).",
            "Disk is almost full ({percent} %).",
        ],
        flags=["python-format"],
    )
    alert.add_location("src/app/monitor.py", 18)
    book = Book(missing, alert, language="en-US", domain="errors")
    book.set_gettext(
        project_id_version="sync-app 2.1",
        report_msgid_bugs_to="i18n@example.org",
        pot_creation_date="2026-11-20 20:22+0100",
    )
    return book


def _rules_book() -> Book:
    """The Book of rules.json.i18t, built with the API of the model."""
    quota = Message(
        "quota.used",
        "Quota normal.",
        plurals=["Quota presque atteint ({used} sur {limit}).", "Quota dépassé."],
        alternatives=[
            ["Quota du dépôt normal.", " ", "Quota du dépôt dépassé de {excess}."]
        ],
        rules={"opaque": {"content": ["kept", "unchanged"]}},
    )
    book = Book(quota, language="fr-FR", domain="rules")
    book.set_metadata("rules", {"opaque": True})
    return book


class TestBookSave:
    @pytest.mark.parametrize(
        "build, name",
        [
            (_errors_book, "errors.json.i18t"),
            (_rules_book, "rules.json.i18t"),
            (lambda: Book(language="fr-FR", domain="messages"), "messages.json.i18t"),
        ],
        ids=["errors", "rules", "empty"],
    )
    def test_book_built_in_memory(self, tmp_path, validator, build, name):
        book = build()
        book.save(str(tmp_path))
        written = tmp_path / name
        assert list(validator.iter_errors(_read(written))) == []
        assert _same_file(written, VALID / name)

    @pytest.mark.parametrize(
        "name", sorted(path.name for path in VALID.glob("*.i18t")), ids=str
    )
    def test_book_loaded_then_saved(self, tmp_path, validator, name):
        shutil.copy(VALID / name, tmp_path / name)
        data = _read(VALID / name)
        book = Book(
            language=data["metadata"]["language"],
            domain=data["metadata"]["domain"],
            file_format="yaml" if name.endswith(".yaml.i18t") else "json",
        )
        book.load(str(tmp_path))
        book.save(str(tmp_path))
        assert list(validator.iter_errors(_read(tmp_path / name))) == []
        assert _same_file(tmp_path / name, VALID / name)


class TestSync:
    def test_empty_book(self, tmp_path, validator):
        check_repository(
            str(tmp_path),
            {"app": ["messages"]},
            {"source": "fr-FR", "hierarchy": {}},
        )
        written = tmp_path / "app" / "locales" / "fr-FR" / "LC_MESSAGES"
        written = written / "messages.json.i18t"
        assert list(validator.iter_errors(_read(written))) == []
        assert written.read_text(encoding="utf-8") == (
            VALID / "messages.json.i18t"
        ).read_text(encoding="utf-8")
