import shutil
from pickle import FALSE

import pytest

import i18n_tools
from i18n_tools.loaders import create_directory, file_exists
from tests.conftest import conf_tests, tmp_full_repository, tmp_repository


@pytest.fixture
def temp_dir(tmp_repository):
    dir_path = tmp_repository[0] / "test_dir"
    dir_path.mkdir()
    yield dir_path
    shutil.rmtree(dir_path)


@pytest.mark.parametrize(
    "target, path, verified",
    [
        ("package", "/locales/_i18n_tools/i18n-tools.json", True),
        ("application", "locales/_i18n_tools/i18n-tools.yaml", True),
        ("package", "locales/_i18n_tools/i18n-tools.false", False),
        ("package", "locales/_i18n_tools/i18n-tools.yaml", True),
        ("package", "locales/_i18n_tools/i18n-tools.toml", True),
        ("application", "locales/i18n-tools.yaml", False),
        ("application", "test.txt", False),
    ],
)
def test_file_exists(target, path, verified, conf_tests, tmp_full_repository):
    temp_file = (
        tmp_full_repository[0] + "/" + conf_tests["repository"][target] + "/" + path
    )
    assert file_exists(temp_file) == verified


def test_create_directory(temp_dir):
    create_directory(temp_dir)
    assert temp_dir.exists()
