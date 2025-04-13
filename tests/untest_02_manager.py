import json
from pathlib import Path

import pytest
from polib import POEntry, POFile

from i18n_tools.manager import (
    _create_po_entry,
    _remove_po_translations,
    _update_json_translations,
    _update_po_translations,
    _verify_available_languages,
    _verify_paths_and_modules,
    _verify_target_domain,
    _verify_target_module,
    add_translation_set,
    remove_translation_set,
    update_translation_set,
)


@pytest.fixture
def sample_repository(tmp_path):
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    (repo_path / "module-1" / "locales").mkdir(parents=True)
    (repo_path / "module-2" / "locales").mkdir(parents=True)
    return {
        "base": str(repo_path),
        "modules": ["module-1", "module-2"],
        "domains": {"module-1": ["domain-1", "domain-2"], "module-2": ["domain-2"]},
        "languages": {
            "fr": ["fr-FR", "fr-BE", "fr-CA"],
            "en": ["en-IE", "en-US", "en-GB"],
            "es": ["es-ES", "es-MX"],
        },
    }


@pytest.fixture
def sample_translations():
    return {
        "fr": {
            "msgid_001": [["Traduction 1"]],
            "msgid_002": [["Traduction 2"], ["Pluriel 1"]],
            "msgid_003": [
                ["Traduction 31", "Option 32"],
                ["Pluriel 1-31", "Pluriel Option 1-32"],
                ["Pluriel 2-31", "Pluriel Option 2-32"],
            ],
            "msgid_004": [
                ["Traduction 41", "Option 42"],
                ["Pluriel 41", "Pluriel Option 42"],
            ],
            "msgid_005": [
                ["Traduction 51", "Option 52", "Option 53"],
                ["Pluriel 51-1", "Pluriel Option 52-1", "Pluriel Option 53-1"],
                ["Pluriel 51-2", "Pluriel Option 52-2", "Pluriel Option 53-2"],
            ],
        },
        "en": {
            "msgid_001": [["Translation 1"]],
            "msgid_002": [["Translation 2"], ["Plural 1"]],
            "msgid_003": [
                ["Translation 31", "Option 32"],
                ["Plural 1-31", "Optional Plural 1-32"],
                ["Plural 2-31", "Optional Plural 2-32"],
            ],
            "msgid_004": [
                ["Translation 41", "Option 42"],
                ["Plural 41", "Optional Plural 42"],
            ],
            "msgid_005": [
                ["Translation 51", "Option 52", "Option 53"],
                ["Plural 51-1", "Optional Plural 52-1", "Optional Plural 53-1"],
                ["Plural 51-2", "Optional Plural 52-2", "Optional Plural 53-2"],
            ],
        },
        "es": {
            "msgid_001": [["Traducción 1"]],
            "msgid_002": [["Traducción 2"], ["Plural 1"]],
        },
    }


@pytest.fixture
def sample_po_file():
    po_file = POFile()
    po_file.metadata = {
        "Project-Id-Version": "1.0",
        "POT-Creation-Date": "2023-01-01 12:00+0000",
        "PO-Revision-Date": "2023-01-01 12:00+0000",
        "Last-Translator": "you <you@example.com>",
        "Language-Team": "French <fr@li.org>",
        "Language": "fr",
        "MIME-Version": "1.0",
        "Content-Type": "text/plain; charset=utf-8",
        "Content-Transfer-Encoding": "8bit",
    }
    # Add entries with and without options
    po_file.append(POEntry(msgid="msgid_001", msgstr="Translation 1"))
    po_file.append(
        POEntry(
            msgid="msgid_002",
            msgstr="Translation 2",
            msgstr_plural={0: "Plural 1", 1: "Plural 2"},
        )
    )
    po_file.append(POEntry(msgid="msgid_003_000", msgstr="Option 1"))
    po_file.append(POEntry(msgid="msgid_003_001", msgstr="Option 2"))
    return po_file


@pytest.fixture
def sample_file(sample_repository, sample_translations):
    repository_path = Path(sample_repository["base"])
    for lang, translations in sample_translations.items():
        lang_path = repository_path / "module-1" / "locales" / lang / "LC_MESSAGES"
        lang_path.mkdir(parents=True, exist_ok=True)

        json_file_path = lang_path / "domain-1.json"
        po_file_path = lang_path / "domain-1.po"

        # Initialize with some existing translations
        with open(json_file_path, "w", encoding="utf-8") as json_file:
            json.dump(translations, json_file)

        po_file = POFile()
        po_file.metadata = {
            "Project-Id-Version": "1.0",
            "POT-Creation-Date": "2023-01-01 12:00+0000",
            "PO-Revision-Date": "2023-01-01 12:00+0000",
            "Last-Translator": "you <you@example.com>",
            "Language-Team": "French <fr@li.org>",
            "Language": lang,
            "MIME-Version": "1.0",
            "Content-Type": "text/plain; charset=utf-8",
            "Content-Transfer-Encoding": "8bit",
        }
        for msgid, msgs in translations.items():
            po_entry = POEntry(msgid=msgid, msgstr=msgs[0][0])
            if len(msgs[0]) > 1:
                po_entry.msgstr_plural = {i: msgs[i][0] for i in range(1, len(msgs))}
            po_file.append(po_entry)
        po_file.save(str(po_file_path))

    return sample_repository


