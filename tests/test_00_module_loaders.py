import shutil

import pytest

from i18n_tools.loaders import build_path, create_directory, file_exists
from tests.conftest import tmp_repository


@pytest.fixture
def temp_dir(tmp_repository):
    dir_path = tmp_repository[0] / "test_dir"
    dir_path.mkdir()
    yield dir_path
    shutil.rmtree(dir_path)


@pytest.mark.parametrize("path", [False, True])
def test_file_exists(path, tmp_repository):
    temp_file = tmp_repository[0] / "test.txt"
    if not path:
        temp_file = str(temp_file)
    assert file_exists(temp_file) == False
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write("test content")
    assert file_exists(temp_file) == True
    assert file_exists("/nonexistent/path") == False


def test_create_directory(temp_dir):
    create_directory(temp_dir)
    assert temp_dir.exists()


def test_build_path(tmp_repository):
    path = build_path(tmp_repository[0], "module_one", "package_one")
    assert path == str(tmp_repository[0] / "module_one" / "package_one")
