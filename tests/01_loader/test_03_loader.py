"""Tests for loaders/loader.py (biface/i18n#31).

load_book() was already covered (A-01). load_locale_json(),
aggregate_locale_json(), save_locale_json(), and
save_aggregated_locale_json() had zero coverage despite #31 claiming
the whole loaders layer had none — verified by coverage measurement
(loader.py was at 43%, the rest of the loaders layer was already at
91-94%)."""

import gzip
import json

import pytest
import yaml

from i18n_tools.loaders.loader import (
    aggregate_locale_json,
    load_book,
    load_locale_json,
    save_aggregated_locale_json,
    save_locale_json,
)

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


class TestLoadLocaleJson:
    def test_load_locale_json_valid(self, tmp_path):
        file = tmp_path / "domain.json"
        file.write_text(json.dumps(VALID_DATA), encoding="utf-8")
        result = load_locale_json(str(file))
        assert result == VALID_DATA

    def test_load_locale_json_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_locale_json(str(tmp_path / "missing.json"))

    def test_load_locale_json_integrity_error(self, tmp_path):
        file = tmp_path / "domain.json"
        file.write_text(json.dumps(INVALID_DATA), encoding="utf-8")
        with pytest.raises(ValueError, match="Integrity check failed"):
            load_locale_json(str(file))


class TestSaveLocaleJson:
    def test_save_locale_json(self, tmp_path):
        file = tmp_path / "domain.json"
        save_locale_json(str(file), VALID_DATA)
        assert json.loads(file.read_text(encoding="utf-8")) == VALID_DATA


class TestAggregateLocaleJson:
    def test_aggregate_locale_json(self, tmp_path):
        module = "module_a"
        domain = "usage"
        locales = tmp_path / module / "locales"
        (locales / "fr").mkdir(parents=True)
        (locales / "fr-FR").mkdir(parents=True)

        fr_data = {"10001": [["Message"], ["Messages"]]}
        fr_fr_data = {"10002": [["Autre message"], ["Autres messages"]]}
        (locales / "fr" / f"{domain}.json").write_text(
            json.dumps(fr_data), encoding="utf-8"
        )
        (locales / "fr-FR" / f"{domain}.json").write_text(
            json.dumps(fr_fr_data), encoding="utf-8"
        )

        structure = {"base": str(tmp_path), "modules": [module]}
        domains = {module: [domain]}
        languages = {"fr": ["fr-FR"]}

        result = aggregate_locale_json(structure, domains, languages)

        assert result[module][domain]["fr"] == fr_data
        assert result[module][domain]["fr-FR"] == fr_fr_data

    def test_aggregate_locale_json_missing_variant_is_skipped(self, tmp_path):
        """A variant with no matching file on disk is simply absent from
        the result — aggregate_locale_json() does not raise."""
        module = "module_a"
        domain = "usage"
        locales = tmp_path / module / "locales"
        (locales / "fr").mkdir(parents=True)
        fr_data = {"10001": [["Message"], ["Messages"]]}
        (locales / "fr" / f"{domain}.json").write_text(
            json.dumps(fr_data), encoding="utf-8"
        )
        # No "fr-FR" directory/file created on purpose.

        structure = {"base": str(tmp_path), "modules": [module]}
        domains = {module: [domain]}
        languages = {"fr": ["fr-FR"]}

        result = aggregate_locale_json(structure, domains, languages)

        assert result[module][domain]["fr"] == fr_data
        assert "fr-FR" not in result[module][domain]


class TestSaveAggregatedLocaleJson:
    def test_save_aggregated_locale_json_creates_gzipped_files(self, tmp_path):
        aggregated_data = {
            "module_a": {
                "usage": {"fr": {"10001": [["Message"], ["Messages"]]}},
            }
        }

        save_aggregated_locale_json(aggregated_data, str(tmp_path))

        module_dir = tmp_path / "module_a"
        locales = module_dir / "locales"

        domain_gz = locales / "usage.json.gz"
        assert domain_gz.exists()
        assert not (locales / "usage.json").exists()
        with gzip.open(domain_gz, "rt", encoding="utf-8") as f:
            assert json.load(f) == {"fr": {"10001": [["Message"], ["Messages"]]}}

        # The module-level aggregate is written next to the module
        # directory itself, not inside locales/.
        module_gz = module_dir / "module_a.json.gz"
        assert module_gz.exists()
        assert not (module_dir / "module_a.json").exists()
        with gzip.open(module_gz, "rt", encoding="utf-8") as f:
            assert json.load(f) == aggregated_data["module_a"]

    def test_save_aggregated_locale_json_handles_submodules(self, tmp_path):
        aggregated_data = {
            "module_a/sub": {
                "usage": {"fr": {"10001": [["Message"], ["Messages"]]}},
            }
        }

        save_aggregated_locale_json(aggregated_data, str(tmp_path))

        module_dir = tmp_path / "module_a" / "sub"
        locales = module_dir / "locales"
        assert (locales / "usage.json.gz").exists()
        # Submodule aggregate is named after the last path segment ("sub").
        assert (module_dir / "sub.json.gz").exists()
