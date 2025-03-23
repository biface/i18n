import pytest

from i18n_tools.loaders.repository import (
    create_module_archive,
    restore_module_from_archive,
)

from .conftest import tmp_repository


def test_create_module_archive(tmp_repository):
    module_path = tmp_repository[0] / "module1"
    module_path.mkdir()
    module_path = module_path / "pkg-1"
    module_path.mkdir()
    archive_name = "module1_archive"
    create_module_archive(str(tmp_repository[0]), str(module_path), archive_name)
    archive_path = tmp_repository[0] / "module1_archive.tar.gz"
    assert archive_path.exists()


def test_restore_module_from_archive(tmp_repository):
    module_path = tmp_repository[0] / "module1"
    module_path.mkdir()
    module_path = module_path / "pkg-1"
    module_path.mkdir()
    archive_name = "module1_archive"
    create_module_archive(str(tmp_repository[0]), str(module_path), archive_name)
    module_path.rmdir()
    restore_module_from_archive(str(tmp_repository[0]), "module1", archive_name)
    assert module_path.exists()


def test_restore_module_raise_exception(tmp_repository):
    module_path = tmp_repository[0] / "module1"
    module_path.mkdir()
    module_path = module_path / "pkg-1"
    module_path.mkdir()
    archive_name = "module1_archive"
    create_module_archive(str(tmp_repository[0]), str(module_path), archive_name)
    module_path.rmdir()
    false_path = tmp_repository[0] / "nonexistent"
    with pytest.raises(FileNotFoundError):
        restore_module_from_archive(
            str(tmp_repository[0]), str(false_path), "nonexistent.tar.gz"
        )
