"""Tests for check_repository() — sync.py (biface/i18n#30).

No test previously covered sync.py at all.
"""

import pytest

from i18n_tools.sync import check_repository


class TestCheckRepository:
    def test_pot_created_once_per_domain_in_templates(self, tmp_path):
        """The bug: .pot was created inside each language's LC_MESSAGES/
        (duplicated per language) instead of once per domain in
        templates/ (DD-12, repository.rst)."""
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
        domains = {"module_a": ["usage"]}
        languages = {
            "source": "en",
            "hierarchy": {"en": ["en-US"], "fr": ["fr-FR"]},
        }

        check_repository(str(tmp_path), domains, languages)

        for lang in ("en", "en-US", "fr-FR"):
            lc_messages = tmp_path / "module_a" / "locales" / lang / "LC_MESSAGES"
            assert (lc_messages / "usage.json").exists()
            assert (lc_messages / "usage.po").exists()

    def test_rejects_relative_tld(self, tmp_path):
        with pytest.raises(ValueError, match="must be absolute"):
            check_repository("relative/path", {}, {"source": "en", "hierarchy": {}})

    def test_rejects_nonexistent_tld(self, tmp_path):
        missing = tmp_path / "does-not-exist"
        with pytest.raises(FileNotFoundError, match="does not exist"):
            check_repository(str(missing), {}, {"source": "en", "hierarchy": {}})
