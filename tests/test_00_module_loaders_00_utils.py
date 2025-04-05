import gzip
import json
import tarfile
from pathlib import Path

import pytest
import toml
import yaml
from babel.messages.catalog import Catalog
from babel.messages.mofile import write_mo
from babel.messages.pofile import write_po

from i18n_tools.loaders.utils import (
    _exist_path,
    _build_path,
    _convert_catalog,
    _create_empty_file,
    _create_empty_json,
    _create_gzip,
    _create_tar_gz,
    _create_directory,
    _load_json,
    _load_machine,
    _load_text,
    _load_toml,
    _load_yaml,
    _non_traversal_path,
    _save_json,
    _save_machine,
    _save_text,
    _save_toml,
    _save_yaml,
)

from .conftest import tmp_function_repository, tmp_module_repository


@pytest.fixture(scope="function")
def json_test_file(tmp_function_repository):
    json_file = tmp_function_repository[3][1] / "test.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump({"key": "value"}, f)
    return str(json_file)


@pytest.fixture(scope="function")
def yaml_test_file(tmp_function_repository):
    yaml_file = tmp_function_repository[3][1] / "test.yaml"
    with open(yaml_file, "w", encoding="utf-8") as f:
        yaml.safe_dump({"key": "value"}, f)
    return str(yaml_file)


@pytest.fixture(scope="function")
def toml_test_file(tmp_function_repository):
    toml_file = tmp_function_repository[3][1] / "test.toml"
    with open(toml_file, "w", encoding="utf-8") as f:
        toml.dump({"key": "value"}, f)
    return str(toml_file)


@pytest.fixture
def text_test_file(tmp_function_repository):
    file_path = tmp_function_repository[3][1] / "test_file.po"
    catalog = Catalog(
        project="i18n-tools", version="1.0", copyright_holder="Personal dev"
    )
    catalog.header_comment = """\
        # This test file is used as experimental
        # Copyright (C) 2023-20025 Personal Dev. Homework
        # This file is distributed as is under the same license as the projet. 
        """
    with open(file_path, "wb") as f:
        write_po(f, catalog)
    yield str(file_path)


@pytest.fixture
def mo_test_file(tmp_function_repository):
    file_path = tmp_function_repository[3][1] / "test_file.mo"
    catalog = Catalog(project="i18n-tools", version="1.0")
    with open(file_path, "wb") as f:
        write_mo(f, catalog)
    yield str(file_path)


@pytest.mark.parametrize("path, expected", [
    ("locales/backup/test.txt", True),
    ("locales/backup/test.json", False),
])
def test_exist_paths(tmp_function_repository, conf_tests, path, expected):
    temp_file = tmp_function_repository[2][0] + "/" + path
    assert _exist_path(temp_file) == expected

