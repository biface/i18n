import pytest
from pathlib import Path
from polib import pofile
from i18n_tools.converter import _initialize_pot_file, populate_pot_files


@pytest.fixture
def setup_repository(tmp_path):
    """Fixture to set up a temporary repository directory for testing."""
    repo_path = tmp_path / "repository"
    repo_path.mkdir()
    return repo_path


@pytest.fixture
def authors():
    """Fixture for the authors dictionary."""
    return {
        "author1": {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "languages": ["en", "fr"],
        },
        "author2": {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane.smith@example.com",
            "languages": ["fr-FR", "fr-BE"],
        },
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


@pytest.fixture
def domains():
    """Fixture for the domains dictionary."""
    return {
        "mod-1": ["errors", "information"],
        "mod-2/pkg-1": ["usages", "information"],
    }


@pytest.fixture
def config(setup_repository):
    """Fixture for the config dictionary."""
    return {"base": str(setup_repository), "modules": ["mod-1", "mod-2/pkg-1"]}


def test_initialize_pot_file(setup_repository, authors):
    domain = "errors"
    language = "en"
    pot_file_path = setup_repository / f"{domain}.pot"
    _initialize_pot_file(str(pot_file_path), domain, authors, language)

    # Load the .pot file and check its content
    pot_file = pofile(str(pot_file_path))
    assert len(pot_file) == 1
    for entry in pot_file:
        assert "Translation by" in entry.msgid


def test_initialize_pot_file_without_author(setup_repository, authors):
    domain = "errors"

    # Test for a language not associated with the author
    language = "fr-CA"
    pot_file_path = setup_repository / f"{domain}-fr.pot"
    _initialize_pot_file(str(pot_file_path), domain, authors, language)

    # Load the .pot file and check its content
    pot_file = pofile(str(pot_file_path))
    assert len(pot_file) == 0  # No authors should be included for "fr-FR"


def test_populate_pot_files_raises_value_error_if_not_absolute(
    setup_repository, domains, languages, authors
):
    config = {"base": "relative/path", "modules": ["mod-1", "mod-2/pkg-1", "mod-3"]}

    with pytest.raises(ValueError):
        populate_pot_files(config, domains, languages, authors)


def test_populate_pot_files_skips_missing_module(
    setup_repository, config, domains, languages, authors
):
    # Run the function to populate the .pot files
    populate_pot_files(config, domains, languages, authors)

    # Check that directories and files are created for valid modules
    for module in ["mod-1", "mod-2/pkg-1"]:
        module_path = Path(config["base"]) / module / "locales"
        assert module_path.exists()

    # Check that no directories or files are created for the invalid module
    invalid_module_path = Path(config["base"]) / "mod-3"
    assert not invalid_module_path.exists()


@pytest.mark.parametrize(
    "language, expected_authors",
    [
        ("en", ["John Doe"]),
        ("fr", ["John Doe"]),
        ("fr-FR", ["Jane Smith"]),
        ("fr-BE", ["Jane Smith"]),
        ("en-US", []),
        ("fr-CA", []),
    ],
)
def test_author_pot_file(setup_repository, authors, language, expected_authors):
    domain = "errors"
    pot_file_path = setup_repository / f"{domain}_{language}.pot"
    _initialize_pot_file(str(pot_file_path), domain, authors, language)

    # Load the .pot file and check its content
    pot_file = pofile(str(pot_file_path))
    assert len(pot_file) == len(expected_authors)
    for entry in pot_file:
        assert any(author in entry.msgid for author in expected_authors)


@pytest.mark.parametrize(
    "module, expected_domains",
    [("mod-1", ["errors", "information"]), ("mod-2/pkg-1", ["usages", "information"])],
)
def test_populate_pot_files(
    setup_repository, config, domains, languages, authors, module, expected_domains
):
    # Ensure the config only includes the module being tested
    config["modules"] = [module]

    # Run the function to populate the .pot files
    populate_pot_files(config, domains, languages, authors)

    # Check if the directories and files are created
    module_path = Path(config["base"]) / module / "locales"
    assert module_path.exists()

    for domain in expected_domains:
        for lang in languages["hierarchy"][languages["source"]] + [languages["source"]]:
            lang_path = module_path / lang / "LC_MESSAGES"
            assert lang_path.exists()

            pot_file_path = lang_path / f"{domain}.pot"
            assert pot_file_path.exists()

            # Load the .pot file and check its content
            pot_file = pofile(str(pot_file_path))
            assert len(pot_file) == len(
                [author for author in authors.values() if lang in author["languages"]]
            )
