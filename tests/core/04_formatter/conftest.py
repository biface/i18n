import pytest

from i18n_tools import __version__
from i18n_tools.models import Message as MessageModel


def _metadata(language: str = "en") -> dict:
    return {
        "version": __version__,
        "language": language,
        "location": [],
        "flags": ["python-format"],
        "user_comments": [],
        "auto_comments": [],
        "count": {"singular": 0, "plurals": []},
    }


@pytest.fixture
def simple_message() -> MessageModel:
    """No alternatives, no plurals: exercises the plain path (row0/col0)."""
    return MessageModel(
        id="greet",
        default="Hello {name}",
        metadata=_metadata(),
    )


@pytest.fixture
def step1_message() -> MessageModel:
    """Every cell requested is directly present — no fallback needed."""
    return MessageModel(
        id="cart",
        default="{count} item",
        options={1: "{count} item (formal)"},
        default_plurals={1: "{count} items"},
        options_plurals={1: {1: "{count} items (formal)"}},
        metadata=_metadata(),
    )


@pytest.fixture
def step2_message() -> MessageModel:
    """
    Row 1 exists, but options_plurals[1][1] is absent: falls back to
    messages[1][0] (default_plurals[1]).
    """
    return MessageModel(
        id="cart",
        default="{count} item",
        options={1: "{count} item (formal)"},
        default_plurals={1: "{count} items"},
        options_plurals={1: {}},
        metadata=_metadata(),
    )


@pytest.fixture
def step3_message() -> MessageModel:
    """
    Row 1 exists (key present) but both its cells are empty markers:
    falls through to messages[0][alternative] (options[1]).
    """
    return MessageModel(
        id="cart",
        default="{count} item",
        options={1: "{count} item (formal)"},
        default_plurals={1: ""},
        options_plurals={1: {}},
        metadata=_metadata(),
    )


@pytest.fixture
def step4_message() -> MessageModel:
    """
    Row 1 exists but everything except messages[0][0] is an empty
    marker: falls all the way through to the singular main text.
    """
    return MessageModel(
        id="cart",
        default="{count} item (singular main)",
        options={1: ""},
        default_plurals={1: ""},
        options_plurals={1: {}},
        metadata=_metadata(),
    )
