import pytest
from babel.messages.catalog import Catalog
from conftest import conf_tests, tmp_module_repository, tmp_function_repository, tmp_repository

from i18n_tools.loaders.handler import (
    build_path,
    create_catalog,
    create_dictionary,
    create_directory,
    create_template,
    fetch_catalog,
    fetch_dictionary,
    fetch_template,
    file_exists,
    remove_catalog,
    remove_dictionary,
    remove_template,
    update_catalog,
    update_dictionary,
)
from i18n_tools.loaders.repository import build_config_repository


@pytest.fixture
def build_test_repository(tmp_repository):
    root_repository = tmp_repository[0]
    print(
        "\nvalid:",
        tmp_repository[5],
        type(tmp_repository[5]),
        "\nerror :",
        tmp_repository[6],
    )
    config_repository = {
        "path": tmp_repository[5]["setup"]["paths"]["application"],
        "languages": tmp_repository[5]["setup"]["languages"],
        "domains": tmp_repository[5]["setup"]["domains"]["application"],
    }

    return config_repository


@pytest.mark.parametrize(
    "module, sub_dirs, expected, verified",
    [
        ("package", ["locales", "_i18n_tools"], "locales/_i18n_tools", True),
        (
            "application",
            ["undiscovered", "..", "locales", "templates"],
            "locales/templates",
            True,
        ),
        ("application", ["locales", "..", "templates"], "locales/templates", False),
    ],
)
def test_build_path(
        tmp_function_repository, conf_tests, module, sub_dirs, expected, verified
):
    base_path = tmp_function_repository[0][0] + "/" + conf_tests["repository"][module]
    expected_path = (
            tmp_function_repository[0][0] + "/" + conf_tests["repository"][module] + "/" + expected
    )
    if verified:
        path = build_path(base_path, *sub_dirs)
        assert path == expected_path
    else:
        with pytest.raises(OSError):
            path = build_path(base_path, *sub_dirs)


@pytest.mark.parametrize(
    "base_path, sub_dirs",
    [
        ("fsm_tools", ["locales", "..", "invalid"]),
    ],
)
def test_build_path_exception(tmp_function_repository, base_path, sub_dirs):
    base_path = str(tmp_function_repository[3][1] / base_path)
    with pytest.raises(IOError):
        build_path(base_path, *sub_dirs)

@pytest.mark.parametrize(
    "dir_path",
    [
        "fsm_tools/turing",
        "fsm_tools/lba",
        "django/fsm_tools/extended"
    ],
)
def test_create_directory(tmp_module_repository, dir_path):
    dir_path = tmp_module_repository[2][1] / dir_path
    create_directory(str(dir_path))
    assert dir_path.exists() == True


@pytest.mark.parametrize(
    "module, domain",
    [
        ("fsm_tools", "django"),
        ("fsm_tools", "error"),
    ],
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
    ],
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
    ],
)
def test_create_dictionary(tmp_repository, module, language, domain):
    create_dictionary(str(tmp_repository[0]), module, language, domain)
    dictionary_file = tmp_repository[0] / module / f"locales/{language}/{domain}.json"
    assert dictionary_file.exists() == True


@pytest.mark.parametrize(
    "module, domain, content",
    [
        ("fsm_tools", "django", "Template content"),
    ],
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
    ],
)
def test_fetch_catalog(tmp_repository, module, language, domain):
    catalog_file = tmp_repository[0] / module / f"locales/{language}/{domain}.po"
    catalog_file.parent.mkdir(parents=True, exist_ok=True)
    catalog_file.write_text('msgid ""\nmsgstr ""\n')
    catalog = fetch_catalog(str(tmp_repository[0]), module, language, domain)
    assert isinstance(catalog, Catalog)


@pytest.mark.parametrize(
    "module, language, domain, content",
    [
        ("fsm_tools", "fr-FR", "django", {"key": "value"}),
    ],
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
    ],
)
def test_update_catalog(tmp_repository, module, language, domain):
    catalog_file = tmp_repository[0] / module / f"locales/{language}/{domain}.po"
    catalog_file.parent.mkdir(parents=True, exist_ok=True)
    catalog_file.write_text('msgid ""\nmsgstr ""\n')
    new_catalog = Catalog()
    new_catalog.add("test_id", locations=[("test.py", 1)])
    update_catalog(str(tmp_repository[0]), module, language, domain, new_catalog)
    updated_catalog = fetch_catalog(str(tmp_repository[0]), module, language, domain)
    assert "test_id" in updated_catalog


@pytest.mark.parametrize(
    "module, language, domain, new_data",
    [
        ("fsm_tools", "fr-FR", "django", {"new_key": "new_value"}),
    ],
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
    ],
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
    ],
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
    ],
)
def test_remove_dictionary(tmp_repository, module, language, domain):
    create_dictionary(str(tmp_repository[0]), module, language, domain)
    dictionary_file = tmp_repository[0] / module / f"locales/{language}/{domain}.json"
    remove_dictionary(str(tmp_repository[0]), module, language, domain)
    assert not dictionary_file.exists()
