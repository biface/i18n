import pytest

from conftest import tmp_repository, conf_tests

from i18n_tools.loaders.handler import (
    build_path,
    file_exists,
    create_directory,
    build_config_repository,
    create_template,
    create_catalog,
    create_dictionary,
    fetch_template,
    fetch_catalog,
    fetch_dictionary,
    update_catalog,
    update_dictionary,
    remove_template,
    remove_catalog,
    remove_dictionary
)
from babel.messages.catalog import Catalog

@pytest.fixture
def build_test_repository(tmp_repository):
    root_repository = tmp_repository[0]
    print("\nvalid:", tmp_repository[5], type(tmp_repository[5]), "\nerror :", tmp_repository[6])
    config_repository = {
        "path": tmp_repository[5]["setup"]["paths"]["application"],
        "languages": tmp_repository[5]["setup"]["languages"],
        "domains": tmp_repository[5]["setup"]["domains"]["application"],
    }

    return config_repository

@pytest.mark.parametrize(
    "base_path, sub_dirs, expected",
    [
        ("fsm_tools", ["locales", "templates"], "fsm_tools/locales/templates"),
        ("fsm_tools", ["locales", "..", "templates"], "fsm_tools/templates"),
    ]
)
def test_build_path(tmp_repository, base_path, sub_dirs, expected):
    base_path = str(tmp_repository[0] / base_path)
    expected_path = tmp_repository[0] / expected
    path = build_path(base_path, *sub_dirs)
    assert path == str(expected_path)

@pytest.mark.parametrize(
    "base_path, sub_dirs",
    [
        ("fsm_tools", ["locales", "..", "invalid"]),
    ]
)
def test_build_path_exception(tmp_repository, base_path, sub_dirs):
    base_path = str(tmp_repository[0] / base_path)
    with pytest.raises(IOError):
        build_path(base_path, *sub_dirs)

@pytest.mark.parametrize(
    "file_path, exists",
    [
        ("config.yaml", True),
        ("config_err.yaml", True),
        ("config.txt", False),
        ("config_err.txt", False),
        ("config_json", False),
    ]
)
def test_file_exists(tmp_repository, file_path, exists):
    test_file = tmp_repository[0] / file_path
    assert file_exists(test_file) == exists

@pytest.mark.parametrize(
    "dir_path",
    [
        ("new_dir"),
        ("nested/new_dir"),
    ]
)
def test_create_directory(tmp_repository, dir_path):
    dir_path = tmp_repository[0] / dir_path
    create_directory(str(dir_path))
    assert dir_path.exists() == True

@pytest.mark.parametrize(
    "module, domain",
    [
        ("fsm_tools", "django"),
        ("fsm_tools", "error"),
    ]
)
def test_create_template(tmp_repository, module, domain):
    create_template(str(tmp_repository[0]), module, domain)
    template_file = tmp_repository[0] / module / "locales/templates" / f"{domain}.pot"
    assert template_file.exists() == True

@pytest.mark.parametrize(
    "module, language, domain",
    [
        ("fsm_tools", "fr-FR", "django"),
        ("fsm_tools", "en-US", "error"),
    ]
)
def test_create_catalog(tmp_repository, module, language, domain):
    create_catalog(str(tmp_repository[0]), module, language, domain)
    catalog_file = tmp_repository[0] / module / f"locales/{language}/{domain}.po"
    assert catalog_file.exists() == True

@pytest.mark.parametrize(
    "module, language, domain",
    [
        ("fsm_tools", "fr-FR", "django"),
        ("fsm_tools", "en-US", "error"),
    ]
)
def test_create_dictionary(tmp_repository, module, language, domain):
    create_dictionary(str(tmp_repository[0]), module, language, domain)
    dictionary_file = tmp_repository[0] / module / f"locales/{language}/{domain}.json"
    assert dictionary_file.exists() == True

@pytest.mark.parametrize(
    "module, domain, content",
    [
        ("fsm_tools", "django", "Template content"),
    ]
)
def test_fetch_template(tmp_repository, module, domain, content):
    template_file = tmp_repository[0] / module / "locales/templates" / f"{domain}.pot"
    template_file.parent.mkdir(parents=True, exist_ok=True)
    template_file.write_text(content)
    fetched_content = fetch_template(str(tmp_repository[0]), module, domain)
    assert fetched_content == content

