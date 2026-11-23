"""Tests for the JSON value aliases (``_json.py``) and the 3.11 fallback of
``TypeAliasType`` (``_compat.py``)."""

import pytest

from i18n_tools._compat import _TypeAliasType
from i18n_tools._json import JSONInput, JSONValue


class TestJSONAliases:
    @pytest.mark.parametrize(
        "alias, name", [(JSONValue, "JSONValue"), (JSONInput, "JSONInput")]
    )
    def test_alias_keeps_its_name(self, alias, name):
        assert alias.__name__ == name
        assert repr(alias) == name


class TestTypeAliasFallback:
    def test_keeps_name_and_value(self):
        alias = _TypeAliasType("Pair", tuple[int, int])
        assert alias.__name__ == "Pair"
        assert alias.__value__ == tuple[int, int]

    def test_shows_its_name(self):
        assert repr(_TypeAliasType("Pair", tuple[int, int])) == "Pair"

    def test_supports_no_type_operation(self):
        alias = _TypeAliasType("Pair", tuple[int, int])
        with pytest.raises(TypeError):
            _ = alias | int  # pyright: ignore[reportOperatorIssue]
