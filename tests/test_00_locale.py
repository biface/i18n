import pytest
from i18n_tools.locale import (
    normalize_language_tag,
    is_valid_language_tag,
    validate_and_normalize_language_tags,
)


@pytest.mark.parametrize(
    "tag, result",
    [
        ("123", False),
        ("English", False),
        (
            "a",
            False,
        ),
        ("de-1996", True),
        ("en", True),
        ("en-Latn-US", True),
        ("en-US", True),
        ("en-US-!", False),
        ("en-x-", False),
        ("en-x-private", True),
        ("en-x-private-", False),
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
        ("zh-Latn-pinyin", True),
    ],
)
def test_is_valid_language_tag(tag, result):
    assert is_valid_language_tag(tag) == result


@pytest.mark.parametrize(
    "tag, result",
    [
        ("En", "en"),
        ("FR", "fr"),
        ("fr-fr", "fr-FR"),
        ("FR-ca", "fr-CA"),
        ("EN-IE", "en-IE"),
        ("ja-latn-Hepburn-Heploc", "ja-Latn-hepburn-heploc"),
    ],
)
def test_normalize_language_tag(tag, result):
    assert normalize_language_tag(tag) == result


def test_is_valid_language_tag_invalid():
    with pytest.raises(ValueError):
        normalize_language_tag("ja.Latn/hepburn@heploc")


@pytest.mark.parametrize(
    "tags, expected",
    [
        (
            ["en", "FR", "es-MX", "zh-Hans", "de-AT"],
            ["en", "fr", "es-MX", "zh-Hans", "de-AT"],
        ),  # Valid
        (["EN", "fr", "ES-mx"], ["en", "fr", "es-MX"]),  # Casse
        (["pt-BR", "ja", "ko"], ["pt-BR", "ja", "ko"]),  # Well formed
    ],
)
def test_validate_and_normalize_language_tags_valid(tags, expected):
    result = validate_and_normalize_language_tags(tags)
    assert result == expected, f"La normalisation a échoué pour {tags}"


@pytest.mark.parametrize(
    "tags, invalid_tag",
    [
        (["en", "xyz", "es-MX"], "xyz"),  # 'xyz' est invalide
        (["123", "fr", "zh-Hans"], "123"),  # '123' est invalide
        (["en-US", "invalid-tag", "de"], "invalid-tag"),  # 'invalid-tag' est invalide
    ],
)
def test_validate_and_normalize_language_tags_invalid(tags, invalid_tag):
    with pytest.raises(ValueError, match=f"Invalid language tag: {invalid_tag}"):
        validate_and_normalize_language_tags(tags)
