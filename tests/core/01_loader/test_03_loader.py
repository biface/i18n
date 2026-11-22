"""Tests for loaders/loader.py (biface/i18n#31).

load_book() and inspect_book_file() read a Book file in format 1.0.0
(docs/source/reference/format.rst); the files of the tests are the valid
fixtures of tests/mock/format/1.0.0, changed one point at a time.
load_locale_json(), aggregate_locale_json(), save_locale_json() and
save_aggregated_locale_json() work on locale files."""

import copy
import gzip
import json
import re
import warnings
from pathlib import Path

import pytest
import yaml

from i18n_tools._finding import Finding
from i18n_tools.exceptions import FormatError, I18nToolsWarning
from i18n_tools.loaders import loader as loader_module
from i18n_tools.loaders._handler import book_count
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

FIXTURES = Path(__file__).resolve().parents[2] / "mock" / "format" / "1.0.0"

# Locale files (not Books): a mapping of identifiers to matrices.
VALID_DATA = {
    ".i18n_tools": {"version": "0.1.0"},
    "metadata": {"language": "fr-FR"},
    "10001": [["Un message"], ["Des messages"]],
    "10002": [["Un autre message", "Une variante"]],
}

INVALID_DATA = {
    "10001": "not-a-list",
}


def _book(name="errors"):
    """A copy of a valid fixture: ``errors`` (en-US, two entries) or ``rules``."""
    return json.loads((FIXTURES / "valid" / f"{name}.json.i18t").read_text("utf-8"))


def _recount(data):
    """Set the root count of ``data`` to what its entries give, as read."""
    entries = [
        {
            "status": (
                "complete" if value["metadata"].get("status") == "complete" else "draft"
            ),
            "count": value["metadata"]["count"],
            "fill_mask": value["metadata"]["fill_mask"],
        }
        for key, value in data.items()
        if key != "metadata"
    ]
    data["metadata"]["count"] = book_count(entries)
    return data


def _write_i18t(directory, data, name="errors.json.i18t"):
    file = directory / name
    file.write_text(json.dumps(data), encoding="utf-8")
    return str(file)


def _write_yaml_i18t(directory, data, name="errors.yaml.i18t"):
    file = directory / name
    file.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return str(file)


