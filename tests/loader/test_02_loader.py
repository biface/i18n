import os

import pytest
from babel.core import Locale

from i18n_tools.__static__ import I18N_TOOLS_TRANSLATION_FILE_EXT
from i18n_tools.loaders.handler import (
    _verify_available_languages,
    _verify_paths_and_modules,
    _verify_target_domain,
    _verify_target_module,
    build_path,
    build_translation_lang_files,
    create_catalog,
    create_dictionary,
    create_directory,
    create_template,
    dump_dictionary,
    fetch_catalog,
    fetch_dictionary,
    fetch_template,
    remove_catalog,
    remove_dictionary,
    remove_template,
    update_catalog,
    update_dictionary,
)
from i18n_tools.loaders.repository import (
    _update_json_translations,
    add_translation_set,
    aggregate_dictionaries,
    build_repository,
    create_module_archive,
    remove_translation_set,
    restore_module_from_archive,
    update_translation_set,
    verify_repository,
)


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
        (
            "package",
            ["i18n_tools", "locales", "_i18n_tools"],
            "i18n_tools/locales/_i18n_tools",
            True,
        ),
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
    base_path = (
        tmp_function_repository[0][0]
        + "/"
        + conf_tests["repository"][module]["repository"]
    )
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
    "dir_path",
    [
        "fsm_tools/turing/locales/templates",
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
    "module, domain, valid, exception",
    [
        ("fsm_tools", "model", True, None),
        ("fsm_tools", "error", False, ValueError),
        ("fsm_tools/turing", "information", True, None),
        ("fsm_tools/turing", "error", True, None),
        ("fsm_tools/turing", "model", False, ValueError),
        ("fsm-tools/turing", "error", False, ValueError),
        ("fsm_tools/turing", "error", False, FileExistsError),
    ],
)
def test_create_template(tmp_module_repository, module, domain, valid, exception):
    if valid:
        create_template(tmp_module_repository[4].get_repository(), module, domain)
        template_file = (
            tmp_module_repository[2][1] / module / "locales/templates" / f"{domain}.pot"
        )
        assert template_file.exists() == True
    else:
        with pytest.raises(exception):
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
        create_catalog(
            tmp_module_repository[4].get_repository(), module, language, domain
        )
        catalog_file = (
            tmp_module_repository[2][1]
            / module
            / f"locales/{language}/LC_MESSAGES/{domain}.po"
        )
        assert catalog_file.exists() == True
        machine_file = (
            tmp_module_repository[2][1]
            / module
            / f"locales/{language}/LC_MESSAGES/{domain}.mo"
        )
        assert machine_file.exists() == True
    else:
        with pytest.raises(Exception):
            create_catalog(
                tmp_module_repository[4].get_repository(), module, language, domain
            )


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
        create_dictionary(
            tmp_module_repository[4].get_repository(), module, language, domain
        )
        catalog_file = (
            tmp_module_repository[2][1]
            / module
            / f"locales/{language}/LC_MESSAGES/{domain}.json.{I18N_TOOLS_TRANSLATION_FILE_EXT}"
        )
        assert catalog_file.exists() == True
    else:
        with pytest.raises(Exception):

            create_dictionary(
                tmp_module_repository[4].get_repository(), module, language, domain
            )


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
        catalog = fetch_template(
            tmp_module_repository[4].get_repository(), module, domain
        )
        assert catalog.project == content[0]
        assert catalog.domain == content[1]
    else:
        with pytest.raises(Exception):
            catalog = fetch_template(
                tmp_module_repository[4].get_repository(), module, domain
            )


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
        catalog = fetch_catalog(
            tmp_module_repository[4].get_repository(), module, language, domain
        )
        assert catalog.project == content[0]
        assert catalog.domain == content[1]
        assert catalog.locale == Locale.parse(language, sep="-")
    else:
        with pytest.raises(Exception):
            catalog = fetch_catalog(
                tmp_module_repository[4].get_repository(), module, language, domain
            )


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
        ("fms_tools/lba", "fr", "information", ["fsm-tools", "information"], False),
    ],
)
def test_fetch_dictionary(
    tmp_module_repository, module, domain, language, content, valid
):
    if valid:
        dictionary = fetch_dictionary(
            tmp_module_repository[4].get_repository(), module, language, domain
        )
        assert dictionary == {}
    else:
        with pytest.raises(Exception):
            dictionary = fetch_dictionary(
                tmp_module_repository[4].get_repository(), module, language, domain
            )