@pytest.mark.parametrize(
    "module, language, domain",
    [
        ("fsm_tools", "fr-FR", "django"),
    ]
)
def test_fetch_catalog(tmp_repository, module, language, domain):
    catalog_file = tmp_repository[0] / module / f"locales/{language}/{domain}.po"
    catalog_file.parent.mkdir(parents=True, exist_ok=True)
    catalog_file.write_text("msgid \"\"\nmsgstr \"\"\n")
    catalog = fetch_catalog(str(tmp_repository[0]), module, language, domain)
    assert isinstance(catalog, Catalog)

@pytest.mark.parametrize(
    "module, language, domain, content",
    [
        ("fsm_tools", "fr-FR", "django", {"key": "value"}),
    ]
)
def test_fetch_dictionary(tmp_repository, module, language, domain, content):
    dictionary_file = tmp_repository[0] / module / f"locales/{language}/{domain}.json"
    dictionary_file.parent.mkdir(parents=True, exist_ok=True)
    dictionary_file.write_text(str(content))
    fetched_content = fetch_dictionary(str(tmp_repository[0]), module, language, domain)
    assert fetched_content == content

@pytest.mark.parametrize(
    "module, language, domain",
    [
        ("fsm_tools", "fr-FR", "django"),
    ]
)
def test_update_catalog(tmp_repository, module, language, domain):
    catalog_file = tmp_repository[0] / module / f"locales/{language}/{domain}.po"
    catalog_file.parent.mkdir(parents=True, exist_ok=True)
    catalog_file.write_text("msgid \"\"\nmsgstr \"\"\n")
    new_catalog = Catalog()
    new_catalog.add("test_id", locations=[("test.py", 1)])
    update_catalog(str(tmp_repository[0]), module, language, domain, new_catalog)
    updated_catalog = fetch_catalog(str(tmp_repository[0]), module, language, domain)
    assert "test_id" in updated_catalog

@pytest.mark.parametrize(
    "module, language, domain, new_data",
    [
        ("fsm_tools", "fr-FR", "django", {"new_key": "new_value"}),
    ]
)
def test_update_dictionary(tmp_repository, module, language, domain, new_data):
    dictionary_file = tmp_repository[0] / module / f"locales/{language}/{domain}.json"
    dictionary_file.parent.mkdir(parents=True, exist_ok=True)
    dictionary_file.write_text("{}")
    update_dictionary(str(tmp_repository[0]), module, language, domain, new_data)
    updated_data = fetch_dictionary(str(tmp_repository[0]), module, language, domain)
    assert updated_data == new_data

@pytest.mark.parametrize(
    "module, domain",
    [
        ("fsm_tools", "django"),
    ]
)
def test_remove_template(tmp_repository, module, domain):
    create_template(str(tmp_repository[0]), module, domain)
    template_file = tmp_repository[0] / module / "locales/templates" / f"{domain}.pot"
    remove_template(str(tmp_repository[0]), module, domain)
    assert not template_file.exists()

@pytest.mark.parametrize(
    "module, language, domain",
    [
        ("fsm_tools", "fr-FR", "django"),
    ]
)
def test_remove_catalog(tmp_repository, module, language, domain):
    create_catalog(str(tmp_repository[0]), module, language, domain)
    catalog_file = tmp_repository[0] / module / f"locales/{language}/{domain}.po"
    remove_catalog(str(tmp_repository[0]), module, language, domain)
    assert not catalog_file.exists()

@pytest.mark.parametrize(
    "module, language, domain",
    [
        ("fsm_tools", "fr-FR", "django"),
    ]
)
def test_remove_dictionary(tmp_repository, module, language, domain):
    create_dictionary(str(tmp_repository[0]), module, language, domain)
    dictionary_file = tmp_repository[0] / module / f"locales/{language}/{domain}.json"
    remove_dictionary(str(tmp_repository[0]), module, language, domain)
    assert not dictionary_file.exists()