def _findings(tmp_path, data, language=None, domain=None):
    """``(severity, where, message)`` of every finding of ``data``."""
    path = _write_i18t(tmp_path, data)
    return [
        (f.severity, f.where, f.message)
        for f in inspect_book_file(path, language, domain)
    ]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestLoadBook:
    def test_load_book_detects_yaml_format(self, tmp_path):
        """biface/i18n#67 — a .yaml.i18t file is read as YAML."""
        result = load_book(_write_yaml_i18t(tmp_path, _book()))["entries"]
        assert list(result) == ["files.missing", "disk.alert"]
        assert (
            result["files.missing"]["messages"] == _book()["files.missing"]["messages"]
        )

    def test_reserved_keys_left_out(self, tmp_path):
        data = {**_book(), ".pyi18t_tools": {"a": 1}, ".i18n_tools": [1]}
        result = load_book(_write_i18t(tmp_path, data))["entries"]
        assert list(result) == ["files.missing", "disk.alert"]

    def test_root_metadata_as_read(self, tmp_path):
        """The root metadata is returned without count and statistics."""
        content = load_book(_write_i18t(tmp_path, _book()))
        expected = {
            key: value
            for key, value in _book()["metadata"].items()
            if key not in ("count", "statistics")
        }
        assert content["metadata"] == expected

    def test_absent_values_read_as_the_format_says(self, tmp_path):
        data = _book()
        for key in ("version", "gettext", "rules", "statistics"):
            del data["metadata"][key]
        metadata = load_book(_write_i18t(tmp_path, data))["metadata"]
        assert metadata["version"] == "0.0.1"
        assert set(metadata["gettext"].values()) == {""}
        assert len(metadata["gettext"]) == 7
        assert metadata["rules"] == {}

    def test_gettext_not_checked(self, tmp_path):
        data = _book()
        data["metadata"]["gettext"] = {"pot_creation_date": 2026, "other": "x"}
        gettext = load_book(_write_i18t(tmp_path, data))["metadata"]["gettext"]
        assert gettext["pot_creation_date"] == 2026
        assert gettext["project_id_version"] == ""
        assert "other" not in gettext

    def test_entry_as_read(self, tmp_path):
        """An entry keeps its content and its metadata, statistics apart."""
        entry = load_book(_write_i18t(tmp_path, _book()))["entries"]["files.missing"]
        expected = copy.deepcopy(_book()["files.missing"])
        del expected["metadata"]["statistics"]
        assert entry == expected

    @pytest.mark.parametrize("severity, warned", [("info", False), ("warning", True)])
    def test_load_book_warns_for_warnings_only(
        self, tmp_path, monkeypatch, severity, warned
    ):
        """Information findings are neither raised nor issued as warnings."""
        path = _write_i18t(tmp_path, _book())
        read_book = loader_module.read_book
        monkeypatch.setattr(
            loader_module,
            "read_book",
            lambda data, language=None, domain=None: (
                read_book(data)[0],
                [Finding(severity, "files.missing", "a finding")],
            ),
        )
        with warnings.catch_warnings(record=True) as record:
            warnings.simplefilter("always", I18nToolsWarning)
            content = load_book(path)
        assert list(content["entries"]) == ["files.missing", "disk.alert"]
        issued = [w for w in record if issubclass(w.category, I18nToolsWarning)]
        assert len(issued) == (1 if warned else 0)

    def test_load_book_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_book(str(tmp_path / "no_such_file.json.i18t"))

    def test_errors_listed_in_the_format_error(self, tmp_path):
        data = {**_book(), "broken": "not-a-mapping"}
        del data["metadata"]["format_version"]
        with pytest.raises(FormatError) as exc_info:
            load_book(_write_i18t(tmp_path, data))
        assert str(exc_info.value).splitlines()[1:] == [
            '  - root: ["metadata", "format_version"] is missing',
            "  - broken: entry is not a mapping",
        ]

    def test_file_left_unchanged(self, tmp_path):
        data = _book()
        data["disk.alert"]["metadata"]["flags"] = ["python-format", "python-format"]
        path = _write_i18t(tmp_path, _recount(data))
        before = Path(path).read_bytes()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", I18nToolsWarning)
            content = load_book(path)
        assert content["entries"]["disk.alert"]["metadata"]["flags"] == [
            "python-format"
        ]
        assert Path(path).read_bytes() == before


class TestInspectBookFile:
    """inspect_book_file() — every finding of a file, nothing raised or warned."""

    @pytest.mark.parametrize("name", ["errors", "rules", "messages"])
    def test_sound_file(self, tmp_path, name):
        assert (
            inspect_book_file(_write_i18t(tmp_path, _book(name), f"{name}.json.i18t"))
            == []
        )

    def test_sound_yaml_file(self, tmp_path):
        assert inspect_book_file(_write_yaml_i18t(tmp_path, _book())) == []

    def test_every_severity_returned_nothing_warned(self, tmp_path):
        data = _book()
        data["files.missing"]["metadata"]["status"] = "draft"
        data["files.missing"]["messages"]["principal"][1] = ""
        data["disk.alert"]["metadata"]["flags"] = ["python-format", "python-format"]
        data["broken"] = "not-a-mapping"
        path = _write_i18t(tmp_path, data)
        with warnings.catch_warnings(record=True) as record:
            warnings.simplefilter("always", I18nToolsWarning)
            findings = inspect_book_file(path)
        assert [w for w in record if issubclass(w.category, I18nToolsWarning)] == []
        assert [(f.severity, f.where) for f in findings] == [
            ("info", "files.missing"),
            ("warning", "disk.alert"),
            ("error", "broken"),
        ]

    @pytest.mark.parametrize(
        "language, domain, expected",
        [
            ("fr-FR", None, "[\"metadata\", \"language\"] 'en-US' is not 'fr-FR'"),
            ("en-GB", None, "[\"metadata\", \"language\"] 'en-US' is not 'en-GB'"),
            (None, "other", "[\"metadata\", \"domain\"] 'errors' is not 'other'"),
        ],
        ids=["other-family", "same-family", "domain"],
    )
    def test_language_and_domain_compared(self, tmp_path, language, domain, expected):
        assert _findings(tmp_path, _book(), language, domain) == [
            ("error", "root", expected)
        ]

    def test_language_compared_after_normalisation(self, tmp_path):
        data = _book()
        data["metadata"]["language"] = "en-us"
        assert _findings(tmp_path, data, "en-US", "errors") == []

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
# Reading format 1.0.0: one rule at a time, on the errors fixture
# ---------------------------------------------------------------------------