@pytest.mark.parametrize(
    "module, language, domain, data, valid",
    [
        (
            "fsm_tools",
            "fr-FR",
            "usage",
            {
                "1000": {
                    "string": "La machine de turing",
                    "plural": "Les machines de turing",
                    "location": "",
                    "previous_id": "",
                },
                "1000_001": {
                    "string": "Automate linéairement borné",
                    "location": "",
                    "previous_id": "1000",
                },
            },
            True,
        ),
        (
            "fsm_tools",
            "fr-FR",
            "usage",
            {
                "1000": {
                    "string": "La machine de turing",
                    "plural": "Les machines de turing",
                    "location": "",
                    "previous_id": "",
                },
                "1000_001": [
                    "Automate linéairement borné",
                    "",
                    "1000",
                ],
            },
            False,
        ),
    ],
)
def test_update_catalog(
    conf_tests, tmp_module_repository, module, language, domain, data, valid
):
    if valid:
        update_catalog(
            tmp_module_repository[4].get_repository(), module, language, domain, data
        )
        catalog = fetch_catalog(
            tmp_module_repository[4].get_repository(), module, language, domain
        )
        assert catalog.locale == Locale.parse(language, sep="-")
        assert catalog.domain == domain
        message = catalog.get("1000_001")
        assert message.string == data["1000_001"]["string"]
    else:
        with pytest.raises(Exception):
            update_catalog(
                tmp_module_repository[4].get_repository(),
                module,
                language,
                domain,
                data,
            )


@pytest.mark.parametrize(
    "module, language, domain, data, valid",
    [
        (
            "fsm_tools",
            "fr-FR",
            "usage",
            {
                "1000": [
                    ["La machine de turing", "Automate linéairement borné"],
                    ["Les machines de turing", "Les automates linéairement bornés"],
                ],
                "2000": [["Automate"], ["Automates"], ["Automatons"]],
            },
            True,
        ),
        (
            "fsm_tools",
            "fr-FR",
            "usage",
            {
                "1000": [
                    ["La machine de turing", "Automate linéairement borné"],
                    ["Les machines de turing", "Les automates linéairement bornés"],
                ],
                "2000": [["Automate", "Automates"], ["Automatons"]],
            },
            False,
        ),
    ],
)
def test_update_dictionary(
    tmp_module_repository, module, language, domain, data, valid
):
    if valid:
        update_dictionary(
            tmp_module_repository[4].get_repository(), module, language, domain, data
        )
        dictionary = fetch_dictionary(
            tmp_module_repository[4].get_repository(), module, language, domain
        )
        assert dictionary.get("1000") == data["1000"]
    else:
        with pytest.raises(Exception):
            update_dictionary(
                tmp_module_repository[4].get_repository(),
                module,
                language,
                domain,
                data,
            )


@pytest.mark.parametrize(
    "module, archive, valid",
    [
        ("fsm_tools", "fsm-tools", True),
        ("django", "django", False),
    ],
)
def test_create_module_archive(tmp_module_repository, module, archive, valid):
    if valid:
        create_module_archive(
            tmp_module_repository[4].get_repository(), module, archive
        )
        archive_file = (
            tmp_module_repository[4].get_repository()[["paths", "repository"]]
            + "/"
            + module
            + "/locales/_i18n_tools/backup/"
            + archive
            + ".tar.gz"
        )
        assert os.path.exists(archive_file)
    else:
        with pytest.raises(Exception):
            create_module_archive(
                tmp_module_repository[4].get_repository(), module, archive
            )


@pytest.mark.parametrize(
    "module, domain",
    [
        ("fsm_tools", "model"),
    ],
)
def test_remove_template(tmp_module_repository, module, domain):
    remove_template(tmp_module_repository[4].get_repository(), module, domain)
    template_file = (
        tmp_module_repository[2][1] / module / "locales/templates" / f"{domain}.pot"
    )
    assert not template_file.exists()


