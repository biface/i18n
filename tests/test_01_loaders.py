import json
import shutil

import pytest
from babel.messages.catalog import Catalog
from babel.messages.pofile import write_po
from polib import POFile

from i18n_tools.loaders import file_exists
from i18n_tools.loaders.loader import (
    _load_mo,
    _load_po,
    _load_pot,
    _save_mo,
    _save_po,
    _save_pot,
    aggregate_locale_json,
    check_json_integrity,
    load_locale_json,
    load_locale_po,
    save_aggregated_locale_json,
    save_locale_json,
    save_locale_po,
    save_locale_pot,
)


@pytest.fixture
def temp_file(tmp_path):
    file_path = tmp_path / "test_file.json"
    yield file_path
    file_path.unlink(missing_ok=True)


@pytest.fixture
def temp_dir(tmp_path):
    dir_path = tmp_path / "test_dir"
    dir_path.mkdir()
    yield dir_path
    shutil.rmtree(dir_path)


@pytest.fixture
def temp_po_file(tmp_path):
    file_path = tmp_path / "test_file.po"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write('msgid ""\nmsgstr ""\n')
    yield file_path
    file_path.unlink(missing_ok=True)


@pytest.fixture
def temp_mo_file(tmp_path):
    file_path = tmp_path / "test_file.mo"
    with open(file_path, "wb") as f:
        f.write(b"\xde\x12\x04\x95")
    yield file_path
    file_path.unlink(missing_ok=True)


def test_load_po_file(temp_po_file):
    po = _load_po(temp_po_file)
    assert isinstance(po, Catalog)


def test_load_po_raises_exception():
    with pytest.raises(FileNotFoundError):
        _load_po("/nonexistent/path")


@pytest.fixture
def setup_valid_po_file(tmp_path):
    """Fixture to set up a temporary valid PO file for testing using Babel."""
    po_file_path = tmp_path / "valid.po"

    # Create a Babel Catalog object
    catalog = Catalog()

    # Add a singular entry
    catalog.add("msgid_001", "Translation 1")

    # Add a plural entry
    catalog.add(
        "msgid_002",
        ("Translation 2", "Plural Translation 2"),
        auto_comments=["Plural form"],
    )

    # Save the catalog to a PO file
    with open(po_file_path, "wb") as po_file:
        write_po(po_file, catalog)

    return po_file_path


def test_load_locale_po_valid(setup_valid_po_file):
    """Test load_locale_po with a valid PO file."""
    po_file_path = setup_valid_po_file
    po_catalog = load_locale_po(str(po_file_path))

    assert len(po_catalog) == 2
    assert po_catalog["msgid_001"].string == "Translation 1"
    assert po_catalog["msgid_002"].string == "Translation 2"


def test_load_locale_po_file_not_found(tmp_path):
    """Test load_locale_po with a non-existent PO file."""
    non_existent_path = tmp_path / "non_existent.po"

    with pytest.raises(FileNotFoundError):
        load_locale_po(str(non_existent_path))


def test_load_pot_file(temp_po_file):
    pot = _load_pot(temp_po_file)
    assert isinstance(pot, Catalog)


def test_load_pot_raises_exception():
    with pytest.raises(FileNotFoundError):
        _load_pot("/nonexistent/path")


def test_load_mo_file(temp_mo_file):
    mo = _load_mo(temp_mo_file)
    assert isinstance(mo, Catalog)


def test_load_mo_raises_exception():
    with pytest.raises(FileNotFoundError):
        _load_mo("/nonexistent/path")


def test_save_po_file(temp_po_file):
    po = Catalog()
    _save_po(temp_po_file, po)
    assert file_exists(temp_po_file) == True


def test_save_locale_po_file(temp_po_file):
    po = Catalog()
    save_locale_po(temp_po_file, po)
    assert file_exists(temp_po_file) == True


def test_save_po_raises_exception():
    po = POFile()
    with pytest.raises(FileNotFoundError):
        _save_po("/nonexistent/path", po)


def test_save_pot_file(temp_po_file):
    pot = Catalog()
    _save_pot(temp_po_file, pot)
    assert file_exists(temp_po_file) == True


def test_save_locale_pot_file(temp_po_file):
    pot = Catalog()
    save_locale_pot(temp_po_file, pot)
    assert file_exists(temp_po_file) == True


def test_save_mo_file(temp_mo_file):
    po_data = Catalog()
    _save_mo(temp_mo_file, po_data)
    assert file_exists(temp_mo_file) == True


