import shutil

import pytest
from conftest import conf_tests, tmp_function_repository

from i18n_tools.loaders import create_directory, file_exists


@pytest.fixture
def temp_dir(tmp_function_repository):
    dir_path = tmp_function_repository[3][1] / "test_dir"
    dir_path.mkdir()
    yield dir_path
    shutil.rmtree(dir_path)


@pytest.mark.parametrize(
    "target, path, verified",
    [
        ("package", "i18n_tools/locales/_i18n_tools/i18n-tools.json", True),
        ("package", "i18n_tools/locales/_i18n_tools/", True),
        ("application", "fsm_tools/locales/_i18n_tools/i18n-tools.yaml", True),
        ("package", "locales/_i18n_tools/i18n-tools.false", False),
        ("package", "i18n_tools/locales/_i18n_tools/i18n-tools.false", False),
        ("package", "i18n_tools/locales/_i18n_tools/i18n-tools.yaml", True),
        ("package", "i18n_tools/locales/_i18n_tools/i18n-tools.toml", True),
        ("application", "locales/i18n-tools.yaml", False),
        ("application", "test.txt", False),
    ],
)
def test_file_exists(target, path, verified, conf_tests, tmp_function_repository):
    temp_file = (
            tmp_function_repository[0][0]
            + "/"
            + conf_tests["repository"][target]["repository"]
            + "/"
            + path
    )
    assert file_exists(temp_file) == verified


def test_create_directory(temp_dir):
    assert temp_dir.exists()
    with pytest.raises(FileExistsError):
        create_directory(temp_dir)