def test_verify_paths_and_modules(sample_repository):
    _verify_paths_and_modules(sample_repository)


def test_verify_paths_and_modules_invalid_path(sample_repository):
    sample_repository["base"] = "/invalid/path"
    with pytest.raises(FileNotFoundError):
        _verify_paths_and_modules(sample_repository)


def test_verify_not_relative_paths(sample_repository):
    sample_repository["base"] = "../../relative/path"
    with pytest.raises(ValueError):
        _verify_paths_and_modules(sample_repository)


@pytest.mark.parametrize(
    "languages, check",
    [
        (["en", "en-IE", "en-GB"], True),
        (["fr", "fr-CA"], True),
        (["it", "it-IT"], False),
        (["es", "es-AR", "es-BO"], False),
    ],
)
def test_verify_available_languages(sample_repository, languages, check):
    if check:
        _verify_available_languages(sample_repository, languages)
    else:
        with pytest.raises(ValueError):
            _verify_available_languages(sample_repository, languages)


@pytest.mark.parametrize(
    "module, check",
    [
        ("module-1", True),
        ("module-2", True),
        ("module-3", False),
        ("module-4", False),
    ],
)
def test_verify_target_module(sample_repository, module, check):
    if check:
        _verify_target_module(sample_repository, module)
    else:
        with pytest.raises(ValueError):
            _verify_target_module(sample_repository, module)


@pytest.mark.parametrize(
    "module, domain, check",
    [
        ("module-1", "domain-1", True),
        ("module-1", "domain-2", True),
        ("module-1", "domain-3", False),
        ("module-2", "domain-1", False),
        ("module-2", "domain-2", True),
        ("module-2", "domain-3", False),
        ("module-3", "domain-1", False),
        ("module-3", "domain-2", False),
    ],
)
def test_verify_target_module_domains(sample_repository, module, domain, check):
    if check:
        _verify_target_domain(sample_repository, module, domain)
    else:
        with pytest.raises(ValueError):
            _verify_target_domain(sample_repository, module, domain)


@pytest.mark.parametrize(
    "existing_translations, translation_data, expected_output",
    [
        (
            {"msgid_001": [["Existing 1"]]},
            {"msgid_001": [["New 1"]]},
            {"msgid_001": [["Existing 1", "New 1"]]},
        ),
        (
            {"msgid_001": [["Existing 1"]]},
            {"msgid_002": [["New 2"]]},
            {"msgid_001": [["Existing 1"]], "msgid_002": [["New 2"]]},
        ),
    ],
)
def test_update_json_translations(
    existing_translations, translation_data, expected_output
):
    result = _update_json_translations(existing_translations, translation_data)
    assert result == expected_output


