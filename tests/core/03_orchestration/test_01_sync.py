"""Tests for check_repository() — sync.py (biface/i18n#30).

No test previously covered sync.py at all.
"""

import pytest

from i18n_tools.loaders.loader import build_book_filename
from i18n_tools.sync import check_repository


class TestCheckRepository:
    def test_pot_created_once_per_domain_in_templates(self, tmp_path):
        """The bug: .pot was created inside each language's LC_MESSAGES/
        (duplicated per language) instead of once per domain in
        templates/."""
        domains = {"module_a": ["usage"]}
        languages = {
            "source": "en",
            "hierarchy": {"en": ["en-US"], "fr": ["fr-FR"]},
        }

        check_repository(str(tmp_path), domains, languages)

        templates_dir = tmp_path / "module_a" / "locales" / "templates"
        assert (templates_dir / "usage.pot").exists()

    def test_pot_not_duplicated_in_lc_messages(self, tmp_path):
        domains = {"module_a": ["usage"]}
        languages = {
            "source": "en",
            "hierarchy": {"en": ["en-US"], "fr": ["fr-FR"]},
        }

        check_repository(str(tmp_path), domains, languages)

        for lang in ("en", "en-US", "fr-FR"):
            lc_messages = tmp_path / "module_a" / "locales" / lang / "LC_MESSAGES"
            assert not (lc_messages / "usage.pot").exists()

    def test_json_and_po_created_per_language(self, tmp_path):
        """The bug: files were created as `{domain}.json`, not matching
        Book/build_book_filename's actual DD-34 `.i18t`-suffixed naming
        (`{domain}.json.i18t`) — Book.load() could never find them."""
        domains = {"module_a": ["usage"]}
        languages = {
            "source": "en",
            "hierarchy": {"en": ["en-US"], "fr": ["fr-FR"]},
        }

        check_repository(str(tmp_path), domains, languages)

        _, expected_filename = build_book_filename("usage")
        for lang in ("en", "en-US", "fr-FR"):
            lc_messages = tmp_path / "module_a" / "locales" / lang / "LC_MESSAGES"
            assert (lc_messages / expected_filename).exists()
            assert (lc_messages / "usage.po").exists()

    def test_hierarchy_parent_key_itself_gets_synced(self, tmp_path):
        """The bug: only hierarchy *values* were synced (e.g. fr-FR,
        fr-BE), never the parent *key* itself (e.g. fr) — even though
        `fr` is a legitimate fallback language in its own right, and
        core.load_corpus() (via locale.get_all_languages()) expects a
        file for it too."""
        domains = {"module_a": ["usage"]}
        languages = {
            "source": "en",
            "hierarchy": {"fr": ["fr-FR", "fr-BE"]},
        }

        check_repository(str(tmp_path), domains, languages)

        for lang in ("en", "fr", "fr-FR", "fr-BE"):
            lc_messages = tmp_path / "module_a" / "locales" / lang / "LC_MESSAGES"
            assert lc_messages.is_dir(), f"missing directory for {lang}"

    def test_rejects_relative_tld(self, tmp_path):
        with pytest.raises(ValueError, match="must be absolute"):
            check_repository("relative/path", {}, {"source": "en", "hierarchy": {}})

    def test_rejects_nonexistent_tld(self, tmp_path):
        missing = tmp_path / "does-not-exist"
        with pytest.raises(FileNotFoundError, match="does not exist"):
            check_repository(str(missing), {}, {"source": "en", "hierarchy": {}})