@pytest.mark.parametrize(
    "module, language, domain",
    [
        ("fsm_tools", "fr-FR", "usage"),
    ],
)
def test_remove_catalog(tmp_module_repository, module, language, domain):
    catalog_file = (
        tmp_module_repository[2][1] / module / f"locales/{language}/{domain}.po"
    )
    remove_catalog(tmp_module_repository[4].get_repository(), module, language, domain)
    assert not catalog_file.exists()


@pytest.mark.parametrize(
    "module, language, domain",
    [
        ("fsm_tools", "fr-FR", "usage"),
    ],
)
def test_remove_dictionary(tmp_module_repository, module, language, domain):
    dictionary_file = (
        tmp_module_repository[2][1] / module / f"locales/{language}/{domain}.json"
    )
    remove_dictionary(
        tmp_module_repository[4].get_repository(), module, language, domain
    )
    assert not dictionary_file.exists()


@pytest.mark.parametrize(
    "module, archive, valid",
    [
        ("fsm_tools", "fsm-tools", True),
        ("django", "django", False),
        ("fsm_tools", "no-archive", False),
    ],
)
def test_restore_module_from_archive(tmp_module_repository, module, archive, valid):
    if valid:
        files_names = [
            f"{tmp_module_repository[4].get_repository()[['paths', 'repository']]}/{module}/locales/fr-FR/LC_MESSAGES/usage.{ext}"
            for ext in ["json." + I18N_TOOLS_TRANSLATION_FILE_EXT, "po", "mo"]
        ]
        """files_names.append(f"{tmp_module_repository[4].get_repository()[['paths', 'repository']]}/{module}/locales/templates/usage.pot")"""
        for file in files_names:
            assert not os.path.exists(file)
        restore_module_from_archive(
            tmp_module_repository[4].get_repository(), module, archive
        )
        for file in files_names:
            assert os.path.exists(file)
    else:
        with pytest.raises(Exception):
            if archive == "no-archive":
                restore_module_from_archive(
                    tmp_module_repository[4].get_repository(), "fsm-tools", archive
                )
            else:
                restore_module_from_archive(
                    tmp_module_repository[4].get_repository(), module, archive
                )


def test_remove_with_failed_paths(tmp_module_repository):
    with pytest.raises(Exception):
        remove_template(
            tmp_module_repository[4].get_repository(), "django-fsm_tools", "usage"
        )
        remove_catalog(
            tmp_module_repository[4].get_repository(), "django-fsm_tools", "fr", "usage"
        )
        remove_dictionary(
            tmp_module_repository[4].get_repository(), "django-fsm_tools", "fr", "usage"
        )


@pytest.mark.parametrize(
    "modules, domains, languages",
    [
        (
            ["fsm_tools", "fsm_tools/turing"],
            {
                "fsm_tools": ["model", "usage"],
                "fsm_tools/turing": ["error", "information"],
            },
            ["fr", "en-US", "en-GB", "fr-FR"],
        ),
    ],
)
def test_build_repository(tmp_module_repository, modules, domains, languages):
    # Call build_repository
    build_repository(tmp_module_repository[4].get_repository())

    # Check that template files exist for each module and domain
    for module in modules:
        for domain in domains.get(module, []):
            template_file = (
                tmp_module_repository[2][1]
                / module
                / "locales/templates"
                / f"{domain}.pot"
            )
            assert template_file.exists() == True

            # Check that catalog files exist for each module, domain, and language
            for language in languages:
                catalog_file = (
                    tmp_module_repository[2][1]
                    / module
                    / f"locales/{language}/LC_MESSAGES/{domain}.po"
                )
                assert catalog_file.exists() == True

                machine_file = (
                    tmp_module_repository[2][1]
                    / module
                    / f"locales/{language}/LC_MESSAGES/{domain}.mo"
                )
                assert machine_file.exists() == True

                # Check that dictionary files exist for each module, domain, and language
                dictionary_file = (
                    tmp_module_repository[2][1]
                    / module
                    / f"locales/{language}/LC_MESSAGES/{domain}.json.{I18N_TOOLS_TRANSLATION_FILE_EXT}"
                )
                assert dictionary_file.exists() == True


