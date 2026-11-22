import pytest

from i18n_tools.models import Message as MessageModel


@pytest.fixture
def simple_message() -> MessageModel:
    """No variant, no plural: exercises the plain path (row 0, column 0)."""
    return MessageModel("greet", "Hello {name}", flags=["python-format"])


@pytest.fixture
def step1_message() -> MessageModel:
    """Every cell requested is directly present — no fallback needed."""
    return MessageModel(
        "cart",
        "{count} item",
        plurals=["{count} items"],
        alternatives=[["{count} item (formal)", "{count} items (formal)"]],
        flags=["python-format"],
    )


@pytest.fixture
def step2_message() -> MessageModel:
    """
    Row 1 exists, but variant 1 has no plural: falls back to
    messages[1][0] (the principal plural).
    """
    return MessageModel(
        "cart",
        "{count} item",
        plurals=["{count} items"],
        alternatives=[["{count} item (formal)"]],
        flags=["python-format"],
    )


@pytest.fixture
def step3_message() -> MessageModel:
    """
    Row 1 exists but both its cells are empty markers: falls through to
    the singular of the variant, messages[0][variant].
    """
    return MessageModel(
        "cart",
        "{count} item",
        plurals=[""],
        alternatives=[["{count} item (formal)"]],
        flags=["python-format"],
    )


@pytest.fixture
def step4_message() -> MessageModel:
    """
    Row 1 exists but everything except messages[0][0] is an empty
    marker: falls all the way through to the singular main text.
    """
    return MessageModel(
        "cart",
        "{count} item (singular main)",
        plurals=[""],
        alternatives=[[""]],
        flags=["python-format"],
    )
