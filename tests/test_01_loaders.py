import pytest
import json
import os
import tarfile
import gzip
import shutil
from pathlib import Path
from polib import pofile, mofile
from i18n_tools.loader import (
    file_exists, create_directory,
    _load_json, _save_json, _create_empty_json,
    _load_po, _save_po, _load_pot, _save_pot, _load_mo, _save_mo,
    _create_empty_file, _create_tar_gz, _create_gzip,
    check_json_integrity, load_locale_json, save_locale_json,
    aggregate_locale_json, save_aggregated_locale_json,
    create_module_archive, restore_module_from_archive
)


@pytest.fixture
def temp_file(tmp_path):
    file_path = tmp_path / 'test_file.json'
    yield file_path
    file_path.unlink(missing_ok=True)


@pytest.fixture
def temp_dir(tmp_path):
    dir_path = tmp_path / 'test_dir'
    dir_path.mkdir()
    yield dir_path
    shutil.rmtree(dir_path)


@pytest.fixture
def temp_po_file(tmp_path):
    file_path = tmp_path / 'test_file.po'
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("msgid \"\"\nmsgstr \"\"\n")
    yield file_path
    file_path.unlink(missing_ok=True)


@pytest.fixture
def temp_mo_file(tmp_path):
    file_path = tmp_path / 'test_file.mo'
    with open(file_path, 'wb') as f:
        f.write(b"\xde\x12\x04\x95")
    yield file_path
    file_path.unlink(missing_ok=True)


def test_file_exists(temp_file):
    assert file_exists(temp_file) == False
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write("test content")
    assert file_exists(temp_file) == True
    assert file_exists("/nonexistent/path") == False


def test_create_directory(temp_dir):
    create_directory(temp_dir)
    assert temp_dir.exists()


def test_load_json(temp_file):
    data = {"key": "value"}
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(data, f)
    assert _load_json(temp_file) == data

def test_load_json_raises_exception():
    with pytest.raises(FileNotFoundError):
        _load_json("/nonexistent/path")


def test_save_json(temp_file):
    data = {"key": "value"}
    _save_json(temp_file, data)
    with open(temp_file, 'r', encoding='utf-8') as f:
        loaded_data = json.load(f)
    assert loaded_data == data

def test_save_json_raises_exception():
    with pytest.raises(FileNotFoundError):
        _save_json("/nonexistent/path", {})

def test_create_empty_json(temp_file):
    _create_empty_json(temp_file)
    with open(temp_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert data == {}

def test_create_empty_json_raises_exception():
    with pytest.raises(FileNotFoundError):
        _create_empty_json("/nonexistent/path")

def test_create_empty_file(temp_file):
    _create_empty_file(temp_file)
    with open(temp_file, 'r', encoding='utf-8') as f:
        content = f.read()
    assert content == ""

def test_create_empty_file_raises_exception():
    with pytest.raises(FileNotFoundError):
        _create_empty_file("/nonexistent/path")

def test_create_tar_gz(tmp_path):
    dir_path = tmp_path / "test_dir"
    dir_path.mkdir()
    archive = "test_archive.tar.gz"
    archive_path = tmp_path / archive
    _create_tar_gz(tmp_path, archive, dir_path)
    assert archive_path.exists()


def test_create_gzip(temp_file):
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write("test content")
    _create_gzip(temp_file)
    gz_file = Path(str(temp_file) + ".gz")
    assert gz_file.exists()
    with gzip.open(gz_file, 'rt', encoding='utf-8') as f:
        content = f.read()
    assert content == "test content"

@pytest.mark.parametrize("data, assertion", [
    ({
        "key1": [["value1"]],
        "key2": [["value2"], ["value3"]]
    }, True),
    ({
        "key1": ["value1"],
        "key2": [["value2"], "value3"]
    }, False),
    ({
        "key1": "value1",
        "key2": [["value2"], ["value3"]]
    }, False),
    ({
        "key1": [],
        "key2": [["value2"], ["value3"]]
    }, False),
    ({
        "key1": [["value1"], ["value3", "value4"]],
        "key2": [["value2"], ["value3"]]
    }, False)
])
def test_check_json_integrity(data, assertion):
    assert check_json_integrity(data) == assertion


def test_load_locale_json(temp_file):
    data = {
        "msgid_001": [
            ["msgstr_001_000", "msgstr_001_001"],
            ["msgplr_001_1_000", "msgplr_001_1_001"]
        ]
    }
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(data, f)
    assert load_locale_json(temp_file) == data

def test_load_locale_json_raises_exception(temp_file):
    data = {
        "msgid_001": [
            ["msgstr_001_000"],
            ["msgplr_001_1_000", "msgplr_001_1_001"]
        ]
    }
    with open(temp_file, 'w', encoding='utf-8') as f:
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
            ["msgplr_001_2_000", "msgplr_001_2_001"]
        ],
        "msgid_002": [
            ["msgstr_002_000"],
            ["msgplr_002_1_000"],
            ["msgplr_002_2_000"]
        ]
    }

    for lang in languages:
        for variant in languages[lang]:
            file_path = module_path / variant / "domain1.json"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f)

    aggregated_data = aggregate_locale_json(structure, domains, languages)
    assert "module1" in aggregated_data
    assert "domain1" in aggregated_data["module1"]
    assert all(variant in aggregated_data["module1"]["domain1"] for lang in languages for variant in languages[lang])