@pytest.mark.parametrize(
    "msgid, msgid_plural, msgstr, msgstr_plural, expected_output",
    [
        (
            "msgid_001",
            "msgid_001_plr",
            "Translation",
            None,
            POEntry(msgid="msgid_001", msgstr="Translation"),
        ),
        (
            "msgid_002",
            "msgid_002_plr",
            "Translation",
            {1: "Plural 1", 2: "Plural 2"},
            POEntry(
                msgid="msgid_002",
                msgid_plural="msgid_002_plr",
                msgstr="Translation",
                msgstr_plural={0: "Translation", 1: "Plural 1", 2: "Plural 2"},
            ),
        ),
    ],
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
            [POEntry(msgid="msgid_001", msgstr="Translation")],
        ),
        (
            {"msgid_004": [["Translation 1", "Translation 2"]]},
            [
                POEntry(msgid="msgid_004_000", msgstr="Translation 1"),
                POEntry(msgid="msgid_004_001", msgstr="Translation 2"),
            ],
        ),
        (
            {"msgid_002": [["Translation"], ["Plural 1"], ["Plural 2"]]},
            [
                POEntry(
                    msgid="msgid_002",
                    msgid_plural="msgid_002_plr",
                    msgstr="Translation",
                    msgstr_plural={0: "Translation", 1: "Plural 1", 2: "Plural 2"},
                )
            ],
        ),
        (
            {
                "msgid_003": [
                    ["Translation 1", "Traduction 2"],
                    ["Plural 1-1", "Plural 2-1"],
                    ["Plural 2-1", "Plural 2-2"],
                ]
            },
            [
                POEntry(
                    msgid="msgid_003_000",
                    msgid_plural="msgid_003_000_plr",
                    msgstr="Translation 1",
                    msgstr_plural={
                        0: "Translation 1",
                        1: "Plural 1-1",
                        2: "Plural 2-1",
                    },
                ),
                POEntry(
                    msgid="msgid_003_001",
                    msgid_plural="msgid_003_001_plr",
                    msgstr="Traduction 2",
                    msgstr_plural={0: "Traduction 2", 1: "Plural 2-1", 2: "Plural 2-2"},
                ),
            ],
        ),
    ],
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
    "translations, expected_po_entries",
    [
        (
            {"msgid_001": [["Translation"]]},
            [POEntry(msgid="msgid_001", msgstr="Translation")],
        ),
        (
            {"msgid_004": [["Translation 1", "Translation 2"]]},
            [
                POEntry(msgid="msgid_004_000", msgstr="Translation 1"),
                POEntry(msgid="msgid_004_001", msgstr="Translation 2"),
            ],
        ),
        (
            {"msgid_002": [["Translation"], ["Plural 1"], ["Plural 2"]]},
            [
                POEntry(
                    msgid="msgid_002",
                    msgid_plural="msgid_002_plr",
                    msgstr="Translation",
                    msgstr_plural={0: "Translation", 1: "Plural 1", 2: "Plural 2"},
                )
            ],
        ),
        (
            {
                "msgid_003": [
                    ["Translation 1", "Traduction 2"],
                    ["Plural 1-1", "Plural 2-1"],
                    ["Plural 2-1", "Plural 2-2"],
                ]
            },
            [
                POEntry(
                    msgid="msgid_003_000",
                    msgid_plural="msgid_003_000_plr",
                    msgstr="Translation 1",
                    msgstr_plural={
                        0: "Translation 1",
                        1: "Plural 1-1",
                        2: "Plural 2-1",
                    },
                ),
                POEntry(
                    msgid="msgid_003_001",
                    msgid_plural="msgid_003_001_plr",
                    msgstr="Traduction 2",
                    msgstr_plural={0: "Traduction 2", 1: "Plural 2-1", 2: "Plural 2-2"},
                ),
            ],
        ),
    ],
)
def test_update_po_translations_with_entry(translations, expected_po_entries):
    po_file = POFile()
    for entry in expected_po_entries:
        po_file.append(entry)
    _update_po_translations(po_file, translations)
    assert len(po_file) == len(expected_po_entries)
    for entry, expected_entry in zip(po_file, expected_po_entries):
        assert entry.msgid == expected_entry.msgid
        assert entry.msgid_plural == expected_entry.msgid_plural
        assert entry.msgstr == expected_entry.msgstr
        if expected_entry.msgstr_plural:
            assert entry.msgstr_plural == expected_entry.msgstr_plural


@pytest.mark.parametrize(
    "module, domain, translations",
    [
        (
            "module-1",
            "domain-1",
            {
                "fr": {
                    "msgid_001": [["Traduction 1"]],
                    "msgid_002": [["Traduction 2"], ["Pluriel 1"], ["Pluriel 2"]],
                    "msgid_003": [
                        ["Traduction 31", "Traduction 32"],
                        ["Pluriel 1-31", "Pluriel 1-32"],
                        ["Pluriel 2-31", "Pluriel 2-32"],
                    ],
                },
                "fr-FR": {
                    "msgid_001": [["Traduction 1"]],
                    "msgid_002": [["Traduction 2"], ["Pluriel 1"], ["Pluriel 2"]],
                },
                "en": {
                    "msgid_001": [["Translation 1"]],
                    "msgid_002": [["Translation 2"], ["Plural 1"], ["Plural 2"]],
                },
                "es": {
                    "msgid_001": [["Traducción 1"]],
                    "msgid_002": [["Traducción 2"], ["Plural 1"], ["Plural 2"]],
                },
            },
        )
    ],
)
def test_add_translation_first_set(sample_repository, module, domain, translations):
    add_translation_set(sample_repository, module, domain, translations)

    repository_path = Path(sample_repository["base"])

    for lang, translation_data in translations.items():
        lang_path = repository_path / module / "locales" / lang / "LC_MESSAGES"
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


