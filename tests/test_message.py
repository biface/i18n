"""
Test module for the Message class in the formatter module.
"""

import pytest

from i18n_tools.models import Message


def test_message_creation():
    """Test creating a Message instance."""
    message = Message(
        message_id="greeting",
        translation="Hello, {name}!",
        alternatives={1: "Hi, {name}!"},
        plural_forms={1: "Hello, {count} {name}s!"},
        context="A greeting message",
        metadata={"locations": ["file.py:10"]},
    )

    assert message.message_id == "greeting"
    assert message.translation == "Hello, {name}!"
    assert message.alternatives == {1: "Hi, {name}!"}
    assert message.plural_forms == {1: "Hello, {count} {name}s!"}
    assert message.context == "A greeting message"
    assert message.metadata == {"locations": ["file.py:10"]}


def test_message_format():
    """Test formatting a message with variables."""
    message = Message(
        message_id="greeting",
        translation="Hello, {name}!",
        alternatives={1: "Hi, {name}!"},
        plural_forms={1: "Hello, {count} {name}s!"},
        alternative_plural_forms={1: {1: "Hi, {count} {name}s!"}},
    )

    # Test formatting the main translation
    assert message.format(name="John") == "Hello, John!"

    # Test formatting an alternative
    assert message.format(alternative=1, name="John") == "Hi, John!"

    # Test formatting a plural form
    assert message.format(plural_index=1, name="user", count=5) == "Hello, 5 users!"

    # Test formatting an alternative plural form
    assert (
        message.format(alternative=1, plural_index=1, name="user", count=3)
        == "Hi, 3 users!"
    )

    # Test missing variable
    with pytest.raises(KeyError):
        message.format()


def test_message_conversion():
    """Test converting a message to different formats."""
    message = Message(
        message_id="greeting",
        translation="Hello, {name}!",
        alternatives={1: "Hi, {name}!"},
        plural_forms={1: "Hello, {count} {name}s!"},
    )

    # Test conversion to unified format
    unified = message.to_unified_format()
    assert unified["translation"] == "Hello, {name}!"
    assert unified["alternatives"] == {"1": "Hi, {name}!"}
    assert unified["plural_forms"] == {"1": "Hello, {count} {name}s!"}

    # Test conversion to i18n_tools format
    i18n_tools_format = message.to_i18n_tools_format()
    assert "messages" in i18n_tools_format
    assert "metadata" in i18n_tools_format
    assert i18n_tools_format["messages"][0][0] == "Hello, {name}!"
    assert i18n_tools_format["messages"][0][1] == "Hi, {name}!"
    assert i18n_tools_format["messages"][1][0] == "Hello, {count} {name}s!"


def test_message_from_unified_format():
    """Test creating a Message from unified format."""
    unified_entry = {
        "translation": "Hello, {name}!",
        "alternatives": {"1": "Hi, {name}!"},
        "plural_forms": {"1": "Hello, {count} {name}s!"},
        "context": "A greeting message",
        "metadata": {"locations": ["file.py:10"]},
    }

    message = Message.from_unified_format("greeting", unified_entry)

    assert message.message_id == "greeting"
    assert message.translation == "Hello, {name}!"
    assert message.alternatives == {1: "Hi, {name}!"}
    assert message.plural_forms == {1: "Hello, {count} {name}s!"}
    assert message.context == "A greeting message"
    assert message.metadata == {"locations": ["file.py:10"]}