def test_create_empty_file(tmp_function_repository):
    temp_file = tmp_function_repository[3][1] / "empty.txt"
    _create_empty_file(temp_file)
    with open(temp_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert content == ""


def test_create_empty_file_raises_exception():
    with pytest.raises(FileNotFoundError):
        _create_empty_file("/nonexistent/path")


def test_create_empty_json(tmp_function_repository):
    temp_file = tmp_function_repository[3][1] / "another.json"
    _create_empty_json(temp_file)
    with open(temp_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data == {}


def test_create_empty_json_raises_exception():
    with pytest.raises(FileNotFoundError):
        _create_empty_json("/nonexistent/path")


def test_load_json(json_test_file):
    assert _load_json(json_test_file) == {"key": "value"}


def test_load_json_raises_exception():
    with pytest.raises(FileNotFoundError):
        _load_json("/nonexistent/path")


def test_save_json(json_test_file):
    data = {"key": "new value"}
    _save_json(json_test_file, data)
    with open(json_test_file, "r", encoding="utf-8") as f:
        loaded_data = json.load(f)
    assert loaded_data == data


def test_save_json_raises_exception():
    with pytest.raises(FileNotFoundError):
        _save_json("/nonexistent/path", {})


def test_load_toml(toml_test_file):
    assert _load_toml(str(toml_test_file)) == {"key": "value"}


def test_load_toml_raise_exception():
    with pytest.raises(FileNotFoundError):
        _load_toml("nonexistent/path")


def test_save_toml(toml_test_file):
    data = {"key": "new value"}
    _save_toml(toml_test_file, data)
    with open(toml_test_file, "r", encoding="utf-8") as f:
        loaded_data = toml.load(f)
    assert loaded_data == data


def test_save_toml_raises_exception():
    with pytest.raises(FileNotFoundError):
        _save_toml("/nonexistent/path", {})


def test_load_yaml(yaml_test_file):
    assert _load_yaml(str(yaml_test_file)) == {"key": "value"}


def test_load_yaml_raise_exception():
    with pytest.raises(FileNotFoundError):
        _load_yaml("nonexistent/path")


def test_save_yaml(yaml_test_file):
    data = {"key": "new value"}
    _save_yaml(yaml_test_file, data)
    with open(yaml_test_file, "r", encoding="utf-8") as f:
        loaded_data = yaml.safe_load(f)
    assert loaded_data == data


def test_save_yaml_raises_exception():
    with pytest.raises(FileNotFoundError):
        _save_yaml("/nonexistent/path", {})


def test_load_text(text_test_file):
    catalog = _load_text(str(text_test_file))
    assert isinstance(catalog, Catalog)
    assert catalog.project == "i18n-tools"
    assert catalog.version == "1.0"


def test_load_text_raises_exception():
    with pytest.raises(FileNotFoundError):
        _load_text("/nonexistent/path")


def test_save_text(text_test_file):
    catalog = _load_text(str(text_test_file))
    catalog.add("Hello", "Bonjour", locations=[("main.py", 10)])
    _save_text(text_test_file, catalog)
    loaded_catalog = _load_text(str(text_test_file))
    assert loaded_catalog.project == "i18n-tools"
    assert "Hello" in loaded_catalog


def test_save_text_raises_exception():
    po = Catalog()
    with pytest.raises(FileNotFoundError):
        _save_text("/nonexistent/path", po)


def test_load_machine(mo_test_file):
    file_path = mo_test_file

    catalog = _load_machine(file_path)

    assert isinstance(catalog, Catalog)
    assert catalog.project == "i18n-tools"
    assert catalog.version == "1.0"


def test_load_machine_raises_exception():
    with pytest.raises(FileNotFoundError):
        _load_machine("/nonexistent/path")


def test_save_machine(tmp_path):
    # Crée un objet Catalog avec des données fictives
    catalog = Catalog(
        project="i18n-tools", version="1.0", copyright_holder="Personal dev"
    )
    catalog.header_comment = """\
            # This test file is used as experimental
            # Copyright (C) 2023-2025 Personal Dev. Homework
            # This file is distributed as is under the same license as the project.
            """

    # Ajoute un enregistrement au catalogue
    catalog.add("Hello", "Bonjour", locations=[("main.py", 10)])

    # Chemin du fichier temporaire pour sauvegarder le catalogue
    file_path = tmp_path / "test_save.mo"

    # Sauvegarde le catalogue dans le fichier
    _save_machine(str(file_path), catalog)

    # Vérifie que le fichier a été créé
    assert file_path.exists()

    # Charge le fichier pour vérifier son contenu
    loaded_catalog = _load_machine(str(file_path))

    # Vérifie que le catalogue chargé contient l'enregistrement ajouté
    assert "Hello" in loaded_catalog


def test_save_machine_raises_exception():
    po = Catalog()
    with pytest.raises(FileNotFoundError):
        _save_machine("/nonexistent/path", po)


def test_convert_catalog(text_test_file):
    # Utilise la fixture pour obtenir le chemin du fichier .po
    po_file_path = text_test_file
    mo_file_path = po_file_path.replace(".po", ".mo")
    # Convertit le fichier .po en .mo
    _convert_catalog(po_file_path)

    assert Path(mo_file_path).exists()

    # Charge le fichier .mo pour vérifier son contenu
    loaded_catalog = _load_machine(str(mo_file_path))

    # Vérifie que le catalogue chargé correspond au catalogue original
    assert loaded_catalog.project == "i18n-tools"
    assert loaded_catalog.version == "1.0"


def test_convert_catalog_raises_exception():
    with pytest.raises(IOError):
        _convert_catalog("/nonexistent/path")


@pytest.mark.parametrize(
    "module_list, safe_members, unsafe_members",
    [
        (
            ["mod-1"],
            [
                tarfile.TarInfo("mod-1/pkg-1/file1.txt"),
                tarfile.TarInfo("mod-1/pkg-2/file2.txt"),
            ],
            [
                tarfile.TarInfo("../../etc/passwd"),
                tarfile.TarInfo("../secret.txt"),
                tarfile.TarInfo("mod-1/../../etc/shadow"),
            ],
        ),
        (
            [
                "module-1",
                "module-2",
            ],
            [
                tarfile.TarInfo("module-1/locales/fr/apps.json"),
                tarfile.TarInfo("module-1/locales/en/apps.json"),
                tarfile.TarInfo("module-2/utils/locales/fr/errors.json"),
                tarfile.TarInfo("module-2/utils/locales/en/errors.json"),
                tarfile.TarInfo("module-2/locales/fr/usages.json"),
                tarfile.TarInfo("module-2/locales/rn/usages.json"),
            ],
            [
                tarfile.TarInfo("/home/user/../../etc/passwd"),
                tarfile.TarInfo("../secret.txt"),
                tarfile.TarInfo("mod-1/../../etc/shadow"),
                tarfile.TarInfo("module-1/../etc/passwd"),
            ],
        ),
    ],
)
def test_non_traversal_path_exclusion(
        tmp_function_repository, module_list, safe_members, unsafe_members
):
    """Test exclusion of directory traversal vulnerabilities."""
    root_path = tmp_function_repository[3][1]
    all_members = safe_members + unsafe_members

    safe_paths = _non_traversal_path(root_path, module_list, all_members)

    # Check that only safe members are included
    assert len(safe_paths) == len(safe_members)
    for member in safe_members:
        assert member in safe_paths

    # Check that unsafe members are excluded
    for member in unsafe_members:
        assert member not in safe_paths


def test_create_gzip(json_test_file):
    _create_gzip(json_test_file)
    gzip_file_path = Path(json_test_file + ".gz")
    assert gzip_file_path.exists()
    with gzip.open(gzip_file_path, "rt", encoding="utf-8") as f_in:
        content = f_in.read()
    assert "key" in content


@pytest.mark.parametrize("use_path", [True, False])
def test_create_tar_gz(tmp_function_repository, use_path):
    root_dir = tmp_function_repository[3][1]
    directory_to_archive = tmp_function_repository[1][1]

    if not use_path:
        root_dir = str(root_dir)
        directory_to_archive = str(directory_to_archive)

    archive_name = "repository_archive.tar.gz"
    _create_tar_gz(root_dir, archive_name, directory_to_archive)
    assert (root_dir / Path(archive_name)).exists()


@pytest.mark.parametrize(
    "subdir_list, expected",
    [
        (["module_one", "package_one"], "/module_one/package_one"),
        (["module_one", "package_one"], "/module_one/package_one"),
        (["module_one", "..", "package_one"], "/package_one"),
        (["module_one", ".", "package_one"], "/module_one/package_one"),
        (["module_one", "sub_module", "..", "package_one"], "/module_one/package_one"),
        (["module_one", "package_one"], "/module_one/package_one"),
    ],
)
def test_build_path(tmp_function_repository, subdir_list, expected):
    # Convert expected to Path object for comparison
    expected_path = Path(str(tmp_function_repository[3][1]) + expected).resolve()

    # Build the path using the function
    result_path = _build_path(tmp_function_repository[3][1], *subdir_list).resolve()

    # Assert that the result matches the expected path
    assert result_path == expected_path

    result_path = _build_path(str(tmp_function_repository[3][1]), *subdir_list).resolve()

    assert result_path == expected_path

@pytest.mark.parametrize(
    "dir_path, path", [
        ("fsm_tools/lba", False),
        ("fsm_tools/locales/en", True),
        ("fsm_tools/locales/fr", False),
        ("fsm_tools/lba/locales/fr", False)
    ]
)
def test_create_directories(tmp_module_repository, dir_path, path):
    if not path:
        dir_path = tmp_module_repository[2][0] + "/" + dir_path
        _create_directory(dir_path)
        assert Path(dir_path).is_dir()
    else:
        dir_path = tmp_module_repository[2][1] / Path(dir_path)
        _create_directory(dir_path)
        assert dir_path.is_dir()

@pytest.mark.parametrize(
    "dir_path, path", [
        ("fsm_tools", True),
        ("fsm_tools/lba", True),
        ("fsm_tools/locales/en", True),
        ("fsm_tools/locales/fr", True),
        ("fsm_tools/locales/fr-FR", False),
        ("fsm_tools/lba/locales/en-US", False)
    ]
)
def test_create_directories_with_failures(tmp_module_repository, dir_path, path):
    dir_path = tmp_module_repository[2][1] / Path(dir_path)
    if path:
        with pytest.raises(FileExistsError):
            _create_directory(dir_path)
    else:
        _create_directory(dir_path)
        assert dir_path.is_dir()