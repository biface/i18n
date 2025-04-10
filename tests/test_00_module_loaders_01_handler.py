import pytest
from babel.core import Locale
from babel.messages.catalog import Catalog, Message
from conftest import (
    conf_tests,
    tmp_function_repository,
    tmp_module_repository,
    tmp_repository,
)

from i18n_tools.loaders.handler import (
    build_path,
    create_catalog,
    create_dictionary,
    create_directory,
    create_template,
    fetch_catalog,
    fetch_dictionary,
    fetch_template,
    remove_catalog,
    remove_dictionary,
    remove_template,
    update_catalog,
    update_dictionary,
)

from i18n_tools.config import Config


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
        ("package", ["i18n_tools", "locales", "_i18n_tools"], "i18n_tools/locales/_i18n_tools", True),
        (
                "application",
                ["fsm_tools", "undiscovered", "..", "locales", "templates"],
                "fsm_tools/locales/templates",
                True,
        ),
        ("application", ["locales", "..", "templates"], "locales/templates", False),
    ],
)
def test_build_path(
        tmp_function_repository, conf_tests, module, sub_dirs, expected, verified
):
    base_path = tmp_function_repository[0][0] + "/" + conf_tests["repository"][module]["repository"]
    expected_path = (
            tmp_function_repository[0][0]
            + "/"
            + conf_tests["repository"][module]["repository"]
            + "/"
            + expected
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
    ["fsm_tools/turing/locales/templates",
     "fsm_tools/locales/en-US/LC_MESSAGES",
     "fsm_tools/locales/en-GB/LC_MESSAGES",
     "fsm_tools/locales/fr/LC_MESSAGES",
     "fsm_tools/locales/fr-FR/LC_MESSAGES",
     "fsm_tools/lba",
     "django/fsm_tools/extended",
     "fsm_tools/turing/locales/en-US/LC_MESSAGES",
     "fsm_tools/turing/locales/en-GB/LC_MESSAGES",
     "fsm_tools/turing/locales/fr/LC_MESSAGES",
     "fsm_tools/turing/locales/fr-FR/LC_MESSAGES",
     ],
)
def test_create_directory(tmp_module_repository, dir_path):
    dir_path = tmp_module_repository[2][1] / dir_path
    create_directory(str(dir_path))
    assert dir_path.exists() == True


@pytest.mark.parametrize(
    "module, domain, valid",
    [
        ("fsm_tools", "model", True),
        ("fsm_tools", "error", False),
        ("fsm_tools/turing", "information", True),
        ("fsm_tools/turing", "error", True),
        ("fsm_tools/turing", "model", False),
        ("fsm-tools/turing", "error", False),
    ],
)
def test_create_template(tmp_module_repository, module, domain, valid):
    if valid:
        create_template(tmp_module_repository[4].get_repository(), module, domain)
        template_file = tmp_module_repository[2][1] / module / "locales/templates" / f"{domain}.pot"
        assert template_file.exists() == True
    else:
        with pytest.raises(Exception):
            create_template(tmp_module_repository[4].get_repository(), module, domain)


@pytest.mark.parametrize(
    "module, language, domain, valid",
    [
        ("fsm_tools", "en", "usage", False),
        ("fsm_tools", "fr", "usage", True),
        ("fsm_tools", "en-US", "usage", True),
        ("fsm_tools", "en-GB", "usage", True),
        ("fsm_tools", "en-US", "usage", False),
        ("fsm_tools", "fr-FR", "usage", True),
        ("fsm_tools/turing", "fr", "error", True),
        ("fsm_tools/turing", "fr-FR", "error", True),
    ],
)
def test_create_catalog(tmp_module_repository, module, language, domain, valid):
    if valid:
        create_catalog(tmp_module_repository[4].get_repository(), module, language, domain)
        catalog_file = tmp_module_repository[2][1] / module / f"locales/{language}/LC_MESSAGES/{domain}.po"
        assert catalog_file.exists() == True
        machine_file = tmp_module_repository[2][1] / module / f"locales/{language}/LC_MESSAGES/{domain}.mo"
        assert machine_file.exists() == True
    else:
        with pytest.raises(Exception):
            create_catalog(tmp_module_repository[4].get_repository(), module, language, domain)