@pytest.mark.parametrize(
    "module, domain, translations, expected_json_content, expected_po_content, should_raise",
    [
        (
            "module-1",
            "domain-1",
            {
                "fr": {
                    "msgid_001": [["Nouvelle Traduction 1"]],
                    "msgid_002": [
                        ["Nouvelle Traduction 2"],
                        ["Nouveau Pluriel 1"],
                        ["Nouveau Pluriel 2"],
                    ],
                },
                "en": {
                    "msgid_001": [["Updated Translation 1"]],
                    "msgid_002": [
                        ["Updated Translation 2"],
                        ["Updated Plural 1"],
                        ["Updated Plural 2"],
                    ],
                },
            },
            {
                "fr": {
                    "msgid_001": [["Nouvelle Traduction 1"]],
                    "msgid_002": [
                        ["Nouvelle Traduction 2"],
                        ["Nouveau Pluriel 1"],
                        ["Nouveau Pluriel 2"],
                    ],
                },
                "en": {
                    "msgid_001": [["Updated Translation 1"]],
                    "msgid_002": [
                        ["Updated Translation 2"],
                        ["Updated Plural 1"],
                        ["Updated Plural 2"],
                    ],
                },
            },
            {
                "fr": [
                    ("msgid_001", "Nouvelle Traduction 1", None),
                    (
                        "msgid_002",
                        "Nouvelle Traduction 2",
                        {0: "Nouveau Pluriel 1", 1: "Nouveau Pluriel 2"},
                    ),
                ],
                "en": [
                    ("msgid_001", "Updated Translation 1", None),
                    (
                        "msgid_002",
                        "Updated Translation 2",
                        {0: "Updated Plural 1", 1: "Updated Plural 2"},
                    ),
                ],
            },
            False,
        ),
        (
            "module-1",
            "domain-1",
            {
                "fr": {
                    "msgid_001": [
                        ["Traduction 31", "Traduction 32"],
                        ["Pluriel 1-31", "Pluriel 1-32"],
                        ["Pluriel 2-31", "Pluriel 2-32"],
                    ],
                },
            },
            {
                "fr": {
                    "msgid_001": [
                        ["Traduction 31", "Traduction 32"],
                        ["Pluriel 1-31", "Pluriel 1-32"],
                        ["Pluriel 2-31", "Pluriel 2-32"],
                    ],
                    "msgid_002": [
                        ["Ancienne Traduction 2"],
                        ["Ancien Pluriel 1"],
                        ["Ancien Pluriel 2"],
                    ],
                },
            },
            {
                "fr": [
                    (
                        "msgid_001_000",
                        "Traduction 31",
                        {0: "Pluriel 1-31", 1: "Pluriel 2-31"},
                    ),
                    (
                        "msgid_001_001",
                        "Traduction 32",
                        {0: "Pluriel 1-32", 1: "Pluriel 2-32"},
                    ),
                    (
                        "msgid_002",
                        "Ancienne Traduction 2",
                        {0: "Ancien Pluriel 1", 1: "Ancien Pluriel 2"},
                    ),
                ],
            },
            False,
        ),
        (
            "module-1",
            "domain-1",
            {
                "fr": {
                    "msgid_004": [["Traduction inexistante"]],
                },
            },
            {},
            {},
            True,
        ),
    ],
)
def test_update_translation_first_set(
    sample_repository,
    module,
    domain,
    translations,
    expected_json_content,
    expected_po_content,
    should_raise,
):
    # Create initial JSON and PO files with some content
    repository_path = Path(sample_repository["base"])
    for lang in translations.keys():
        normalized_lang = lang.replace("-", "_")
        lang_path = (
            repository_path / module / "locales" / normalized_lang / "LC_MESSAGES"
        )
        lang_path.mkdir(parents=True, exist_ok=True)

        json_file_path = lang_path / f"{domain}.json"
        po_file_path = lang_path / f"{domain}.po"

        # Initialize with some existing translations
        initial_translations = {
            "msgid_001": [["Ancienne Traduction 1"]],
            "msgid_002": [
                ["Ancienne Traduction 2"],
                ["Ancien Pluriel 1"],
                ["Ancien Pluriel 2"],
            ],
        }
        with open(json_file_path, "w", encoding="utf-8") as json_file:
            json.dump(initial_translations, json_file)

        po_file = POFile()
        po_file.metadata = {
            "Project-Id-Version": "1.0",
            "POT-Creation-Date": "2023-01-01 12:00+0000",
            "PO-Revision-Date": "2023-01-01 12:00+0000",
            "Last-Translator": "you <you@example.com>",
            "Language-Team": "French <fr@li.org>",
            "Language": "fr",
            "MIME-Version": "1.0",
            "Content-Type": "text/plain; charset=utf-8",
            "Content-Transfer-Encoding": "8bit",
        }
        for msgid, msgs in initial_translations.items():
            po_entry = POEntry(msgid=msgid, msgstr=msgs[0][0])
            if len(msgs[0]) > 1:
                po_entry.msgstr_plural = {i: msgs[i][0] for i in range(1, len(msgs))}
            po_file.append(po_entry)
        po_file.save(str(po_file_path))

    # Test update translations
    if should_raise:
        with pytest.raises(KeyError):
            update_translation_set(sample_repository, module, domain, translations)
    else:
        update_translation_set(sample_repository, module, domain, translations)

        # Verify JSON content
        for lang, expected_content in expected_json_content.items():
            normalized_lang = lang.replace("-", "_")
            lang_path = (
                repository_path / module / "locales" / normalized_lang / "LC_MESSAGES"
            )
            json_file_path = lang_path / f"{domain}.json"

            with open(json_file_path, "r", encoding="utf-8") as json_file:
                saved_json_content = json.load(json_file)
                assert saved_json_content == expected_content

        # Verify PO content
        for lang, expected_content in expected_po_content.items():
            normalized_lang = lang.replace("-", "_")
            lang_path = (
                repository_path / module / "locales" / normalized_lang / "LC_MESSAGES"
            )
            po_file_path = lang_path / f"{domain}.po"

            po_file = POFile(str(po_file_path))
            for entry, (msgid, msgstr, msgstr_plural) in zip(po_file, expected_content):
                assert entry.msgid == msgid
                assert entry.msgstr == msgstr
                if msgstr_plural:
                    assert entry.msgstr_plural == msgstr_plural