def test_verify_repository(tmp_module_repository):
    assert verify_repository(tmp_module_repository[4].get_repository()) == True


@pytest.mark.parametrize(
    "module, domain, valid, exception",
    [
        ("fsm_tools", "usage", True, None),
        ("fsm_tools/turing", "information", True, None),
        ("fsm-tools/turing", "information", False, ValueError),
    ],
)
def test_aggregate_dictionaries(
    tmp_module_repository, module, domain, valid, exception
):
    config = tmp_module_repository[4]
    if valid:
        aggregate_dictionaries(config.get_repository(), module, domain)
        dictionary_path = build_path(tmp_module_repository[2][1] / module / "locales")
        dictionary_file = dictionary_path + f"/{domain}_aggregated.json"
        assert os.path.exists(dictionary_file)
        dictionary_zip = dictionary_path + f"/{domain}_aggregated.json.gz"
        assert os.path.exists(dictionary_zip)
    else:
        with pytest.raises(exception):
            aggregate_dictionaries(config.get_repository(), module, domain)


@pytest.mark.parametrize(
    "module, domain, lang, valid, exception",
    [
        ("fsm_tools", "usage", "fr", True, None),
        ("fsm_tools/turing", "information", "en-US", True, None),
        ("fsm_tools/turing", "information", "en-IE", False, OSError),
        (
            "fsm_tools/turing",
            "information",
            "ja.Latn/hepburn@heploc",
            False,
            ValueError,
        ),
    ],
)
def test_translation_lang_file(
    tmp_module_repository, module, domain, lang, valid, exception
):
    repository = tmp_module_repository[4].get_repository()
    if valid:
        file_json, file_po, file_pot = build_translation_lang_files(
            repository, module, domain, lang
        )
        assert (
            file_json
            == repository["paths"]["repository"]
            + "/"
            + module
            + "/locales/"
            + lang
            + "/LC_MESSAGES/"
            + domain
            + ".json.i18t"
        )
        assert (
            file_po
            == repository["paths"]["repository"]
            + "/"
            + module
            + "/locales/"
            + lang
            + "/LC_MESSAGES/"
            + domain
            + ".po"
        )
    else:
        with pytest.raises(exception):
            build_translation_lang_files(repository, module, domain, lang)


@pytest.mark.parametrize(
    "repository, modified_path, valid, exception",
    [
        ("application", "", True, None),
        ("package", "", False, FileNotFoundError),
        ("application", "fsm_tools/turing", False, ValueError),
    ],
)
def test_verify_path_and_modules(
    tmp_module_repository, repository, modified_path, valid, exception
):
    config = tmp_module_repository[4]
    if repository == "application":
        config.switch_to_application_config()
        config.load()
    elif repository == "package":
        config.switch_to_package_config()
        config.get_repository()["paths"]["repository"] = tmp_module_repository[1][0]
        config.get_repository()["paths"]["config"] = (
            tmp_module_repository[1][0] + "/i18n_tools/locales/_i18n_tools"
        )
        config.get_repository()["paths"]["settings"] = "i18n-tools.yaml"
        config.load()

    if modified_path != "":
        old_path = config.get_repository()["paths"]["repository"]
        config.get_repository()["paths"]["repository"] = modified_path
        with pytest.raises(exception):
            _verify_paths_and_modules(config.get_repository())
        config.get_repository()["paths"]["repository"] = old_path
    else:
        if valid:
            _verify_paths_and_modules(config.get_repository())
        else:
            with pytest.raises(exception):
                _verify_paths_and_modules(config.get_repository())


@pytest.mark.parametrize(
    "languages, valid, exception",
    [
        (["fr", "en-US", "en-GB"], True, None),
        (["en", "en-US", "en-GB", "fr-FR"], True, None),
        (
            ["fr", "en-US", "en-GB", "fr-FR", "ja.Latn/hepburn@heploc"],
            False,
            ValueError,
        ),
        (["sv", "en-US", "en-GB", "fr-FR"], False, ValueError),
    ],
)
def test_verify_available_language(tmp_module_repository, languages, valid, exception):
    if valid:
        _verify_available_languages(
            tmp_module_repository[4].get_repository(), languages
        )
    else:
        with pytest.raises(exception):
            _verify_available_languages(
                tmp_module_repository[4].get_repository(), languages
            )


