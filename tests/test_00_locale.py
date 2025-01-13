import pytest
from i18n_tools.locale import normalize_language_tag, is_valid_language_tag


@pytest.mark.parametrize("tag, result", [
    ("123", False),
    ("English", False),
    ("a", False,),
    ("de-1996", True),
    ("en", True),
    ("en-Latn-US", True),
    ("en-US", True),
    ("en-US-!", False),
    ("en-x-", False),
    ("en-x-private", True),
    ("en-x-private-",False),
    ("eng-Latin", False),
    ("es-419", True),
    ("fr", True),
    ("fr+FR", False),
    ("fr-CA", True),
    ("fr-FR", True),
    ("fr-fr", True),
    ("francais", False),
    ("frç", False),
    ("ja-Latn-hepburn-heploc", True),
    ("ja.Latn/hepburn@heploc", False),
    ("sl-rozaj-biske-1994", True),
    ("zh-Hans-1234", False),
    ("zh-Hans-CN", True),
    ("zh-Hant", True),
    ("zh-Latn-pinyin", True)
])
def test_is_valid_language_tag(tag, result):
    assert is_valid_language_tag(tag) == result


@pytest.mark.parametrize("tag, result", [
    ("En", "en"),
    ("FR", "fr"),
    ("fr-fr", "fr-FR"),
    ("FR-ca", "fr-CA"),
    ("EN-IE", "en-IE"),
    ("ja-latn-Hepburn-Heploc", "ja-Latn-hepburn-heploc"),
])
def test_normalize_language_tag(tag, result):
    assert normalize_language_tag(tag) == result

def test_is_valid_language_tag_invalid():
    with pytest.raises(ValueError):
        normalize_language_tag("ja.Latn/hepburn@heploc")