def _set(path, value):
    """A change of the data: the value at ``path`` (keys from the root)."""

    def change(data):
        node = data
        for key in path[:-1]:
            node = node[key]
        node[path[-1]] = value

    return change


def _drop(path):
    """A change of the data: the key at ``path`` removed."""

    def change(data):
        node = data
        for key in path[:-1]:
            node = node[key]
        del node[path[-1]]

    return change


def _changed(change, recount=False):
    data = _book()
    change(data)
    return _recount(data) if recount else data


FM = "files.missing"
DA = "disk.alert"


class TestReadRoot:
    @pytest.mark.parametrize(
        "change, expected",
        [
            (_drop(["metadata"]), '["metadata"] is missing'),
            (_set(["metadata"], []), '["metadata"] is not a mapping'),
            (
                _drop(["metadata", "format_version"]),
                '["metadata", "format_version"] is missing',
            ),
            (
                _set(["metadata", "format_version"], "1.0"),
                '["metadata", "format_version"] \'1.0\' is not a strict semantic '
                + "version (MAJOR.MINOR.PATCH)",
            ),
            (
                _set(["metadata", "format_version"], 1),
                '["metadata", "format_version"] is not a string',
            ),
            (
                _set(["metadata", "format_version"], "2.1.0"),
                '["metadata", "format_version"] \'2.1.0\': major version 2 is not '
                + "known (known: 1)",
            ),
            (
                _set(["metadata", "version"], "01.0.0"),
                '["metadata", "version"] \'01.0.0\' is not a strict semantic version '
                + "(MAJOR.MINOR.PATCH)",
            ),
            (_drop(["metadata", "language"]), '["metadata", "language"] is missing'),
            (
                _set(["metadata", "language"], "not a tag!"),
                '["metadata", "language"] \'not a tag!\' is not a valid language tag',
            ),
            (_drop(["metadata", "domain"]), '["metadata", "domain"] is missing'),
            (
                _set(["metadata", "rules"], []),
                '["metadata", "rules"] is not a mapping',
            ),
            (
                _set(["metadata", "plural_rule"], {}),
                "unknown key 'plural_rule' in [\"metadata\"]",
            ),
            (
                _set(["metadata", "statistics", "words"], -1),
                '["metadata", "statistics", "words"] is not an integer >= 0',
            ),
            (
                _set(["metadata", "count", "filled"], "6"),
                '["metadata", "count", "filled"] is not an integer >= 0',
            ),
            (_set([""], {}), "an identifier is empty"),
        ],
        ids=[
            "no-metadata",
            "metadata-list",
            "no-format-version",
            "format-version-short",
            "format-version-int",
            "format-version-major",
            "version-leading-zero",
            "no-language",
            "invalid-language",
            "no-domain",
            "rules-list",
            "unknown-key",
            "statistics-type",
            "count-type",
            "empty-identifier",
        ],
    )
    def test_error(self, tmp_path, change, expected):
        assert _findings(tmp_path, _changed(change)) == [("error", "root", expected)]

    def test_invalid_language_without_a_place(self, tmp_path):
        """A language that is not a tag is an error, the place unknown."""
        data = _changed(_set(["metadata", "language"], "xx-!!"))
        assert [f[0] for f in _findings(tmp_path, data)] == ["error"]

    @pytest.mark.parametrize(
        "change, expected",
        [
            (
                _drop(["metadata", "count"]),
                ['["metadata", "count"] is missing: recomputed at the next write'],
            ),
            (
                _set(["metadata", "count", "filled"], 5),
                [
                    '["metadata", "count", "filled"] is 5, the entries give 6: '
                    + "recomputed at the next write"
                ],
            ),
            (
                _drop(["metadata", "count", "empty"]),
                [
                    '["metadata", "count", "empty"] is missing: recomputed at the '
                    + "next write"
                ],
            ),
        ],
        ids=["count-absent", "count-differs", "count-key-absent"],
    )
    def test_book_count_warning(self, tmp_path, change, expected):
        findings = _findings(tmp_path, _changed(change))
        assert findings == [("warning", "root", message) for message in expected]

    @pytest.mark.parametrize(
        "change",
        [
            _drop(["metadata", "statistics"]),
            _set(["metadata", "statistics", "words"], 1),
            _drop(["metadata", "version"]),
            _drop(["metadata", "gettext"]),
            _set(["metadata", "gettext", "header_comment"], ["any", "value"]),
            _set(["metadata", "rules"], {"open": {"content": [1]}}),
        ],
        ids=[
            "statistics-absent",
            "statistics-not-compared",
            "version-absent",
            "gettext-absent",
            "gettext-not-checked",
            "rules-content-open",
        ],
    )
    def test_no_finding(self, tmp_path, change):
        assert _findings(tmp_path, _changed(change)) == []

    def test_book_count_left_aside_when_an_entry_is_not_read(self, tmp_path):
        data = _changed(_set([FM, "messages"], [["a"]]))
        assert [f[:2] for f in _findings(tmp_path, data)] == [("error", FM)]