@pytest.mark.parametrize(
    "msgids_to_remove, expected_remaining_entries",
    [
        ({("msgid_001", 1)}, ["msgid_002", "msgid_003_000", "msgid_003_001"]),
        ({("msgid_002", 1)}, ["msgid_001", "msgid_003_000", "msgid_003_001"]),
        ({("msgid_003", 2)}, ["msgid_001", "msgid_002"]),
        ({("msgid_001", 1), ("msgid_003", 2)}, ["msgid_002"]),
    ],
)
def test_remove_po_translations(
    sample_po_file, msgids_to_remove, expected_remaining_entries
):
    # Remove specified translations
    _remove_po_translations(sample_po_file, msgids_to_remove)

    # Verify remaining entries
    remaining_entries = [entry.msgid for entry in sample_po_file]
    assert remaining_entries == expected_remaining_entries


@pytest.mark.parametrize(
    "module, domain, translations, expected_json_content, expected_po_content",
    [
        (
            "module-1",
            "domain-1",
            {
                "es": {
                    "msgid_003": [
                        ["Traducción 31", "Option 32"],
                        ["Plural 1-31", "Option plural 1-32"],
                        ["Plural 2-31", "Option plural 2-32"],
                    ],
                },
            },
            {
                "fr": {
                    "msgid_001": [["Traduction 1"]],
                    "msgid_002": [["Traduction 2"], ["Pluriel 1"]],
                    "msgid_003": [
                        ["Traduction 31", "Option 32"],
                        ["Pluriel 1-31", "Pluriel Option 1-32"],
                        ["Pluriel 2-31", "Pluriel Option 2-32"],
                    ],
                    "msgid_004": [
                        ["Traduction 41", "Option 42"],
                        ["Pluriel 41", "Pluriel Option 42"],
                    ],
                    "msgid_005": [
                        ["Traduction 51", "Option 52", "Option 53"],
                        ["Pluriel 51-1", "Pluriel Option 52-1", "Pluriel Option 53-1"],
                        ["Pluriel 51-2", "Pluriel Option 52-2", "Pluriel Option 53-2"],
                    ],
                },
                "es": {
                    "msgid_001": [["Traducción 1"]],
                    "msgid_002": [["Traducción 2"], ["Plural 1"]],
                    "msgid_003": [
                        ["Traducción 31", "Option 32"],
                        ["Plural 1-31", "Option plural 1-32"],
                        ["Plural 2-31", "Option plural 2-32"],
                    ],
                },
            },
            {
                "fr": [
                    ("msgid_001", "Traduction 1", None),
                    ("msgid_002", "Traduction 2", {0: "Pluriel 1"}),
                    (
                        "msgid_003_000",
                        "Traduction 31",
                        {0: "Pluriel 1-31", 1: "Pluriel 2-31"},
                    ),
                    (
                        "msgid_003_001",
                        "Option 32",
                        {0: "Pluriel Option 1-32", 1: "Pluriel Option 2-32"},
                    ),
                    ("msgid_004_000", "Traduction 41", {0: "Pluriel 41"}),
                    ("msgid_004_001", "Option 42", {0: "Pluriel Option 42"}),
                    (
                        "msgid_005_000",
                        "Traduction 51",
                        {0: "Pluriel 51-1", 1: "Pluriel 51-2"},
                    ),
                    (
                        "msgid_005_001",
                        "Option 52",
                        {0: "Pluriel Option 52-1", 1: "Pluriel Option 52-2"},
                    ),
                    (
                        "msgid_005_002",
                        "Option 53",
                        {0: "Pluriel Option 53-1", 1: "Pluriel Option 53-2"},
                    ),
                ],
                "es": [
                    ("msgid_001", "Traducción 1", None),
                    ("msgid_002", "Traducción 2", {0: "Plural 1"}),
                    (
                        "msgid_003_000",
                        "Traducción 31",
                        {0: "Plural 1-31", 1: "Pluriel 2-31"},
                    ),
                    (
                        "mgsid_003_001",
                        "Option 32",
                        {0: "Option plural 1-32", 1: "Option plural 2-32"},
                    ),
                ],
            },
        ),
    ],
)
def test_add_translation_set(
    sample_file,
    module,
    domain,
    translations,
    expected_json_content,
    expected_po_content,
):
    add_translation_set(sample_file, module, domain, translations)

    repository_path = Path(sample_file["base"])

    for lang, expected_content in expected_json_content.items():
        lang_path = repository_path / module / "locales" / lang / "LC_MESSAGES"
        json_file_path = lang_path / f"{domain}.json"

        with open(json_file_path, "r", encoding="utf-8") as json_file:
            saved_json_content = json.load(json_file)
            assert saved_json_content == expected_content

    for lang, expected_content in expected_po_content.items():
        lang_path = repository_path / module / "locales" / lang / "LC_MESSAGES"
        po_file_path = lang_path / f"{domain}.po"

        po_file = POFile(str(po_file_path))
        for entry, (msgid, msgstr, msgstr_plural) in zip(po_file, expected_content):
            assert entry.msgid == msgid
            assert entry.msgstr == msgstr
            if msgstr_plural:
                assert entry.msgstr_plural == msgstr_plural