def test_save_locale_json(temp_file):
    data = {
        "msgid_001": [
            ["msgstr_001_000", "msgstr_001_001"],
            ["msgplr_001_1_000", "msgplr_001_1_001"],
            ["msgplr_001_2_000", "msgplr_001_2_001"]
        ],
        "msgid_002": [
            ["msgstr_002_000"],
            ["msgplr_002_1_000"],
            ["msgplr_002_2_000"]
        ]
    }
    save_locale_json(temp_file, data)
    with open(temp_file, 'r', encoding='utf-8') as f:
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
                        ["msgplr_001_2_000", "msgplr_001_2_001"]
                    ],
                    "msgid_002": [
                        ["msgstr_002_000"],
                        ["msgplr_002_1_000"],
                        ["msgplr_002_2_000"]
                    ]
                },
                "en-GB": {
                    "msgid_001": [
                        ["msgstr_001_000", "msgstr_001_001"],
                        ["msgplr_001_1_000", "msgplr_001_1_001"],
                        ["msgplr_001_2_000", "msgplr_001_2_001"]
                    ],
                    "msgid_002": [
                        ["msgstr_002_000"],
                        ["msgplr_002_1_000"],
                        ["msgplr_002_2_000"]
                    ]
                }
            }
        }
    }
    save_aggregated_locale_json(aggregated_data, str(tmp_path))
    module_path = tmp_path / "module1"
    assert (module_path / "locales/domain1.json.gz").exists()
    assert (module_path / "module1.json.gz").exists()

def test_create_module_archive(tmp_path):
    module_path = tmp_path / "module1"
    module_path.mkdir()
    module_path = module_path / "pkg-1"
    module_path.mkdir()
    archive_name = "module1_archive"
    create_module_archive(str(tmp_path), str(module_path), archive_name)
    archive_path = tmp_path / "module1_archive.tar.gz"
    assert archive_path.exists()

def test_restore_module_from_archive(tmp_path):
    module_path = tmp_path / "module1"
    module_path.mkdir()
    module_path = module_path / "pkg-1"
    module_path.mkdir()
    archive_name = "module1_archive"
    create_module_archive(str(tmp_path), str(module_path), archive_name)
    module_path.rmdir()
    restore_module_from_archive(str(tmp_path), str(module_path), archive_name)
    assert module_path.exists()

def test_restore_moudle_raise_exception(tmp_path):
    module_path = tmp_path / "module1"
    module_path.mkdir()
    module_path = module_path / "pkg-1"
    module_path.mkdir()
    archive_name = "module1_archive"
    create_module_archive(str(tmp_path), str(module_path), archive_name)
    module_path.rmdir()
    false_path = tmp_path / "nonexistent"
    with pytest.raises(FileNotFoundError):
        restore_module_from_archive(str(tmp_path), str(false_path), "nonexistent.tar.gz")