@pytest.mark.parametrize(
    "module, valid, exception",
    [
        ("fsm_tools", True, None),
        ("fsm_tools/turing", True, None),
        ("fsm-tools/turing", False, ValueError),
    ],
)
def test_verify_target_module(tmp_module_repository, module, valid, exception):
    if valid:
        _verify_target_module(tmp_module_repository[4].get_repository(), module)
    else:
        with pytest.raises(exception):
            _verify_target_module(tmp_module_repository[4].get_repository(), module)


@pytest.mark.parametrize(
    "module, domain, valid, exception, msg_error",
    [
        ("fsm_tools", "usage", True, None, None),
        (
            "fsm_tools/turing",
            "model",
            False,
            IndexError,
            "The target domain 'model' is not registered in the repository",
        ),
        (
            "fsm-tools/turing",
            "information",
            False,
            ValueError,
            "The target module 'fsm-tools/turing' is not registered in the repository",
        ),
    ],
)
def test_verify_target_domain(
    tmp_module_repository, module, domain, valid, exception, msg_error
):
    if valid:
        _verify_target_domain(tmp_module_repository[4].get_repository(), module, domain)
    else:
        with pytest.raises(exception, match=msg_error):
            _verify_target_domain(
                tmp_module_repository[4].get_repository(), module, domain
            )


@pytest.mark.parametrize(
    "existing_translation, translation_data, expected_result",
    [
        (
            {},
            {"1000": [["Dictionary"], ["Dictionaries"]]},
            {"1000": [["Dictionary"], ["Dictionaries"]]},
        ),
        (
            {"1000": [["Dictionary"], ["Dictionaries"]]},
            {"1001": [["Mouse"], ["Mice"]]},
            {"1000": [["Dictionary"], ["Dictionaries"]], "1001": [["Mouse"], ["Mice"]]},
        ),
        (
            {},
            {
                "1000": [
                    ["Un dictionnaire", "Le dictionnaire"],
                    ["Deux dictionnaires", "Les deux dictionnaires"],
                    ["Des dictionnaires", "Les dictionnaires"],
                ]
            },
            {
                "1000": [
                    ["Un dictionnaire", "Le dictionnaire"],
                    ["Deux dictionnaires", "Les deux dictionnaires"],
                    ["Des dictionnaires", "Les dictionnaires"],
                ]
            },
        ),
        (
            {
                "1000": [
                    ["Un dictionnaire", "Le dictionnaire"],
                    ["Deux dictionnaires", "Les deux dictionnaires"],
                    ["Des dictionnaires", "Les dictionnaires"],
                ]
            },
            {
                "1000": [
                    ["Un dictionnaire", "Le dictionnaire"],
                    ["Deux dictionnaires", "Les deux dictionnaires"],
                    ["Trois dictionnaires", "Les trois dictionnaires"],
                    ["Des dictionnaires", "Les dictionnaires"],
                ],
                "1010": [
                    ["Un bateau", "Le bateau"],
                    ["Deux bateaux", "Les deux bateaux"],
                    ["Des bateaux", "Les bateaux"],
                ],
            },
            {
                "1000": [
                    ["Un dictionnaire", "Le dictionnaire"],
                    ["Deux dictionnaires", "Les deux dictionnaires"],
                    ["Trois dictionnaires", "Les trois dictionnaires"],
                    ["Des dictionnaires", "Les dictionnaires"],
                ],
                "1010": [
                    ["Un bateau", "Le bateau"],
                    ["Deux bateaux", "Les deux bateaux"],
                    ["Des bateaux", "Les bateaux"],
                ],
            },
        ),
    ],
)
def test_update_json_translation(
    existing_translation, translation_data, expected_result
):
    assert (
        _update_json_translations(existing_translation, translation_data)
        == expected_result
    )


