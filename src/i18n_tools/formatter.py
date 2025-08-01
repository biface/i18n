"""
Formatter Module
================

This module is responsible for constructing messages to be added to a translation dictionary, transcribing data supplied by converters, and formatting them into strings for error messages.

It also publishes messages in i18next mode using the appropriate APIs.

Main responsibilities:
    - Build a message to be stored in a translation dictionary
    - Transcribe and format data from converters.
    - Publish messages in i18next mode using appropriate APIs.

"""

from .models import Corpus, Message


def publish(message: Message) -> str:
    """
    Format a message using the appropriate format.
    """
    try:
        return message.format()
    except Exception as e:
        raise e
