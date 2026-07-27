"""
Test module for resolve() in i18n-tools/fallback
"""

import pytest

from i18n_tools.fallback import resolve
from i18n_tools.models.repository import Repository


@pytest.fixture
def repository_with_hierarchy() -> Repository:
    repository = Repository()
    repository.hierarchy = {"fr": ["fr-FR", "fr-BE"], "en": ["en-US"]}
    repository.fallback = "en"
    return repository


@pytest.fixture
def empty_repository() -> Repository:
    return Repository()


class TestResolveWithHierarchyAndFallback:
    @pytest.mark.parametrize(
        "lang, expected",
        [
            # Requested language absent, hierarchy + global fallback both apply
            ("fr-CH", ["fr-CH", "fr", "fr-FR", "fr-BE", "en", "en-US"]),
            # Requested tag is already a parent key in hierarchy
            ("fr", ["fr", "fr-FR", "fr-BE", "en", "en-US"]),
            # Requested tag is already a variant listed under its own parent
            ("fr-FR", ["fr-FR", "fr", "fr-BE", "en", "en-US"]),
            # Requested language has no hierarchy entry at all — only the
            # global fallback and its variants apply
            ("de", ["de", "en", "en-US"]),
            # Requested tag's parent IS the global fallback language itself
            ("en-GB", ["en-GB", "en", "en-US"]),
        ],
    )
    def test_resolve_chain(self, repository_with_hierarchy, lang, expected):
        assert resolve(lang, repository_with_hierarchy) == expected


class TestResolveWithoutConfiguration:
    def test_resolve_no_hierarchy_no_fallback_keeps_parent_only(self, empty_repository):
        assert resolve("fr-CH", empty_repository) == ["fr-CH", "fr"]

    def test_resolve_base_language_alone_returns_itself_only(self, empty_repository):
        assert resolve("en", empty_repository) == ["en"]


class TestResolveInvariants:
    def test_resolve_never_repeats_a_tag(self, repository_with_hierarchy):
        chain = resolve("en-GB", repository_with_hierarchy)
        assert len(chain) == len(set(chain))

    def test_resolve_starts_with_normalized_requested_language(
        self, repository_with_hierarchy
    ):
        assert resolve("fr-ch", repository_with_hierarchy)[0] == "fr-CH"

    def test_resolve_returns_a_new_list_each_call(self, repository_with_hierarchy):
        first = resolve("fr-CH", repository_with_hierarchy)
        first.append("tampered")
        second = resolve("fr-CH", repository_with_hierarchy)
        assert "tampered" not in second


class TestResolveInvalidInput:
    def test_resolve_raises_on_invalid_tag(self, empty_repository):
        with pytest.raises(ValueError, match="Invalid language tag"):
            resolve("!!!not-valid###", empty_repository)
