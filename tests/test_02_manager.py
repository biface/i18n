import pytest
import json
from pathlib import Path
from i18n_tools.manager import (
    _verify_paths_and_modules,
    _update_json_translations,
    _create_po_entry,
    _update_po_translations,
    add_translation_set
)
from polib import POFile, POEntry


@pytest.fixture
def sample_repository(tmp_path):
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    (repo_path / "module-1" / "locales").mkdir(parents=True)
    (repo_path / "module-2" / "locales").mkdir(parents=True)
    return {
        "base": str(repo_path),
        "modules": ["module-1", "module-2"],
        "domains": {
            "module-1": ["domain-1", "domain-2"],
            "module-2": ["domain-2"]
        },
        "languages": {
            "fr": ["fr-FR", "fr-BE", "fr-CA"],
            "en": ["en-IE", "en-US", "en-GB"],
            "es": ["es-ES", "es-MX"],
        }
    }


@pytest.fixture
def sample_translations():
    return {
        "fr": {
            "msgid_001": [["Traduction 1"]],
            "msgid_002": [["Traduction 2"], ["Pluriel 1", "Pluriel 2"]]
        },
        "en": {
            "msgid_001": [["Translation 1"]],
            "msgid_002": [["Translation 2"], ["Plural 1", "Plural 2"]]
        }
    }


def test_verify_paths_and_modules(sample_repository):
    _verify_paths_and_modules(sample_repository)


def test_verify_paths_and_modules_invalid_path(sample_repository):
    sample_repository["base"] = "/invalid/path"
    with pytest.raises(FileNotFoundError):
        _verify_paths_and_modules(sample_repository)


@pytest.mark.parametrize(
    "existing_translations, translation_data, expected_output",
    [
        (
                {"msgid_001": [["Existing 1"]]},
                {"msgid_001": [["New 1"]]},
                {"msgid_001": [["Existing 1", "New 1"]]}
        ),
        (
                {"msgid_001": [["Existing 1"]]},
                {"msgid_002": [["New 2"]]},
                {"msgid_001": [["Existing 1"]], "msgid_002": [["New 2"]]}
        ),
    ]
)
def test_update_json_translations(existing_translations, translation_data, expected_output):
    result = _update_json_translations(existing_translations, translation_data)
    assert result == expected_output


@pytest.mark.parametrize(
    "msgid, msgid_plural, msgstr, msgstr_plural, expected_output",
    [
        (
                "msgid_001", "msgid_001_plr", "Translation", None,
                POEntry(msgid="msgid_001", msgid_plural="msgid_001_plr", msgstr="Translation")
        ),
        (
                "msgid_002", "msgid_002_plr", "Translation", {0: "Plural 1", 1: "Plural 2"},
                POEntry(msgid="msgid_002", msgid_plural="msgid_002_plr", msgstr="Translation",
                        msgstr_plural={0: "Plural 1", 1: "Plural 2"})
        ),
    ]
)
def test_create_po_entry(msgid, msgid_plural, msgstr, msgstr_plural, expected_output):
    result = _create_po_entry(msgid, msgid_plural, msgstr, msgstr_plural)
    assert result.msgid == expected_output.msgid
    assert result.msgid_plural == expected_output.msgid_plural
    assert result.msgstr == expected_output.msgstr
    if msgstr_plural:
        assert result.msgstr_plural == expected_output.msgstr_plural


@pytest.mark.parametrize(
    "translations, expected_po_entries",
    [
        (
                {"msgid_001": [["Translation"]]},
                [POEntry(msgid="msgid_001", msgid_plural="msgid_001_plr", msgstr="Translation")]
        ),
        (
                {"msgid_002": [["Translation"], ["Plural 1"], ["Plural 2"]]},
                [POEntry(msgid="msgid_002", msgid_plural="msgid_002_plr", msgstr="Translation",
                         msgstr_plural={1: "Plural 1", 2: "Plural 2"})]
        ),
        (
                {"msgid_003": [["Translation 1", "Traduction 2"],
                               ["Plural 1-1", "Plural 2-1"],
                               ["Plural 2-1", "Plural 2-2"]]},
                [POEntry(msgid="msgid_003_000", msgid_plural="msgid_003_000_plr", msgstr="Translation 1",
                         msgstr_plural={1: "Plural 1-1", 2: "Plural 2-1"}),
                 POEntry(msgid="msgid_003_001", msgid_plural="msgid_003_001_plr", msgstr="Traduction 2",
                         msgstr_plural={1: "Plural 2-1", 2: "Plural 2-2"})
                 ]
        )
    ]
)
def test_update_po_translations(translations, expected_po_entries):
    po_file = POFile()
    _update_po_translations(po_file, translations)
    assert len(po_file) == len(expected_po_entries)
    for entry, expected_entry in zip(po_file, expected_po_entries):
        assert entry.msgid == expected_entry.msgid
        assert entry.msgid_plural == expected_entry.msgid_plural
        assert entry.msgstr == expected_entry.msgstr
        if expected_entry.msgstr_plural:
            assert entry.msgstr_plural == expected_entry.msgstr_plural


@pytest.mark.parametrize(
    "translations",
    [
        {
            "fr": {
                "msgid_001": [["Traduction 1"]],
                "msgid_002": [["Traduction 2"], ["Pluriel 1"], ["Pluriel 2"]]
            },
            "fr-FR": {
                "msgid_001": [["Traduction 1"]],
                "msgid_002": [["Traduction 2"], ["Pluriel 1"], ["Pluriel 2"]]
            },
            "en": {
                "msgid_001": [["Translation 1"]],
                "msgid_002": [["Translation 2"], ["Plural 1"], ["Plural 2"]]
            },
            "es": {
                "msgid_001": [["Traducción 1"]],
                "msgid_002": [["Traducción 2"], ["Plural 1"], ["Plural 2"]]
            }
        },
    ]
)
def test_add_translation_set(sample_repository, translations):
    add_translation_set(sample_repository, translations)

    repository_path = Path(sample_repository["base"])

    for lang, translation_data in translations.items():
        for module in sample_repository["modules"]:
            for domain in sample_repository["domains"][module]:
                lang_path = (
                    repository_path
                    / module
                    / "locales"
                    / lang
                    / "LC_MESSAGES"
                )
                json_file_path = lang_path / f"{domain}.json"
                po_file_path = lang_path / f"{domain}.po"

                # Verify JSON content
                with open(json_file_path, "r", encoding="utf-8") as json_file:
                    saved_json_content = json.load(json_file)
                    assert saved_json_content == translation_data

                # Verify PO content
                po_file = POFile(str(po_file_path))
                for entry in po_file:
                    msgid = entry.msgid.split("_")[0]
                    assert msgid in translation_data
                    if len(translation_data[msgid][0]) == 1:
                        assert entry.msgstr == translation_data[msgid][0][0]
                    else:
                        assert entry.msgstr in translation_data[msgid][0]
                        if entry.msgstr_plural:
                            for i, plural in enumerate(translation_data[msgid][1:]):
                                assert entry.msgstr_plural[i] == plural[0]
