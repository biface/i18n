import os
from pathlib import Path

import pytest

from i18n_tools.sync import check_repository


@pytest.fixture
def setup_repository(tmp_path):
    """Fixture to set up a temporary directory for testing."""
    return tmp_path / "repository"


@pytest.fixture
def domains():
    """Fixture for the domains dictionary."""
    return {
        "mod-1": ["errors", "information"],
        "mod-2/pkg-1": ["usages", "information"],
    }


@pytest.fixture
def languages():
    """Fixture for the languages dictionary."""
    return {
        "source": "en",
        "hierarchy": {
            "fr": ["fr-FR", "fr-BE", "fr-CA"],
            "en": ["en-IE", "en-US", "en-GB"],
        },
        "fallback": "fr",
    }


def test_check_repository_raises_value_error_if_not_absolute(
    setup_repository, domains, languages
):
    tld = "relative/path"

    with pytest.raises(ValueError):
        check_repository(tld, domains, languages)


def test_check_repository_raises_file_not_found_error_if_not_exists(
    tmp_path, domains, languages
):
    tld = str(tmp_path / "nonexistent")

    with pytest.raises(FileNotFoundError):
        check_repository(tld, domains, languages)


def test_check_repository_creates_files(setup_repository, domains, languages):
    setup_repository.mkdir(parents=True)
    tld = str(setup_repository)

    # Run the function to create the files
    check_repository(tld, domains, languages)

    # Check if the directories and files are created
    for module, domain_list in domains.items():
        module_path = Path(tld) / module / "locales"
        assert module_path.exists()

        for domain in domain_list:
            for lang in (
                languages["hierarchy"]["fr"]
                + languages["hierarchy"]["en"]
                + [languages["source"]]
            ):
                lang_path = module_path / lang / "LC_MESSAGES"
                assert lang_path.exists()

                json_file = lang_path / f"{domain}.json"
                pot_file = lang_path / f"{domain}.pot"
                po_file = lang_path / f"{domain}.po"
                assert json_file.exists()
                assert pot_file.exists()
                assert po_file.exists()


def test_check_repository_does_not_recreate_existing_files(
    setup_repository, domains, languages
):
    setup_repository.mkdir(parents=True)
    tld = str(setup_repository)

    # Create some existing files
    module = "mod-1"
    domain = "errors"
    lang = "fr-FR"
    module_path = Path(tld) / module / "locales"
    lang_path = module_path / lang / "LC_MESSAGES"
    lang_path.mkdir(parents=True, exist_ok=True)

    json_file = lang_path / f"{domain}.json"
    pot_file = lang_path / f"{domain}.pot"
    po_file = lang_path / f"{domain}.po"

    json_file.touch()
    pot_file.touch()
    po_file.touch()

    # Get the modification times before running the function
    json_mtime = json_file.stat().st_mtime
    pot_mtime = pot_file.stat().st_mtime
    po_mtime = po_file.stat().st_mtime

    # Run the function
    check_repository(tld, domains, languages)

    # Check that the modification times have not changed
    assert json_file.stat().st_mtime == json_mtime
    assert pot_file.stat().st_mtime == pot_mtime
    assert po_file.stat().st_mtime == po_mtime