@pytest.mark.parametrize(
    "module, domain, translation_data, valid, expected_result, exception, msg_error",
    [
        (
            "fsm_tools",
            "usage",
            {
                "fr": {
                    "10101": [
                        [
                            "L'automate n'a pas pu lire le symbole car l'alphabet est vide.",
                            "L'automate n'a pas pu lire le symbole '{symbol}' car celui-ci est absent de l'alphabet.",
                        ]
                    ],
                    "10102": [
                        [
                            "L'automate n'a pas pu écrire le symbole '{symbol}' car il y est déjà présent."
                        ]
                    ],
                    "10103": [["Dois être supprimé"]],
                    "10104": [[""]],
                    "10106": [[""]],
                    "10109": [[""]],
                },
                "en": {
                    "10101": [
                        [
                            "The automaton could not read the symbol because the alphabet is empty.",
                            "The automaton could not read the symbol '{symbol}' because it is missing from the alphabet.",
                        ]
                    ],
                    "10102": [
                        [
                            "The automaton could not write the symbol '{symbol}' because it is already present."
                        ]
                    ],
                    "10103": [["Must be erased"]],
                    "10104": [[""]],
                    "10106": [[""]],
                    "10109": [[""]],
                },
            },
            True,
            [
                [
                    ["fr", "10101"],
                    [
                        [
                            "L'automate n'a pas pu lire le symbole car l'alphabet est vide.",
                            "L'automate n'a pas pu lire le symbole '{symbol}' car celui-ci est absent de l'alphabet.",
                        ]
                    ],
                ],
                [
                    ["fr", "10102"],
                    [
                        [
                            "L'automate n'a pas pu écrire le symbole '{symbol}' car il y est déjà présent."
                        ]
                    ],
                ],
                [
                    ["en", "10101"],
                    [
                        [
                            "The automaton could not read the symbol because the alphabet is empty.",
                            "The automaton could not read the symbol '{symbol}' because it is missing from the alphabet.",
                        ]
                    ],
                ],
                [
                    ["en", "10102"],
                    [
                        [
                            "The automaton could not write the symbol '{symbol}' because it is already present."
                        ]
                    ],
                ],
            ],
            None,
            None,
        ),
        (
            "fsm_tools",
            "usage",
            {
                "fr-BE": {
                    "10101": [
                        [
                            "L'automate n'a pas pu lire le symbole car l'alphabet est vide.",
                            "L'automate n'a pas pu lire le symbole '{symbol}' car celui-ci est absent de l'alphabet.",
                        ]
                    ],
                    "10102": [
                        [
                            "L'automate n'a pas pu écrire le symbole '{symbol}' car il y est déjà présent."
                        ]
                    ],
                    "10104": [[""]],
                    "10106": [[""]],
                    "10109": [[""]],
                }
            },
            False,
            [],
            ValueError,
            None,
        ),
        ("fsm_tools", "usages", {}, False, [], IndexError, ""),
    ],
)
def tests_add_translation_set(
    tmp_module_repository,
    module,
    domain,
    translation_data,
    valid,
    expected_result,
    exception,
    msg_error,
):
    if valid:
        add_translation_set(
            tmp_module_repository[4].get_repository(), module, domain, translation_data
        )
        for paths, data in expected_result:
            dictionary = fetch_dictionary(
                tmp_module_repository[4].get_repository(), module, paths[0], domain
            )
            assert dictionary[paths[1]] == data
    else:
        with pytest.raises(exception):
            add_translation_set(
                tmp_module_repository[4].get_repository(),
                module,
                domain,
                translation_data,
            )


