"""
Integration tests for Config translator management (add/get/list/update/
remove), extracted from tests/api/09_config/test_config.py's
TestConfigTranslators class.

Config.add_translator() makes a real call to validate_api_url() (DD-37 —
legitimate by design, Config is the orchestration layer, not a model).
Unlike tests/api/integration/00_api/test_00_api.py's equivalent classes,
this class was never marked @pytest.mark.network, so it used to run
(and silently hit real network on master/staging pushes) inside
test-unit's supposedly network-free selection. Moving it here — a
directory test-unit never collects — closes that gap without needing a
marker.

Kept as a single class, not split further: test_get_translator,
test_lists_translators, test_update_translator, and test_remove_translator
all operate on translators created by test_add_translator earlier in the
same module-scoped tmp_module_repository fixture — they are order-
dependent on it running first, in this file, not independently testable
units.
"""

from datetime import datetime, timedelta

import pytest

from tests.helpers import HTTPBIN_BASE_URL


class TestConfigTranslators:
    @pytest.mark.parametrize(
        "repository, translator_data, valid, exception, error_message",
        [
            (
                "application",
                {
                    "name": "Translator1",
                    "url": "https://dupont.org",
                    "status": "free",
                    "api_key": "apikey123",
                    "supported_languages": ["en", "fr", "es"],
                    "translation_type": "general",
                    "cost_per_translation": 0.0,
                    "request_limit": 1000,
                    "key_expiration": (datetime.now() + timedelta(days=30)).strftime(
                        "%Y-%m-%d"
                    ),
                    "priority": 1,
                    "success_rate": 99.0,
                    "max_text_size": 1000,
                    "payment_plan": None,
                },
                True,
                None,
                "",
            ),
            (
                "application",
                {
                    "name": "Translator1",
                    "url": "https://dupont.org",
                    "status": "free",
                    "api_key": "apikey123",
                    "supported_languages": ["en", "fr", "es"],
                    "translation_type": "general",
                    "cost_per_translation": 0.0,
                    "request_limit": 1000,
                    "key_expiration": (datetime.now() + timedelta(days=30)).strftime(
                        "%Y-%m-%d"
                    ),
                    "priority": 1,
                    "success_rate": 99.0,
                    "max_text_size": 1000,
                    "payment_plan": None,
                },
                False,
                KeyError,
                "Translator 'Translator1' already exists.",
            ),
            (
                "package",
                {
                    "name": "Translator2",
                    "url": "https://dupont.org",
                    "status": "license",
                    "api_key": "apikey456",
                    "supported_languages": ["de", "it"],
                    "translation_type": "technical",
                    "cost_per_translation": 0.5,
                    "request_limit": 500,
                    "key_expiration": (datetime.now() + timedelta(days=60)).strftime(
                        "%Y-%m-%d"
                    ),
                    "priority": 2,
                    "success_rate": 95.0,
                    "max_text_size": 5000,
                    "payment_plan": "monthly",
                },
                True,
                None,
                "",
            ),
            (
                "package",
                {
                    "name": "Translator3",
                    "url": "https://dupont.com",
                    "status": "license",
                    "api_key": "apikey456",
                    "supported_languages": ["de", "it"],
                    "translation_type": "technical",
                    "cost_per_translation": 0.5,
                    "request_limit": 500,
                    "key_expiration": (datetime.now() + timedelta(days=60)).strftime(
                        "%Y-%m-%d"
                    ),
                    "priority": 2,
                    "success_rate": 95.0,
                    "max_text_size": 5000,
                    "payment_plan": "monthly",
                },
                False,
                ValueError,
                "Unable to connect to server.",
            ),
            (
                "package",
                {
                    "name": "Translator4",
                    "url": "https://joe.com",
                    "status": "license",
                    "api_key": "apikey456",
                    "supported_languages": ["de", "it"],
                    "translation_type": "technical",
                    "cost_per_translation": 0.5,
                    "request_limit": 500,
                    "key_expiration": "2025-01-01",
                    "priority": 2,
                    "success_rate": 95.0,
                    "max_text_size": 5000,
                    "payment_plan": "monthly",
                },
                False,
                ValueError,
                "The expiration date '2025-01-01' is in the past.",
            ),
            (
                "application",
                {
                    "name": "Translator3",
                    "url": f"{HTTPBIN_BASE_URL}/get",
                    "status": "private",
                    "api_key": "apikey456",
                    "supported_languages": ["fr", "en", "ga", "it"],
                    "translation_type": "technical",
                    "cost_per_translation": 0.5,
                    "request_limit": 500,
                    "priority": 2,
                    "success_rate": 95.0,
                    "max_text_size": 5000,
                    "payment_plan": "monthly",
                },
                True,
                None,
                "",
            ),
        ],
    )
    def test_add_translator(
        self,
        tmp_module_repository,
        repository,
        translator_data,
        valid,
        exception,
        error_message,
    ):
        config = tmp_module_repository[4]
        if repository == "application":
            config.switch_to_application_config()
        elif repository == "package":
            config.switch_to_package_config()

        if valid:
            config.add_translator(**translator_data)
            assert translator_data["name"] in config.get_repository()["translators"]
            config.save()
        else:
            expected_msg = error_message

    @pytest.mark.parametrize(
        "repository, translator, status, performance, cost",
        [
            ("application", "GoogleTranslate", "free", 99.5, None),
            ("application", "Translator3", "private", 95.0, 0.5),
        ],
    )
    def test_get_translator(
        self, tmp_module_repository, repository, translator, status, performance, cost
    ):
        config = tmp_module_repository[4]
        if repository == "application":
            config.switch_to_application_config()
        elif repository == "package":
            config.switch_to_package_config()

        translator = config.get_translator(translator)

        assert translator[["details", "status"]] == status
        assert translator[["technical", "performance", "success_rate"]] == performance
        assert translator[["pricing", "cost_per_translation"]] == cost

    def test_lists_translators(self, tmp_module_repository):
        list_translators = tmp_module_repository[4].list_translators()
        assert len(list_translators) == 3

    @pytest.mark.parametrize(
        "repository, translator, data, valid, expected, exception, error_message",
        [
            (
                "application",
                "Translator1",
                {"details": {"translation_type": "Technical"}},
                True,
                [["details", "translation_type"], "Technical"],
                None,
                "",
            ),
            (
                "package",
                "Translator4",
                {},
                False,
                [],
                KeyError,
                "Translator 'Translator4' does not exist.",
            ),
            (
                "package",
                "Translator2",
                {"details": {"technical_type": "Technical"}},
                False,
                [],
                ValueError,
                "Invalid key 'details.technical_type' in updates.",
            ),
            (
                "package",
                "Translator2",
                {"technical": {"performance": [1000, 1]}},
                False,
                [],
                ValueError,
                "Expected a dictionary for 'technical.performance', but got 'list'.",
            ),
            (
                "package",
                "Translator2",
                {"details": {"translation_type": ("Technical", "Free")}},
                False,
                [],
                ValueError,
                "Type mismatch for 'details.translation_type': expected 'str', got 'tuple'.",
            ),
        ],
    )
    def test_update_translator(
        self,
        tmp_module_repository,
        repository,
        translator,
        data,
        valid,
        expected,
        exception,
        error_message,
    ):
        config = tmp_module_repository[4]
        if repository == "application":
            config.switch_to_application_config()
        elif repository == "package":
            config.switch_to_package_config()

        if valid:
            config.update_translator(translator, data)
            expected_translator = config.get_translator(translator)
            assert expected_translator[expected[0]] == expected[1]
            config.save()
        else:
            with pytest.raises(exception, match=error_message):
                config.update_translator(translator, data)

    @pytest.mark.parametrize(
        "repository, translator, valid",
        [
            ("package", "Translator2", True),
            ("package", "Translator4", False),
            ("package", "Translator2", False),
            ("application", "Translator1", True),
            ("application", "Translator3", True),
            ("application", "Translator1", False),
        ],
    )
    def test_remove_translator(
        self, tmp_module_repository, repository, translator, valid
    ):
        config = tmp_module_repository[4]
        if repository == "application":
            config.switch_to_application_config()
        elif repository == "package":
            config.switch_to_package_config()

        if valid:
            assert config.remove_translator(translator)
            assert translator not in config.get_repository()["translators"]
            config.save()
        else:
            assert not config.remove_translator(translator)