def test_save_mo_raises_exception():
    po_data = POFile()
    with pytest.raises(FileNotFoundError):
        _save_mo("/nonexistent/path", po_data)


def test_save_pot_raises_exception():
    pot = POFile()
    with pytest.raises(FileNotFoundError):
        _save_pot("/nonexistent/path", pot)


@pytest.mark.parametrize(
    "data, assertion",
    [
        ({"key1": [["value1"]], "key2": [["value2"], ["value3"]]}, True),
        ({"key1": ["value1"], "key2": [["value2"], "value3"]}, False),
        ({"key1": "value1", "key2": [["value2"], ["value3"]]}, False),
        ({"key1": [], "key2": [["value2"], ["value3"]]}, False),
        (
            {
                "key1": [["value1"], ["value3", "value4"]],
                "key2": [["value2"], ["value3"]],
            },
            False,
        ),
    ],
)
def test_check_json_integrity(data, assertion):
    assert check_json_integrity(data) == assertion


def test_load_locale_json(temp_file):
    data = {
        "msgid_001": [
            ["msgstr_001_000", "msgstr_001_001"],
            ["msgplr_001_1_000", "msgplr_001_1_001"],
        ]
    }
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(data, f)
    assert load_locale_json(temp_file) == data


def test_load_locale_json_raises_exception(temp_file):
    data = {"msgid_001": [["msgstr_001_000"], ["msgplr_001_1_000", "msgplr_001_1_001"]]}
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(data, f)
    with pytest.raises(ValueError):
        load_locale_json(temp_file)


def test_aggregate_locale_json(tmp_path):
    structure = {"base": str(tmp_path), "modules": ["module1"]}
    domains = {"module1": ["domain1"]}
    languages = {"en": ["en-US", "en-GB"], "fr": ["fr-FR", "fr-CA"]}

    module_path = tmp_path / "module1" / "locales"
    module_path.mkdir(parents=True)

    data = {
        "msgid_001": [
            ["msgstr_001_000", "msgstr_001_001"],
            ["msgplr_001_1_000", "msgplr_001_1_001"],
            ["msgplr_001_2_000", "msgplr_001_2_001"],
        ],
        "msgid_002": [["msgstr_002_000"], ["msgplr_002_1_000"], ["msgplr_002_2_000"]],
    }

    for lang in languages:
        for variant in languages[lang]:
            file_path = module_path / variant / "domain1.json"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f)

    aggregated_data = aggregate_locale_json(structure, domains, languages)
    assert "module1" in aggregated_data
    assert "domain1" in aggregated_data["module1"]
    assert all(
        variant in aggregated_data["module1"]["domain1"]
        for lang in languages
        for variant in languages[lang]
    )


def test_save_locale_json(temp_file):
    data = {
        "msgid_001": [
            ["msgstr_001_000", "msgstr_001_001"],
            ["msgplr_001_1_000", "msgplr_001_1_001"],
            ["msgplr_001_2_000", "msgplr_001_2_001"],
        ],
        "msgid_002": [["msgstr_002_000"], ["msgplr_002_1_000"], ["msgplr_002_2_000"]],
    }
    save_locale_json(temp_file, data)
    with open(temp_file, "r", encoding="utf-8") as f:
        loaded_data = json.load(f)
    assert loaded_data == data


def test_save_aggregated_locale_json(tmp_path):
    aggregated_data = {
        "module1": {
            "domain1": {
                "en-US": {
                    "msgid_001": [
                        ["msgstr_001_000", "msgstr_001_001"],
                        ["msgplr_001_1_000", "msgplr_001_1_001"],
                        ["msgplr_001_2_000", "msgplr_001_2_001"],
                    ],
                    "msgid_002": [
                        ["msgstr_002_000"],
                        ["msgplr_002_1_000"],
                        ["msgplr_002_2_000"],
                    ],
                },
                "en-GB": {
                    "msgid_001": [
                        ["msgstr_001_000", "msgstr_001_001"],
                        ["msgplr_001_1_000", "msgplr_001_1_001"],
                        ["msgplr_001_2_000", "msgplr_001_2_001"],
                    ],
                    "msgid_002": [
                        ["msgstr_002_000"],
                        ["msgplr_002_1_000"],
                        ["msgplr_002_2_000"],
                    ],
                },
            }
        }
    }
    save_aggregated_locale_json(aggregated_data, str(tmp_path))
    module_path = tmp_path / "module1"
    assert (module_path / "locales/domain1.json.gz").exists()
    assert (module_path / "module1.json.gz").exists()
