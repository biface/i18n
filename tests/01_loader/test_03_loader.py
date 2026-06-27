"""Tests for load_book() — loaders/loader.py (A-01)."""

import json

import pytest
import yaml

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


def _write_yaml_i18t(directory, data, name="usage.yaml.i18t"):
    file = directory / name
    file.write_text(yaml.safe_dump(data), encoding="utf-8")
    return str(file)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestLoadBook:
    def test_load_book_detects_yaml_format(self, tmp_path):
        """biface/i18n#67 — un fichier .yaml.i18t doit être chargé en YAML,
        pas toujours en JSON. Avant #67, load_book() ignorait le format
        détecté et appelait systématiquement _load_json()."""
        result = load_book(_write_yaml_i18t(tmp_path, VALID_DATA))
        assert set(result.keys()) == {"10001", "10002"}
        assert result["10001"]["messages"] == [["Un message"], ["Des messages"]]

    def test_load_book_returns_filtered_dict(self, tmp_path):
        """Cas nominal : retourne un dict avec les bons msgids, clés réservées exclues."""
        result = load_book(_write_i18t(tmp_path, VALID_DATA))
        assert isinstance(result, dict)
        assert set(result.keys()) == {"10001", "10002"}
        assert ".i18n_tools" not in result
        assert "metadata" not in result

    def test_load_book_entry_structure(self, tmp_path):
        """Chaque entrée contient les clés 'messages' et 'metadata'."""
        result = load_book(_write_i18t(tmp_path, VALID_DATA))
        for entry in result.values():
            assert "messages" in entry
            assert "metadata" in entry

    def test_load_book_file_not_found(self, tmp_path):
        """Fichier inexistant → FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_book(str(tmp_path / "no_such_file.json.i18t"))

    def test_load_book_integrity_error(self, tmp_path):
        """Matrice mal formée → ValueError."""
        with pytest.raises(ValueError):
            load_book(_write_i18t(tmp_path, INVALID_DATA))
