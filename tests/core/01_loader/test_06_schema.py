"""Tests for the JSON Schema of the ``.i18t`` 1.0.0 format.

The schema is read from the installed package. The fixtures of
``tests/mock/format/1.0.0/`` are Book files: those of ``valid/`` are what a
conforming writer produces, each file of ``invalid/`` breaks one rule of the
schema, at the path given by ``INVALID``.
"""

import json
from importlib import resources
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

FIXTURES = Path(__file__).resolve().parents[2] / "mock" / "format" / "1.0.0"
SCHEMA_ID = (
    "https://pyi18t-tools.readthedocs.io/en/stable/schemas/i18t-1.0.0.schema.json"
)

# fixture name (the domain) -> path of the only error the schema reports
INVALID: dict[str, list[str | int]] = {
    "no-metadata": [],
    "no-format-version": ["metadata"],
    "format-version-2": ["metadata", "format_version"],
    "version-prerelease": ["metadata", "version"],
    "reserved-key": [],
    "unknown-root-key": ["metadata"],
    "matrix-entry": ["files.missing", "messages"],
    "no-entry-metadata": ["files.missing"],
    "entry-version": ["files.missing", "metadata"],
    "empty-principal": ["files.missing", "messages", "principal"],
    "location-list": ["files.missing", "metadata", "locations", 0],
    "status-invalid": ["files.missing", "metadata", "status"],
    "fill-mask-matrix": ["files.missing", "metadata", "fill_mask"],
    "duplicate-token": [
        "files.missing",
        "metadata",
        "count",
        "tokens",
        "principal",
        0,
    ],
}


def _schema() -> dict[str, object]:
    path = resources.files("i18n_tools") / "schemas" / "i18t-1.0.0.schema.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _read(path: Path) -> object:
    text = path.read_text(encoding="utf-8")
    if path.name.endswith(".yaml.i18t"):
        return yaml.safe_load(text)
    return json.loads(text)


def _files(kind: str) -> list[Path]:
    return sorted((FIXTURES / kind).glob("*.i18t"))


@pytest.fixture(scope="module")
def validator() -> Draft202012Validator:
    return Draft202012Validator(_schema())


class TestSchemaFile:
    def test_is_a_valid_2020_12_schema(self):
        schema = _schema()
        Draft202012Validator.check_schema(schema)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"

    def test_has_its_published_identifier(self):
        assert _schema()["$id"] == SCHEMA_ID


class TestValidFixtures:
    @pytest.mark.parametrize("path", _files("valid"), ids=lambda p: p.name)
    def test_is_accepted(self, validator, path):
        assert list(validator.iter_errors(_read(path))) == []

    @pytest.mark.parametrize("domain", ["errors", "rules"])
    def test_json_and_yaml_hold_the_same_content(self, domain):
        json_book = _read(FIXTURES / "valid" / f"{domain}.json.i18t")
        yaml_book = _read(FIXTURES / "valid" / f"{domain}.yaml.i18t")
        assert json_book == yaml_book


class TestInvalidFixtures:
    def test_every_file_has_its_expected_error(self):
        assert sorted(p.name.split(".")[0] for p in _files("invalid")) == sorted(
            INVALID
        )

    @pytest.mark.parametrize("name", sorted(INVALID))
    def test_is_refused_at_the_expected_path(self, validator, name):
        errors = list(
            validator.iter_errors(_read(FIXTURES / "invalid" / f"{name}.json.i18t"))
        )
        assert [list(error.absolute_path) for error in errors] == [INVALID[name]]