@pytest.mark.parametrize(
    "module, domain, translation_data, valid, expected_result, exception, msg_error",
    [
        (
            "fsm_tools",
            "usage",
            {
                "fr": {
                    "10104": [
                        [
                            "Supprimer un élément de l’ensemble des terminaux d’une grammaire récursivement énumérable"
                        ]
                    ],
                    "10106": [
                        [
                            "Modifier un élément de l’ensemble des terminaux d’une grammaire récursivement énumérable"
                        ]
                    ],
                    "10109": [
                        [
                            "Rechercher un symbole dans l’ensemble des terminaux d’une grammaire récursivement énumérable"
                        ]
                    ],
                },
                "en": {
                    "10104": [
                        [
                            "Delete an element from the set of terminals of a recursively enumerable grammar"
                        ]
                    ],
                    "10106": [
                        [
                            "Modify an element of the set of terminals of a recursively enumerable grammar"
                        ]
                    ],
                    "10109": [
                        [
                            "Search for a symbol in the set of terminals of a recursively enumerable grammar"
                        ]
                    ],
                },
            },
            True,
            [
                [
                    ["fr", "10101"],
                    [
                        [
                            "L'automate n'a pas pu lire le symbole car l'alphabet est vide.",
                            "L'automate n'a pas pu lire le symbole '{symbol}' car celui-ci est absent de l'alphabet.",
                        ]
                    ],
                ],
                [
                    ["fr", "10102"],
                    [
                        [
                            "L'automate n'a pas pu écrire le symbole '{symbol}' car il y est déjà présent."
                        ]
                    ],
                ],
                [["fr", "10103"], [["Dois être supprimé"]]],
                [
                    ["fr", "10104"],
                    [
                        [
                            "Supprimer un élément de l’ensemble des terminaux d’une grammaire récursivement énumérable"
                        ]
                    ],
                ],
                [
                    ["fr", "10106"],
                    [
                        [
                            "Modifier un élément de l’ensemble des terminaux d’une grammaire récursivement énumérable"
                        ]
                    ],
                ],
                [
                    ["fr", "10109"],
                    [
                        [
                            "Rechercher un symbole dans l’ensemble des terminaux d’une grammaire récursivement énumérable"
                        ]
                    ],
                ],
                [
                    ["en", "10101"],
                    [
                        [
                            "The automaton could not read the symbol because the alphabet is empty.",
                            "The automaton could not read the symbol '{symbol}' because it is missing from the alphabet.",
                        ]
                    ],
                ],
                [
                    ["en", "10102"],
                    [
                        [
                            "The automaton could not write the symbol '{symbol}' because it is already present."
                        ]
                    ],
                ],
                [["en", "10103"], [["Must be erased"]]],
            ],
            None,
            None,
        ),
        ("fsm_tools", "usages", {}, False, [], IndexError, ""),
        (
            "fsm_tools",
            "usage",
            {
                "en": {
                    "10199": [
                        [
                            "Delete the entire set of terminals of a recursively enumerable grammar"
                        ]
                    ]
                }
            },
            False,
            [],
            KeyError,
            "",
        ),
    ],
)
def tests_update_translation_set(
    tmp_module_repository,
    module,
    domain,
    translation_data,
    valid,
    expected_result,
    exception,
    msg_error,
):
    if valid:
        update_translation_set(
            tmp_module_repository[4].get_repository(), module, domain, translation_data
        )
        for paths, data in expected_result:
            dictionary = fetch_dictionary(
                tmp_module_repository[4].get_repository(), module, paths[0], domain
            )
            assert dictionary[paths[1]] == data
    else:
        with pytest.raises(exception):
            update_translation_set(
                tmp_module_repository[4].get_repository(),
                module,
                domain,
                translation_data,
            )


@pytest.mark.parametrize(
    "module, domain, translation_data, valid, expected_result, exception, msg_error",
    [
        (
            "fsm_tools",
            "usage",
            {
                "fr": {
                    "10103": [["Dois être supprimé"]],
                },
                "en": {
                    "10103": [["Must be erased"]],
                },
            },
            True,
            [
                [["fr", "10103"], [["Dois être supprimé"]]],
                [["en", "10103"], [["Must be erased"]]],
            ],
            None,
            None,
        ),
        ("fsm_tools", "usages", {}, False, [], IndexError, ""),
    ],
)
def tests_remove_translation_set(
    tmp_module_repository,
    module,
    domain,
    translation_data,
    valid,
    expected_result,
    exception,
    msg_error,
):
    if valid:
        remove_translation_set(
            tmp_module_repository[4].get_repository(), module, domain, translation_data
        )
        for paths, data in expected_result:
            dictionary = fetch_dictionary(
                tmp_module_repository[4].get_repository(), module, paths[0], domain
            )
            assert paths[1] not in dictionary.keys()
    else:
        with pytest.raises(exception):
            update_translation_set(
                tmp_module_repository[4].get_repository(),
                module,
                domain,
                translation_data,
            )