@pytest.mark.parametrize(
    "module, language, domain, valid",
    [
        ("fsm_tools", "en", "usage", True),
        ("fsm_tools", "fr", "usage", True),
        ("fsm_tools", "en-US", "usage", True),
        ("fsm_tools", "en-GB", "usage", True),
        ("fsm_tools", "en-US", "usage", False),
        ("fsm_tools", "fr-FR", "usage", True),
        ("fsm_tools/turing", "fr", "error", True),
        ("fsm_tools/turing", "fr-FR", "error", True),
    ],
)
def test_create_dictionary(tmp_module_repository, module, language, domain, valid):
    if valid:
        create_dictionary(tmp_module_repository[4].get_repository(), module, language, domain)
        catalog_file = tmp_module_repository[2][1] / module / f"locales/{language}/LC_MESSAGES/{domain}.json"
        assert catalog_file.exists() == True
    else:
        with pytest.raises(Exception):
            create_dictionary(tmp_module_repository[4].get_repository(), module, language, domain)


@pytest.mark.parametrize(
    "module, domain, content, valid",
    [
        ("fsm_tools", "model", ["fsm-tools", "model"], True),
        ("fsm_tools", "error", ["fsm-tools", "error"], False),
        ("fsm_tools/turing", "information", ["fsm-tools", "information"], True),
        ("fsm_tools/turing", "error", ["fsm-tools", "error"], True),
        ("fsm_tools/turing", "model", ["fsm-tools", "model"], False),
        ("fsm_tools", "usage", ["fsm-tools", "usage"], True),
    ],
)
def test_fetch_template(tmp_module_repository, module, domain, content, valid):
    if valid:
        catalog = fetch_template(tmp_module_repository[4].get_repository(), module, domain)
        assert catalog.project == content[0]
        assert catalog.domain == content[1]
    else:
        with pytest.raises(Exception):
            catalog = fetch_template(tmp_module_repository[4].get_repository(), module, domain)


@pytest.mark.parametrize(
    "module, domain, language, content, valid",
    [
        ("fsm_tools", "usage", "en", ["fsm-tools", "usage"], True),
        ("fsm_tools", "usage", "en-US", ["fsm-tools", "usage"], True),
        ("fsm_tools", "error", "fr", ["fsm-tools", "error"], False),
        ("fsm_tools", "usage", "fr", ["fsm-tools", "usage"], True),
        ("fsm_tools/turing", "error", "fr-FR", ["fsm-tools", "error"], True),
    ],
)
def test_fetch_catalog(tmp_module_repository, module, language, domain, content, valid):
    if valid:
        catalog = fetch_catalog(tmp_module_repository[4].get_repository(), module, language, domain)
        assert catalog.project == content[0]
        assert catalog.domain == content[1]
        assert catalog.locale == Locale.parse(language, sep="-")
    else:
        with pytest.raises(Exception):
            catalog = fetch_catalog(tmp_module_repository[4].get_repository(), module, language, domain)

@pytest.mark.parametrize(
    "module, language, domain, content, valid",
    [
        ("fsm_tools", "en", "usage", ["fsm-tools", "0.0.1"], True),
        ("fsm_tools", "fr", "usage", ["fsm-tools", "0.0.1"], True),
        ("fsm_tools", "en-US", "usage", ["fsm-tools", "0.0.1"], True),
        ("fsm_tools", "en-GB", "usage", ["fsm-tools", "0.0.1"], True),
        ("fsm_tools", "fr-FR", "usage", ["fsm-tools", "0.0.1"], True),
        ("fsm_tools/turing", "fr", "error", ["fsm-tools", "0.0.1"], True),
        ("fsm_tools/turing", "fr-FR", "error", ["fsm-tools", "0.0.1"], True),
    ],
)
def test_fetch_dictionary(tmp_module_repository, module, domain, language, content, valid):
    if valid:
        dictionary = fetch_dictionary(tmp_module_repository[4].get_repository(), module, language, domain)
        assert dictionary[".i18n_tools"]["name"] == content[0]
        assert dictionary[".i18n_tools"]["version"] == content[1]
    else:
        with pytest.raises(Exception):
            dictionary = fetch_dictionary(tmp_module_repository[4].get_repository(), module, language, domain)

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
