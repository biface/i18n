import pytest
from i18n_tools.locale import normalize_language_tag, is_valid_language_tag


@pytest.mark.parametrize("tag, result", [
    ("en", True),
    ("AbsconsLanguage", False),
    ("fr", True),
    ("fr-FR", True),
    ("fr+FR", False),
    ("ja-Latn-hepburn-heploc", True),
    ("ja.Latn/hepburn@heploc", False),
    ("zh-Latn-pinyin", True)
])
def test_is_valid_language_tag(tag, result):
    assert is_valid_language_tag(tag) == result


@pytest.mark.parametrize("tag, result", [
    ("En", "en"),
    ("FR", "fr"),
    ("fr-fr", "fr-FR"),
    ("ja-latn-Hepburn-Heploc", "ja-Latn-hepburn-heploc"),
])
def test_normalize_language_tag(tag, result):
    assert normalize_language_tag(tag) == result

def test_is_valid_language_tag_invalid():
    with pytest.raises(ValueError):
        normalize_language_tag("ja.Latn/hepburn@heploc")