@pytest.mark.parametrize(
    "module, domain, translations, expected_json_content, expected_po_content, should_raise",
    [
        (
            "module-1",
            "domain-1",
            {
                "fr": {
                    "msgid_001": [["Nouvelle Traduction 1"]],
                    "msgid_002": [
                        ["Nouvelle Traduction 2"],
                        ["Nouveau Pluriel 1"],
                        ["Nouveau Pluriel 2"],
                    ],
                },
                "en": {
                    "msgid_001": [["Updated Translation 1"]],
                    "msgid_002": [
                        ["Updated Translation 2"],
                        ["Updated Plural 1"],
                        ["Updated Plural 2"],
                    ],
                },
            },
            {
                "fr": {
                    "msgid_001": [["Nouvelle Traduction 1"]],
                    "msgid_002": [
                        ["Nouvelle Traduction 2"],
                        ["Nouveau Pluriel 1"],
                        ["Nouveau Pluriel 2"],
                    ],
                    "msgid_003": [
                        ["Traduction 31", "Option 32"],
                        ["Pluriel 1-31", "Pluriel Option 1-32"],
                        ["Pluriel 2-31", "Pluriel Option 2-32"],
                    ],
                    "msgid_004": [
                        ["Traduction 41", "Option 42"],
                        ["Pluriel 41", "Pluriel Option 42"],
                    ],
                    "msgid_005": [
                        ["Traduction 51", "Option 52", "Option 53"],
                        ["Pluriel 51-1", "Pluriel Option 52-1", "Pluriel Option 53-1"],
                        ["Pluriel 51-2", "Pluriel Option 52-2", "Pluriel Option 53-2"],
                    ],
                },
                "en": {
                    "msgid_001": [["Updated Translation 1"]],
                    "msgid_002": [
                        ["Updated Translation 2"],
                        ["Updated Plural 1"],
                        ["Updated Plural 2"],
                    ],
                    "msgid_003": [
                        ["Translation 31", "Option 32"],
                        ["Plural 1-31", "Optional Plural 1-32"],
                        ["Plural 2-31", "Optional Plural 2-32"],
                    ],
                    "msgid_004": [
                        ["Translation 41", "Option 42"],
                        ["Plural 41", "Optional Plural 42"],
                    ],
                    "msgid_005": [
                        ["Translation 51", "Option 52", "Option 53"],
                        ["Plural 51-1", "Optional Plural 52-1", "Optional Plural 53-1"],
                        ["Plural 51-2", "Optional Plural 52-2", "Optional Plural 53-2"],
                    ],
                },
            },
            {
                "fr": [
                    ("msgid_001", "Nouvelle Traduction 1", None),
                    (
                        "msgid_002",
                        "Nouvelle Traduction 2",
                        {0: "Nouveau Pluriel 1", 1: "Nouveau Pluriel 2"},
                    ),
                    (
                        "msgid_003_000",
                        "Traduction 31",
                        {0: "Pluriel 1-31", 1: "Pluriel 2-31"},
                    ),
                    (
                        "msgid_003_001",
                        "Option 32",
                        {0: "Pluriel Option 1-32", 1: "Pluriel Option 2-32"},
                    ),
                    ("msgid_004_000", "Traduction 41", {0: "Pluriel 41"}),
                    ("msgid_004_001", "Option 42", {0: "Pluriel Option 42"}),
                    (
                        "msgid_005_000",
                        "Traduction 51",
                        {0: "Pluriel 51-1", 1: "Pluriel 51-2"},
                    ),
                    (
                        "msgid_005_001",
                        "Option 52",
                        {0: "Pluriel Option 52-1", 1: "Pluriel Option 52-2"},
                    ),
                    (
                        "msgid_005_002",
                        "Option 53",
                        {0: "Pluriel Option 53-1", 1: "Pluriel Option 53-2"},
                    ),
                ],
                "en": [
                    ("msgid_001", "Updated Translation 1", None),
                    (
                        "msgid_002",
                        "Updated Translation 2",
                        {0: "Updated Plural 1", 1: "Updated Plural 2"},
                    ),
                    (
                        "msgid_003_000",
                        "Translation 31",
                        {0: "Plural 1-31", 1: "Plural 2-31"},
                    ),
                    (
                        "msgid_003_001",
                        "Option 32",
                        {0: "Optional Plural 1-32", 1: "Optional Plural 2-32"},
                    ),
                    ("msgid_004_000", "Translation 41", {0: "Plural 41"}),
                    ("msgid_004_001", "Option 42", {0: "Optional Plural 42"}),
                    (
                        "msgid_005_000",
                        "Translation 51",
                        {0: "Plural 51-1", 1: "Plural 51-2"},
                    ),
                    (
                        "msgid_005_001",
                        "Option 52",
                        {0: "Optional Plural 52-1", 1: "Optional Plural 52-2"},
                    ),
                    (
                        "msgid_005_002",
                        "Option 53",
                        {0: "Optional Plural 53-1", 1: "Optional Plural 53-2"},
                    ),
                ],
            },
            False,
        ),
        (
            "module-1",
            "domain-1",
            {
                "fr": {
                    "msgid_003": [
                        ["Traduction 31", "Option 32"],
                        ["Pluriel 1-31", "Pluriel Option 1-32"],
                        ["Pluriel 2-31", "Pluriel Option 2-32"],
                    ],
                },
            },
            {
                "fr": {
                    "msgid_001": [["Traduction 1"]],
                    "msgid_002": [["Traduction 2"], ["Pluriel 1"]],
                    "msgid_003": [
                        ["Traduction 31", "Option 32"],
                        ["Pluriel 1-31", "Pluriel Option 1-32"],
                        ["Pluriel 2-31", "Pluriel Option 2-32"],
                    ],
                    "msgid_004": [
                        ["Traduction 41", "Option 42"],
                        ["Pluriel 41", "Pluriel Option 42"],
                    ],
                    "msgid_005": [
                        ["Traduction 51", "Option 52", "Option 53"],
                        ["Pluriel 51-1", "Pluriel Option 52-1", "Pluriel Option 53-1"],
                        ["Pluriel 51-2", "Pluriel Option 52-2", "Pluriel Option 53-2"],
                    ],
                },
            },
            {
                "fr": [
                    ("msgid_001", "Nouvelle Traduction 1", None),
                    (
                        "msgid_002",
                        "Nouvelle Traduction 2",
                        {0: "Nouveau Pluriel 1", 1: "Nouveau Pluriel 2"},
                    ),
                    (
                        "msgid_003_000",
                        "Traduction 31",
                        {0: "Pluriel 1-31", 1: "Pluriel 2-31"},
                    ),
                    (
                        "msgid_003_001",
                        "Option 32",
                        {0: "Pluriel Option 1-32", 1: "Pluriel Option 2-32"},
                    ),
                    ("msgid_004_000", "Traduction 41", {0: "Pluriel 41"}),
                    ("msgid_004_001", "Option 42", {0: "Pluriel Option 42"}),
                    (
                        "msgid_005_000",
                        "Traduction 51",
                        {0: "Pluriel 51-1", 1: "Pluriel 51-2"},
                    ),
                    (
                        "msgid_005_001",
                        "Option 52",
                        {0: "Pluriel Option 52-1", 1: "Pluriel Option 52-2"},
                    ),
                    (
                        "msgid_005_002",
                        "Option 53",
                        {0: "Pluriel Option 53-1", 1: "Pluriel Option 53-2"},
                    ),
                ],
            },
            False,
        ),
        (
            "module-1",
            "domain-1",
            {
                "fr": {
                    "msgid_007": [["Traduction inexistante"]],
                },
            },
            {},
            {},
            True,
        ),
    ],
)
def test_update_translation_set(
    sample_file,
    module,
    domain,
    translations,
    expected_json_content,
    expected_po_content,
    should_raise,
):
    # Test update translations
    if should_raise:
        with pytest.raises(KeyError):
            update_translation_set(sample_file, module, domain, translations)
    else:
        update_translation_set(sample_file, module, domain, translations)

        # Verify JSON content
        repository_path = Path(sample_file["base"])
        for lang, expected_content in expected_json_content.items():
            lang_path = repository_path / module / "locales" / lang / "LC_MESSAGES"
            json_file_path = lang_path / f"{domain}.json"

            with open(json_file_path, "r", encoding="utf-8") as json_file:
                saved_json_content = json.load(json_file)
                assert saved_json_content == expected_content

        # Verify PO content
        for lang, expected_content in expected_po_content.items():
            lang_path = repository_path / module / "locales" / lang / "LC_MESSAGES"
            po_file_path = lang_path / f"{domain}.po"

            po_file = POFile(str(po_file_path))
            for entry, (msgid, msgstr, msgstr_plural) in zip(po_file, expected_content):
                assert entry.msgid == msgid
                assert entry.msgstr == msgstr
                if msgstr_plural:
                    assert entry.msgstr_plural == msgstr_plural


