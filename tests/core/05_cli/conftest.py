import pytest

from i18n_tools.config import Config
from i18n_tools.models.corpus import Book, Message
from i18n_tools.patterns import Singleton


@pytest.fixture
def isolated_config_singleton():
    """
    Temporarily clears the Config singleton so a test can construct one
    of its own bound to a specific config file, then restores whatever
    instance (if any) existed before — 09_config inherits the Singleton
    from 01_loader and must see it unchanged, regardless of what runs
    in between (see tests/conftest.py's "TEST EXECUTION ORDER" note).
    """
    saved = Singleton._instances.pop(Config, None)
    try:
        yield
    finally:
        Singleton._instances.pop(Config, None)
        if saved is not None:
            Singleton._instances[Config] = saved


@pytest.fixture
def i18t_file(tmp_path):
    """
    A real, on-disk .i18t file under a DD-12-compliant
    <lang>/LC_MESSAGES/<domain>.<format>.i18t layout, with one message.
    """
    directory = tmp_path / "fr-FR" / "LC_MESSAGES"
    directory.mkdir(parents=True)

    book = Book(language="fr-FR", domain="messages")
    message = Message(
        id="greet",
        default="Bonjour",
        metadata={
            "version": "0.9.0",
            "language": "fr-FR",
            "location": [],
            "flags": [],
            "user_comments": [],
            "auto_comments": [],
            "count": {"singular": 0, "plurals": []},
        },
    )
    book.add("messages", [message])
    book.save(str(directory))

    return str(directory / book.filename)


@pytest.fixture
def template_i18t_file(tmp_path):
    """A .i18t file sitting directly under templates/ — no language."""
    directory = tmp_path / "templates"
    directory.mkdir(parents=True)
    file_path = directory / "messages.json.i18t"
    file_path.write_text("{}")
    return str(file_path)


@pytest.fixture
def sync_config_file(tmp_path):
    """A minimal, valid application configuration file for `sync`."""
    repository_root = tmp_path / "repo"
    repository_root.mkdir()
    config_file = tmp_path / "i18n-tools.yaml"
    config_file.write_text(
        "configuration: application\n"
        "application:\n"
        "  paths:\n"
        f"    repository: {repository_root}\n"
        "  domains:\n"
        "    app:\n"
        "      - messages\n"
        "  languages:\n"
        "    source: en\n"
        "    hierarchy: {}\n"
    )
    return str(config_file), str(repository_root)
