"""
Minimal test file for Book model using shared fixtures from tests/models/conftest.py
"""

import pytest

# Using fixtures: fr_fr_book, en_us_book, en_gb_book, it_it_book from local conftest.py


@pytest.mark.parametrize("book", ["fr_fr_book", "en_us_book", "en_gb_book", "it_it_book"]) 
def test_book(book, request):
    book = request.getfixturevalue(book)
    for id, message in book.messages.items():
        assert id == message.id
    assert len(book.messages) == 10
