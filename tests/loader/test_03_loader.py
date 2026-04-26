"""Tests for load_book() — loaders/loader.py (A-01)."""

import json

import pytest

from i18n_tools.loaders.loader import load_book


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_DATA = {
    ".i18n_tools": {"version": "0.1.0"},
    "metadata": {"language": "fr-FR"},
    "10001": [["Un message"], ["Des messages"]],
    "10002": [["Un autre message", "Une variante"]],
}

INVALID_DATA = {
    "10001": "not-a-list",
}


def _write_i18t(directory, data, name="usage.json.i18t"):
    file = directory / name
    file.write_text(json.dumps(data), encoding="utf-8")
    return str(file)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_load_book_returns_filtered_dict(tmp_path):
    """Cas nominal : retourne un dict avec les bons msgids, clés réservées exclues."""
    result = load_book(_write_i18t(tmp_path, VALID_DATA))
    assert isinstance(result, dict)
    assert set(result.keys()) == {"10001", "10002"}
    assert ".i18n_tools" not in result
    assert "metadata" not in result


def test_load_book_entry_structure(tmp_path):
    """Chaque entrée contient les clés 'messages' et 'metadata'."""
    result = load_book(_write_i18t(tmp_path, VALID_DATA))
    for entry in result.values():
        assert "messages" in entry
        assert "metadata" in entry


def test_load_book_file_not_found(tmp_path):
    """Fichier inexistant → FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_book(str(tmp_path / "no_such_file.json.i18t"))


def test_load_book_integrity_error(tmp_path):
    """Matrice mal formée → ValueError."""
    with pytest.raises(ValueError):
        load_book(_write_i18t(tmp_path, INVALID_DATA))