class TestReadEntry:
    @pytest.mark.parametrize(
        "change, expected",
        [
            (_set([FM], []), "entry is not a mapping"),
            (_drop([FM, "messages"]), '["messages"] is missing'),
            (_drop([FM, "metadata"]), '["metadata"] is missing'),
            (_set([FM, "metadata"], []), '["metadata"] is not a mapping'),
            (_set([FM, "odd"], 1), "unknown key 'odd' in the entry"),
            (
                _set([FM, "messages"], [["a", "b"], ["c", "d"]]),
                '["messages"] is a matrix (format 0.10.0): expected '
                + '{"principal": [...], "alternatives": [...]}',
            ),
            (_set([FM, "messages"], "text"), '["messages"] is not a mapping'),
            (
                _drop([FM, "messages", "principal"]),
                '["messages", "principal"] is missing',
            ),
            (
                _set([FM, "messages", "principal"], []),
                '["messages", "principal"] is empty: it holds at least the singular',
            ),
            (
                _drop([FM, "messages", "alternatives"]),
                '["messages", "alternatives"] is missing',
            ),
            (
                _set([FM, "messages", "alternatives", 0, 1], 0),
                '["messages", "alternatives", 0, 1] is not a string',
            ),
            (
                _set([FM, "messages", "alternatives", 0], ["only the singular"]),
                '["messages", "alternatives", 0] has 1 segments, '
                + '["messages", "principal"] has 2',
            ),
            (
                _set([FM, "messages", "principal", 0], "File {name is missing."),
                "text (0, 0) is not a valid format string: expected '}' before end "
                + "of string",
            ),
            (
                _set([FM, "messages", "alternatives", 0, 0], "File {name!x}."),
                "text (1, 0) is not a valid format string: unknown conversion '!x' "
                + "in the field 'name'",
            ),
            (_drop([FM, "metadata", "id"]), '["metadata", "id"] is missing'),
            (
                _set([FM, "metadata", "id"], "file.missing"),
                '["metadata", "id"] \'file.missing\' is not the key of the entry',
            ),
            (
                _set([FM, "metadata", "id"], ""),
                '["metadata", "id"] is not a non-empty string',
            ),
            (
                _set([FM, "metadata", "version"], "0.10.0"),
                "unknown key 'version' in [\"metadata\"]",
            ),
            (
                _set([FM, "metadata", "flags"], [""]),
                '["metadata", "flags", 0] is empty',
            ),
            (
                _set([FM, "metadata", "flags"], "python-format"),
                '["metadata", "flags"] is not a list',
            ),
            (
                _set([FM, "metadata", "user_comments"], [1]),
                '["metadata", "user_comments"] is not a list of strings',
            ),
            (
                _set([FM, "metadata", "context"], None),
                '["metadata", "context"] is not a string',
            ),
            (
                _set([FM, "metadata", "rules"], []),
                '["metadata", "rules"] is not a mapping',
            ),
            (
                _set([FM, "metadata", "statistics"], {"words": 14}),
                None,
            ),
            (
                _set([FM, "metadata", "statistics", "lines"], 1),
                'unknown key \'lines\' in ["metadata", "statistics"]',
            ),
        ],
        ids=[
            "entry-list",
            "no-messages",
            "no-metadata",
            "metadata-list",
            "unknown-entry-key",
            "matrix",
            "messages-str",
            "no-principal",
            "empty-principal",
            "no-alternatives",
            "text-not-str",
            "rule-1",
            "malformed-braces",
            "unknown-conversion",
            "no-id",
            "id-not-key",
            "id-empty",
            "unknown-metadata-key",
            "empty-flag",
            "flags-str",
            "comments-not-str",
            "context-none",
            "rules-list",
            "statistics-key-absent-not-checked",
            "unknown-statistics-key",
        ],
    )
    def test_error(self, tmp_path, change, expected):
        findings = _findings(tmp_path, _changed(change))
        assert findings == ([] if expected is None else [("error", FM, expected)])

    @pytest.mark.parametrize(
        "key",
        [
            "context",
            "locations",
            "flags",
            "user_comments",
            "auto_comments",
            "statistics",
        ],
    )
    def test_absent_key_error_in_a_complete_message(self, tmp_path, key):
        assert _findings(tmp_path, _changed(_drop([FM, "metadata", key]))) == [
            ("error", FM, f'["metadata", "{key}"] is missing')
        ]

    @pytest.mark.parametrize(
        "key",
        [
            "context",
            "locations",
            "flags",
            "user_comments",
            "auto_comments",
            "statistics",
        ],
    )
    def test_absent_key_warning_in_a_draft(self, tmp_path, key):
        assert _findings(tmp_path, _changed(_drop([DA, "metadata", key]))) == [
            ("warning", DA, f'["metadata", "{key}"] is missing')
        ]

    @pytest.mark.parametrize("key", ["rules", "status"])
    def test_absent_key_without_finding(self, tmp_path, key):
        data = _changed(_drop([DA, "metadata", key]), recount=True)
        assert _findings(tmp_path, data) == []

    def test_absent_values_read(self, tmp_path):
        data = _book()
        for key in (
            "context",
            "locations",
            "flags",
            "user_comments",
            "rules",
            "status",
        ):
            del data[DA]["metadata"][key]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", I18nToolsWarning)
            metadata = load_book(_write_i18t(tmp_path, data))["entries"][DA]["metadata"]
        assert {
            key: metadata[key]
            for key in (
                "context",
                "locations",
                "flags",
                "user_comments",
                "rules",
                "status",
            )
        } == {
            "context": "",
            "locations": [],
            "flags": [],
            "user_comments": [],
            "rules": {},
            "status": "draft",
        }

    def test_repeated_flag_warning_and_removed(self, tmp_path):
        data = _changed(_set([DA, "metadata", "flags"], ["a", "b", "a"]), recount=True)
        assert _findings(tmp_path, data) == [
            (
                "warning",
                DA,
                '["metadata", "flags"]: \'a\' is repeated: the repetition is removed',
            )
        ]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", I18nToolsWarning)
            entry = load_book(_write_i18t(tmp_path, data))["entries"][DA]
        assert entry["metadata"]["flags"] == ["a", "b"]

    @pytest.mark.parametrize(
        "text, field", [("{} files", ""), ("{0} files", "0"), ("{0.name}", "0.name")]
    )
    def test_positional_token_warning(self, tmp_path, text, field):
        data = _changed(_set([DA, "messages", "principal", 0], text))
        data[DA]["metadata"]["count"]["tokens"]["principal"][0] = []
        assert _findings(tmp_path, data) == [
            (
                "warning",
                DA,
                f"text (0, 0) has a positional token '{{{field}}}': tokens are passed "
                + "by name",
            )
        ]

    @pytest.mark.parametrize(
        "text, tokens, message",
        [
            (
                "{user.name} files",
                ["user.name"],
                "has a token with attribute or index access '{user.name}': a token "
                + "is a plain name",
            ),
            (
                "{items[0]} files",
                ["items[0]"],
                "has a token with attribute or index access '{items[0]}': a token "
                + "is a plain name",
            ),
            (
                "{n:{w}} files",
                ["n", "w"],
                "has a field nested in a format specification '{w}': a token is "
                + "not nested",
            ),
        ],
        ids=["attribute", "index", "nested"],
    )
    def test_token_form_warning(self, tmp_path, text, tokens, message):
        data = _changed(_set([DA, "messages", "principal", 0], text))
        data[DA]["metadata"]["count"]["tokens"]["principal"][0] = tokens
        assert _findings(tmp_path, data) == [("warning", DA, f"text (0, 0) {message}")]

    def test_plain_tokens_give_no_warning(self, tmp_path):
        data = _changed(_set([DA, "messages", "principal", 0], "{n:d} {n!r:>4}"))
        data[DA]["metadata"]["count"]["tokens"]["principal"][0] = ["n"]
        assert _findings(tmp_path, data) == []

    def test_invalid_status_read_as_draft(self, tmp_path):
        data = _changed(_set([FM, "metadata", "status"], "final"))
        assert _findings(tmp_path, data)[0] == (
            "warning",
            FM,
            "[\"metadata\", \"status\"] 'final' is not 'draft' or 'complete': read as draft",
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", I18nToolsWarning)
            entry = load_book(_write_i18t(tmp_path, data))["entries"][FM]
        assert entry["metadata"]["status"] == "draft"


class TestReadRecord:
    """count and fill_mask of an entry: well formed, divergence, broken message."""

    @pytest.mark.parametrize(
        "change",
        [
            lambda data: None,
            _drop([DA, "metadata", "count"]),
            _drop([DA, "metadata", "fill_mask"]),
        ],
        ids=["sound", "draft-no-count", "draft-no-fill-mask"],
    )
    def test_no_finding(self, tmp_path, change):
        assert _findings(tmp_path, _changed(change)) == []

    def test_divergence_of_a_draft_is_information(self, tmp_path):
        data = _changed(_set([DA, "messages", "principal", 1], " "))
        assert _findings(tmp_path, data) == [
            (
                "info",
                DA,
                "the content differs from the record (completeness not validated): "
                + "text (0, 1) lost; tokens of text (0, 1): recorded [percent], "
                + "observed []",
            )
        ]

    @pytest.mark.parametrize(
        "change, defects",
        [
            (
                _set([FM, "messages", "alternatives", 0, 1], "{n} files are missing."),
                "the content differs from the record: text (1, 1) added; tokens of "
                + "text (1, 1): recorded [], observed [n]",
            ),
            (
                _set([FM, "messages", "principal", 0], "File {path} is missing."),
                "the content differs from the record: tokens of text (0, 0): "
                + "recorded [name], observed [path]",
            ),
            (
                _drop([FM, "metadata", "count"]),
                'no record (["metadata", "count"] missing)',
            ),
            (
                lambda data: [
                    data[FM]["metadata"].pop(key) for key in ("count", "fill_mask")
                ],
                'no record (["metadata", "count"] and ["metadata", "fill_mask"] missing)',
            ),
        ],
        ids=["text-added", "token-changed", "no-count", "no-record"],
    )
    def test_broken_message_in_a_complete_book(self, tmp_path, change, defects):
        data = _changed(change)
        data[DA]["metadata"]["status"] = "complete"
        data[DA]["metadata"]["count"] = _book()[DA]["metadata"]["count"]
        data = _recount(data) if "count" in data[FM]["metadata"] else data
        findings = [f for f in _findings(tmp_path, data) if f[1] != "root"]
        assert findings == [
            (
                "warning",
                FM,
                f"complete message broken ({defects}): read as draft, and its Book "
                + "with it",
            )
        ]

    def test_broken_message_in_a_draft_book_is_information(self, tmp_path):
        data = _changed(_set([FM, "messages", "principal", 1], ""))
        assert _findings(tmp_path, data) == [
            (
                "info",
                FM,
                "complete message broken (the content differs from the record: "
                + "text (0, 1) lost; tokens of text (0, 1): recorded [n], observed []): "
                + "read as draft",
            )
        ]

    def test_principal_singular_not_filled_breaks_a_complete_message(self, tmp_path):
        data = _changed(_set([FM, "messages", "principal", 0], "  "))
        assert _findings(tmp_path, data)[0] == (
            "info",
            FM,
            "complete message broken (the content differs from the record: text "
            + "(0, 0) lost; tokens of text (0, 0): recorded [name], observed []; "
            + "principal singular not filled): read as draft",
        )

    def test_broken_message_read_as_draft_with_its_record(self, tmp_path):
        data = _changed(_set([FM, "messages", "principal", 1], ""))
        entry = load_book(_write_i18t(tmp_path, data))["entries"][FM]
        assert entry["metadata"]["status"] == "draft"
        assert entry["metadata"]["count"] == _book()[FM]["metadata"]["count"]
        assert entry["metadata"]["fill_mask"] == _book()[FM]["metadata"]["fill_mask"]

    @pytest.mark.parametrize(
        "path, value, defect",
        [
            (
                ["count", "declensions"],
                0,
                '["metadata", "count", "declensions"] is not an integer >= 1',
            ),
            (
                ["count", "declensions"],
                "1",
                '["metadata", "count", "declensions"] is not an integer >= 1',
            ),
            (
                ["count", "singulars"],
                2,
                '["metadata", "count", "singulars"] is 2, ["metadata", "count", '
                + '"declensions"] is 1, 1 + ["metadata", "count", "alternatives"] is 1',
            ),
            (
                ["count", "plurals"],
                1,
                '["metadata", "count", "plurals"] is 1, ["metadata", "count", '
                + '"segments"] give 2',
            ),
            (
                ["count", "tokens", "principal", 0],
                ["percent", "percent"],
                '["metadata", "count", "tokens", "principal", 0] is not a sorted list '
                + "of distinct names",
            ),
            (
                ["fill_mask"],
                [[True], [True]],
                '["metadata", "fill_mask"] is not a mapping',
            ),
            (
                ["fill_mask", "principal"],
                [True],
                '["metadata", "fill_mask"] does not have the shape given by '
                + '["metadata", "count", "segments"]',
            ),
            (
                ["count", "segments", "extra"],
                1,
                'unknown key \'extra\' in ["metadata", "count", "segments"]',
            ),
        ],
        ids=[
            "zero",
            "str",
            "singulars",
            "plurals",
            "repeated-token",
            "matrix-mask",
            "mask-shape",
            "unknown-key",
        ],
    )
    def test_record_not_well_formed(self, tmp_path, path, value, defect):
        draft = _changed(_set([DA, "metadata", *path], value))
        assert _findings(tmp_path, draft) == [
            ("warning", DA, f"record ignored, not well formed: {defect}")
        ]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", I18nToolsWarning)
            entry = load_book(_write_i18t(tmp_path, draft))["entries"][DA]
        assert "count" not in entry["metadata"] and "fill_mask" not in entry["metadata"]
        complete = _changed(_set([DA, "metadata", *path], value))
        complete[DA]["metadata"]["status"] = "complete"
        assert ("error", DA, f"record not well formed: {defect}") in _findings(
            tmp_path, complete
        )


class TestReadLocations:
    @staticmethod
    def _locations(locations):
        return _changed(_set([DA, "metadata", "locations"], locations), recount=True)

    @pytest.mark.parametrize(
        "locations",
        [
            [],
            [{"file": "app.py", "line": 12, "declension": None, "segment": None}],
            [{"file": "app.py", "line": 12, "declension": 0, "segment": 1}],
        ],
        ids=["empty", "open", "fixed"],
    )
    def test_accepted(self, tmp_path, locations):
        content = load_book(_write_i18t(tmp_path, self._locations(locations)))
        assert content["entries"][DA]["metadata"]["locations"] == locations

    @pytest.mark.parametrize(
        "item",
        [
            ["app.py", 12],
            {"file": "app.py", "line": 12},
            {"file": "app.py", "line": 12, "declension": None, "segment": None, "x": 1},
            {"file": "", "line": 12, "declension": None, "segment": None},
            {"file": "app.py", "line": 0, "declension": None, "segment": None},
            {"file": "app.py", "line": True, "declension": None, "segment": None},
            {"file": "app.py", "line": 1, "declension": -1, "segment": None},
            {"file": "app.py", "line": 1, "declension": None, "segment": "0"},
            {"file": "app.py", "line": 1, "declension": False, "segment": None},
            "app.py:12",
        ],
        ids=[
            "list-form",
            "missing-keys",
            "extra-key",
            "empty-file",
            "line-zero",
            "line-bool",
            "negative",
            "segment-str",
            "declension-bool",
            "string-item",
        ],
    )
    def test_refused(self, tmp_path, item):
        assert _findings(tmp_path, self._locations([item])) == [
            (
                "error",
                DA,
                '["metadata", "locations", 0] is not a location '
                + '{"file", "line", "declension", "segment"}',
            )
        ]

    def test_not_a_list(self, tmp_path):
        assert _findings(tmp_path, self._locations("app.py:12")) == [
            ("error", DA, '["metadata", "locations"] is not a list')
        ]

    @pytest.mark.parametrize(
        "declension, segment, expected",
        [
            (
                1,
                None,
                '["metadata", "locations", 0]: declension 1 is beyond the content '
                + "(0..0): to be corrected",
            ),
            (
                None,
                3,
                '["metadata", "locations", 0]: segment 3 is beyond the content '
                + "(0..2): to be corrected",
            ),
        ],
        ids=["declension", "segment"],
    )
    def test_beyond_the_content_kept(self, tmp_path, declension, segment, expected):
        location = {
            "file": "a.py",
            "line": 1,
            "declension": declension,
            "segment": segment,
        }
        data = self._locations([location])
        assert _findings(tmp_path, data) == [("warning", DA, expected)]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", I18nToolsWarning)
            entry = load_book(_write_i18t(tmp_path, data))["entries"][DA]
        assert entry["metadata"]["locations"] == [location]


class TestInvalidFixtures:
    """Each invalid fixture of the schema, read by the reader."""

    EXPECTED = {
        "no-metadata": ("error", "root", '["metadata"] is missing'),
        "no-format-version": (
            "error",
            "root",
            '["metadata", "format_version"] is missing',
        ),
        "format-version-2": (
            "error",
            "root",
            '["metadata", "format_version"] \'2.0.0\': major version 2 is not known '
            + "(known: 1)",
        ),
        "version-prerelease": (
            "error",
            "root",
            '["metadata", "version"] \'0.0.1-rc.1\' is not a strict semantic version '
            + "(MAJOR.MINOR.PATCH)",
        ),
        "reserved-key": None,
        "former-reserved-key": None,
        "empty-identifier": ("error", "root", "an identifier is empty"),
        "empty-flag": ("error", FM, '["metadata", "flags", 0] is empty'),
        "duplicate-flag": (
            "warning",
            FM,
            '["metadata", "flags"]: \'python-format\' is repeated: the repetition is '
            + "removed",
        ),
        "empty-flag-name": (
            "error",
            "root",
            '["metadata", "statistics", "flags"] is not a mapping of flags to '
            + "integers >= 0",
        ),
        "unknown-root-key": (
            "error",
            "root",
            "unknown key 'plural_rule' in [\"metadata\"]",
        ),
        "matrix-entry": (
            "error",
            FM,
            '["messages"] is a matrix (format 0.10.0): expected '
            + '{"principal": [...], "alternatives": [...]}',
        ),
        "no-entry-metadata": ("error", FM, '["metadata"] is missing'),
        "no-entry-id": ("error", FM, '["metadata", "id"] is missing'),
        "entry-version": ("error", FM, "unknown key 'version' in [\"metadata\"]"),
        "empty-principal": (
            "error",
            FM,
            '["messages", "principal"] is empty: it holds at least the singular',
        ),
        "location-list": (
            "error",
            FM,
            '["metadata", "locations", 0] is not a location '
            + '{"file", "line", "declension", "segment"}',
        ),
        "status-invalid": (
            "warning",
            FM,
            "[\"metadata\", \"status\"] 'fuzzy' is not 'draft' or 'complete': read "
            + "as draft",
        ),
        "fill-mask-matrix": (
            "error",
            FM,
            'record not well formed: ["metadata", "fill_mask"] is not a mapping',
        ),
        "duplicate-token": (
            "error",
            FM,
            'record not well formed: ["metadata", "count", "tokens", "principal", 0] '
            + "is not a sorted list of distinct names",
        ),
    }

    def test_every_fixture_listed(self):
        names = sorted(
            p.name.split(".")[0] for p in (FIXTURES / "invalid").glob("*.i18t")
        )
        assert names == sorted(self.EXPECTED)

    @pytest.mark.parametrize("name", sorted(EXPECTED))
    def test_first_finding(self, name):
        path = FIXTURES / "invalid" / f"{name}.json.i18t"
        findings = [
            (f.severity, f.where, f.message) for f in inspect_book_file(str(path))
        ]
        expected = self.EXPECTED[name]
        assert (findings[:1] if findings else [None]) == [expected]
