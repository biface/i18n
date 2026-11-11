"""Tests for loaders/loader.py (biface/i18n#31).

load_book() was already covered (A-01). load_locale_json(),
aggregate_locale_json(), save_locale_json(), and
save_aggregated_locale_json() had zero coverage despite #31 claiming
the whole loaders layer had none — verified by coverage measurement
(loader.py was at 43%, the rest of the loaders layer was already at
91-94%)."""

import gzip
import json
import re
import warnings

import pytest
import yaml

from i18n_tools._finding import Finding
from i18n_tools.exceptions import FormatError, I18nToolsWarning
from i18n_tools.loaders import loader as loader_module
from i18n_tools.loaders.loader import (
    aggregate_locale_json,
    inspect_book_file,
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
        détecté et appelait systématiquement load_json()."""
        result = load_book(_write_yaml_i18t(tmp_path, VALID_DATA))["entries"]
        assert set(result.keys()) == {"10001", "10002"}
        assert result["10001"]["messages"] == [["Un message"], ["Des messages"]]

    def test_load_book_returns_filtered_dict(self, tmp_path):
        """Cas nominal : retourne un dict avec les bons msgids, clés réservées exclues."""
        result = load_book(_write_i18t(tmp_path, VALID_DATA))["entries"]
        assert isinstance(result, dict)
        assert set(result.keys()) == {"10001", "10002"}
        assert ".i18n_tools" not in result
        assert "metadata" not in result

    def test_load_book_returns_root_metadata(self, tmp_path):
        """The root metadata of the file is returned apart from the entries."""
        content = load_book(_write_i18t(tmp_path, VALID_DATA))
        assert content["metadata"] == {"language": "fr-FR"}

    def test_load_book_without_root_metadata(self, tmp_path):
        """A file without root metadata yields an empty mapping."""
        content = load_book(_write_i18t(tmp_path, {"10001": [["Un message"]]}))
        assert content["metadata"] == {}

    def test_load_book_entry_structure(self, tmp_path):
        """Chaque entrée contient les clés 'messages' et 'metadata'."""
        result = load_book(_write_i18t(tmp_path, VALID_DATA))["entries"]
        for entry in result.values():
            assert "messages" in entry
            assert "metadata" in entry

    @pytest.mark.parametrize("severity, warned", [("info", False), ("warning", True)])
    def test_load_book_warns_for_warnings_only(
        self, tmp_path, monkeypatch, severity, warned
    ):
        """Information findings are neither raised nor issued as warnings."""
        path = _write_i18t(tmp_path, VALID_DATA)
        monkeypatch.setattr(
            loader_module,
            "inspect_book_data",
            lambda data, language=None, domain=None: [
                Finding(severity, "10001", "a finding")
            ],
        )
        with warnings.catch_warnings(record=True) as record:
            warnings.simplefilter("always", I18nToolsWarning)
            content = load_book(path)
        assert set(content["entries"].keys()) == {"10001", "10002"}
        issued = [w for w in record if issubclass(w.category, I18nToolsWarning)]
        assert len(issued) == (1 if warned else 0)

    def test_load_book_file_not_found(self, tmp_path):
        """Fichier inexistant → FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_book(str(tmp_path / "no_such_file.json.i18t"))

    def test_load_book_integrity_error(self, tmp_path):
        """Matrice mal formée → FormatError."""
        with pytest.raises(FormatError):
            load_book(_write_i18t(tmp_path, INVALID_DATA))

    def test_load_book_native_entry_keeps_metadata(self, tmp_path):
        """A native entry keeps its matrix and its metadata."""
        data = {
            "10001": {
                "messages": [["Un message", "Une variante"], ["Des messages", ""]],
                "metadata": {"locations": [["app.py", 12]], "flags": ["fuzzy"]},
            }
        }
        result = load_book(_write_i18t(tmp_path, data))["entries"]
        assert result["10001"]["messages"] == data["10001"]["messages"]
        assert result["10001"]["metadata"] == data["10001"]["metadata"]

    def test_load_book_native_entry_without_metadata(self, tmp_path):
        """The metadata key of a native entry is optional."""
        data = {"10001": {"messages": [["Un message"]]}}
        result = load_book(_write_i18t(tmp_path, data))["entries"]
        assert result["10001"] == {"messages": [["Un message"]], "metadata": {}}

    def test_load_book_mixed_entry_forms(self, tmp_path):
        """Native and legacy entries can share one file."""
        data = {
            "10001": {"messages": [["Un message"]], "metadata": {}},
            "10002": [["Un autre message"]],
        }
        result = load_book(_write_i18t(tmp_path, data))["entries"]
        assert result["10002"] == {"messages": [["Un autre message"]], "metadata": {}}

    @pytest.mark.parametrize(
        "entry",
        [
            {"metadata": {}},
            {"messages": [["a", "b"], ["c"]]},
            {"messages": [["a"]], "metadata": []},
            {"messages": "not-a-list"},
            {"messages": [[]]},
        ],
        ids=[
            "no-messages",
            "ragged-matrix",
            "metadata-not-dict",
            "matrix-not-list",
            "empty-rows",
        ],
    )
    def test_load_book_native_entry_integrity_error(self, tmp_path, entry):
        """A malformed native entry fails the integrity check."""
        with pytest.raises(FormatError):
            load_book(_write_i18t(tmp_path, {"10001": entry}))


class TestInspectBookFile:
    """inspect_book_file() — every finding of a file, nothing raised or warned."""

    def test_sound_file(self, tmp_path):
        assert inspect_book_file(_write_i18t(tmp_path, VALID_DATA)) == []

    def test_sound_yaml_file(self, tmp_path):
        assert inspect_book_file(_write_yaml_i18t(tmp_path, VALID_DATA)) == []

    def test_every_severity_returned_nothing_warned(self, tmp_path):
        data = {
            "10001": "not-a-list",
            "10002": {"messages": [["Un message"]], "metadata": {"colour": "red"}},
            "10003": {
                "messages": [["Un", "Une"], ["Des", ""]],
                "metadata": {
                    "status": "draft",
                    **SOUND_RECORD,
                    "fill_mask": [[True, True], [True, True]],
                },
            },
        }
        path = _write_i18t(tmp_path, data)
        with warnings.catch_warnings(record=True) as record:
            warnings.simplefilter("always", I18nToolsWarning)
            findings = inspect_book_file(path)
        assert [w for w in record if issubclass(w.category, I18nToolsWarning)] == []
        assert [(f.severity, f.where) for f in findings] == [
            ("error", "10001"),
            ("warning", "10002"),
            ("info", "10003"),
        ]

    @pytest.mark.parametrize(
        "language, domain, expected",
        [
            ("en-US", None, "language"),
            (None, "other", "domain 'usage' is not 'other'"),
        ],
        ids=["language", "domain"],
    )
    def test_language_and_domain_compared(self, tmp_path, language, domain, expected):
        data = {**VALID_DATA, "metadata": {"language": "fr-FR", "domain": "usage"}}
        findings = inspect_book_file(_write_i18t(tmp_path, data), language, domain)
        assert [f.severity for f in findings] == ["error"]
        assert findings[0].where == "root"
        assert expected in findings[0].message

    @pytest.mark.parametrize(
        "name, text",
        [
            ("usage.json.i18t", "{not json"),
            ("usage.yaml.i18t", "key: [unclosed"),
        ],
        ids=["json", "yaml"],
    )
    def test_unreadable_content(self, tmp_path, name, text):
        file = tmp_path / name
        file.write_text(text, encoding="utf-8")
        [finding] = inspect_book_file(str(file))
        assert (finding.severity, finding.where) == ("error", "root")
        assert finding.message.startswith("unreadable content: ")

    @pytest.mark.parametrize(
        "name, text",
        [("usage.json.i18t", "[1, 2]"), ("usage.yaml.i18t", "- a\n- b\n")],
        ids=["json", "yaml"],
    )
    def test_content_not_a_mapping(self, tmp_path, name, text):
        file = tmp_path / name
        file.write_text(text, encoding="utf-8")
        assert inspect_book_file(str(file)) == [
            Finding("error", "root", "content is not a mapping")
        ]

    def test_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            inspect_book_file(str(tmp_path / "no_such_file.json.i18t"))

    @pytest.mark.parametrize(
        "args",
        [(42,), ("usage.json.i18t", 1), ("usage.json.i18t", None, 1)],
        ids=["file_path", "language", "domain"],
    )
    def test_argument_guards(self, args):
        with pytest.raises(TypeError, match="inspect_book_file"):
            inspect_book_file(*args)


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


# ---------------------------------------------------------------------------
# Status and recorded counters of an entry (DD-45)
# ---------------------------------------------------------------------------

RECORD_MATRIX = [["Un fichier", "Un document"], ["Des fichiers", ""]]
SOUND_RECORD = {
    "singular_count": 2,
    "segment_count": 2,
    "fill_mask": [[True, True], [True, False]],
}


def _load_entry(tmp_path, entry_metadata):
    """Load a file holding one entry; return the I18nToolsWarning messages."""
    data = {
        "metadata": {"language": "fr-FR"},
        "10001": {"messages": RECORD_MATRIX, "metadata": entry_metadata},
    }
    path = _write_i18t(tmp_path, data)
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always", I18nToolsWarning)
        load_book(path)
    return [str(w.message) for w in record if issubclass(w.category, I18nToolsWarning)]


class TestLoadBookRecord:
    @pytest.mark.parametrize(
        "entry_metadata",
        [
            {},
            {"singular_count": 2},
            {"plural_counts": [1, 0]},
            {"plural_counts": "not checked"},
            {"status": "draft", **SOUND_RECORD},
            {"status": "complete", **SOUND_RECORD},
            {
                "status": "draft",
                **SOUND_RECORD,
                "fill_mask": [[True, True], [True, True]],
            },
        ],
        ids=[
            "legacy-no-status",
            "legacy-singular-count",
            "legacy-plural-counts",
            "plural-counts-ignored",
            "sound-draft",
            "sound-complete",
            "diverging-draft-is-info",
        ],
    )
    def test_loads_without_warning(self, tmp_path, entry_metadata):
        assert _load_entry(tmp_path, entry_metadata) == []

    @pytest.mark.parametrize(
        "entry_metadata, expected",
        [
            (
                {"status": "final", **SOUND_RECORD},
                "status 'final' is not 'draft' or 'complete': read as draft",
            ),
            (
                {
                    "status": "complete",
                    **SOUND_RECORD,
                    "fill_mask": [[True, True], [True, True]],
                },
                "content differs from the recorded counters: text (1, 1) lost",
            ),
            ({"status": "complete"}, "complete without recorded counters"),
            (
                {"status": "complete", "singular_count": 2, "segment_count": 2},
                "complete without recorded counters",
            ),
            (
                {"status": "draft", **SOUND_RECORD, "segment_count": 0},
                "counters ignored (segment_count is not an int >= 1)",
            ),
        ],
        ids=[
            "unknown-status",
            "diverging-complete",
            "complete-without-counters",
            "complete-incomplete-counters",
            "draft-damaged-counters",
        ],
    )
    def test_warns(self, tmp_path, entry_metadata, expected):
        messages = _load_entry(tmp_path, entry_metadata)
        assert len(messages) == 1
        assert messages[0].endswith(f"10001: {expected}")

    @pytest.mark.parametrize(
        "change, expected",
        [
            ({"singular_count": "2"}, "singular_count is not an int >= 1"),
            ({"segment_count": True}, "segment_count is not an int >= 1"),
            ({"fill_mask": "mask"}, "fill_mask is not a list of lists"),
            ({"fill_mask": [[True, True], [True]]}, "fill_mask is not a rectangle"),
            (
                {"fill_mask": [[True, 1], [True, False]]},
                "fill_mask holds a value that is not a boolean",
            ),
            ({"segment_count": 3}, "fill_mask has 2 rows, segment_count is 3"),
            ({"singular_count": 1}, "fill_mask has 2 columns, singular_count is 1"),
        ],
        ids=[
            "count-str",
            "count-bool",
            "mask-str",
            "ragged",
            "non-bool",
            "rows",
            "columns",
        ],
    )
    def test_damaged_counters_of_a_complete_entry_fail(
        self, tmp_path, change, expected
    ):
        data = {
            "10001": {
                "messages": RECORD_MATRIX,
                "metadata": {"status": "complete", **SOUND_RECORD, **change},
            }
        }
        with pytest.raises(
            FormatError, match=re.escape(f"damaged counters: {expected}")
        ):
            load_book(_write_i18t(tmp_path, data))


class TestLoadBookLocations:
    @staticmethod
    def _data(locations: object) -> dict:
        return {
            "10001": {
                "messages": [["Un fichier"]],
                "metadata": {"locations": locations},
            }
        }

    @pytest.mark.parametrize(
        "locations",
        [
            [],
            [["app.py", 12]],
            [["app.py", 12, 1, 0]],
            [["app.py", 12, None, 1], ["cli.py", 3, 2, None]],
            [["app.py", 12, None, None]],
        ],
        ids=["empty", "pair", "full", "open-coordinates", "both-open"],
    )
    def test_accepted_forms(self, tmp_path, locations):
        content = load_book(_write_i18t(tmp_path, self._data(locations)))
        assert content["entries"]["10001"]["metadata"]["locations"] == locations

    @pytest.mark.parametrize(
        "locations",
        [
            [["app.py"]],
            [["app.py", 12, 1]],
            [["app.py", 12, 1, 0, 0]],
            [["", 12]],
            [[12, "app.py"]],
            [["app.py", 0]],
            [["app.py", True]],
            [["app.py", 12, -1, 0]],
            [["app.py", 12, 1, "0"]],
            [["app.py", 12, False, 0]],
            ["app.py:12"],
            "app.py:12",
        ],
        ids=[
            "one-item",
            "three-items",
            "five-items",
            "empty-file",
            "swapped",
            "line-zero",
            "line-bool",
            "variant-negative",
            "segment-str",
            "variant-bool",
            "string-item",
            "not-a-list",
        ],
    )
    def test_rejected_forms(self, tmp_path, locations):
        with pytest.raises(
            FormatError, match=re.escape("[file, line, variant, segment] items")
        ):
            load_book(_write_i18t(tmp_path, self._data(locations)))
