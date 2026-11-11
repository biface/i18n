import pytest

from i18n_tools import __version__
from i18n_tools.models import Declension
from i18n_tools.models import Message as MessageModel


def _metadata(language: str = "en") -> dict:
    return {
        "version": __version__,
        "language": language,
        "locations": [],
        "flags": ["python-format"],
        "user_comments": [],
        "auto_comments": [],
    }


@pytest.fixture
def simple_message() -> MessageModel:
    """No variant, no plural: exercises the plain path (row 0, column 0)."""
    return MessageModel(
        id="greet", principal=Declension("Hello {name}"), metadata=_metadata()
    )


@pytest.fixture
def step1_message() -> MessageModel:
    """Every cell requested is directly present — no fallback needed."""
    return MessageModel(
        id="cart",
        principal=Declension("{count} item", ("{count} items",)),
        variants=[Declension("{count} item (formal)", ("{count} items (formal)",))],
        metadata=_metadata(),
    )


@pytest.fixture
def step2_message() -> MessageModel:
    """
    Row 1 exists, but variant 1 has no plural: falls back to
    messages[1][0] (the principal plural).
    """
    return MessageModel(
        id="cart",
        principal=Declension("{count} item", ("{count} items",)),
        variants=[Declension("{count} item (formal)")],
        metadata=_metadata(),
    )


@pytest.fixture
def step3_message() -> MessageModel:
    """
    Row 1 exists but both its cells are empty markers: falls through to
    the singular of the variant, messages[0][variant].
    """
    return MessageModel(
        id="cart",
        principal=Declension("{count} item", ("",)),
        variants=[Declension("{count} item (formal)")],
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
        principal=Declension("{count} item (singular main)", ("",)),
        variants=[Declension("")],
        metadata=_metadata(),
    )