@pytest.mark.parametrize(
    "module, domain, removed_translations, expected_json_content, expected_po_content",
    [
        (
            "module-1",
            "domain-1",
            {
                "fr": {
                    "msgid_001": [["Traduction 1"]],
                    "msgid_002": [["Traduction 2"], ["Pluriel 1"]],
                    "msgid_003": [
                        ["Traduction 31", "Option 32"],
                        ["Pluriel 1-31", "Pluriel Option 1-32"],
                        ["Pluriel 2-31", "Pluriel Option 2-32"],
                    ],
                    "msgid_004": [
                        ["Traduction 41", "Option 42"],
                        ["Pluriel 41", "Pluriel Option 42"],
                    ],
                    "msgid_005": [
                        ["Traduction 51", "Option 52", "Option 53"],
                        ["Pluriel 51-1", "Pluriel Option 52-1", "Pluriel Option 53-1"],
                        ["Pluriel 51-2", "Pluriel Option 52-2", "Pluriel Option 53-2"],
                    ],
                },
                "en": {
                    "msgid_001": [["Translation 1"]],
                    "msgid_002": [["Translation 2"], ["Plural 1"]],
                    "msgid_003": [
                        ["Translation 31", "Option 32"],
                        ["Plural 1-31", "Optional Plural 1-32"],
                        ["Plural 2-31", "Optional Plural 2-32"],
                    ],
                    "msgid_004": [
                        ["Translation 41", "Option 42"],
                        ["Plural 41", "Optional Plural 42"],
                    ],
                    "msgid_005": [
                        ["Translation 51", "Option 52", "Option 53"],
                        ["Plural 51-1", "Optional Plural 52-1", "Optional Plural 53-1"],
                        ["Plural 51-2", "Optional Plural 52-2", "Optional Plural 53-2"],
                    ],
                },
                "es": {
                    "msgid_001": [["Traducción 1"]],
                    "msgid_002": [["Traducción 2"], ["Plural 1"]],
                },
            },
            {
                "fr": {},
                "en": {},
                "es": {},
            },
            {
                "fr": [],
                "en": [],
                "es": [],
            },
        )
    ],
)
def test_remove_translation_set(
    sample_repository,
    sample_translations,
    module,
    domain,
    removed_translations,
    expected_json_content,
    expected_po_content,
):
    # Build content repository
    add_translation_set(sample_repository, module, domain, sample_translations)
    # Remove translations
    remove_translation_set(sample_repository, module, domain, removed_translations)

    # Verify JSON content
    repository_path = Path(sample_repository["base"])
    for lang, expected_content in expected_json_content.items():
        lang_path = repository_path / module / "locales" / lang / "LC_MESSAGES"
        json_file_path = lang_path / f"{domain}.json"

        with open(json_file_path, "r", encoding="utf-8") as json_file:
            saved_json_content = json.load(json_file)
            assert saved_json_content == expected_content

    # Verify PO content
    for lang, expected_content in expected_po_content.items():
        lang_path = repository_path / module / "locales" / lang / "LC_MESSAGES"
        po_file_path = lang_path / f"{domain}.po"

        po_file = POFile(str(po_file_path))
        remaining_entries = [
            (entry.msgid, entry.msgstr, entry.msgstr_plural) for entry in po_file
        ]
        assert remaining_entries == expected_content
