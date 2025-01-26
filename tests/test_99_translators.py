import pytest
from unittest.mock import patch
from datetime import datetime, timedelta
from i18n_tools.config import Config


@pytest.fixture
def mock_validate_api_url():
    with patch("i18n_tools.config.validate_api_url") as mock_validate:

        def side_effect(url):
            return {"url": url, "is_alive": True, "status_code": 200, "error": None}

        mock_validate.side_effect = side_effect
        yield mock_validate


@pytest.fixture(autouse=True)
def reset_config_singleton():
    """Réinitialiser l'instance de Config avant chaque test pour garantir l'état propre."""
    Config._instance = None
    yield


config = Config()


# Test pour ajouter des traducteurs avec validation simulée
@pytest.mark.parametrize(
    "translator_data",
    [
        {
            "name": "Translator1",
            "url": "https://valid-url1.api",
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
        {
            "name": "Translator2",
            "url": "https://valid-url2.api",
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
        {
            "name": "Translator3",
            "url": "https://valid-url3.api",
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
    ],
)
def test_add_translator_with_mocked_validation(mock_validate_api_url, translator_data):
    """Tester l'ajout de traducteurs en simulant la validation de l'URL."""
    config.add_translator(**translator_data)
    translators = config.list_translators()

    # Vérifie si le traducteur est bien ajouté
    assert translator_data["name"] in translators

    # Vérifie si la fonction validate_api_url a été appelée avec la bonne URL
    mock_validate_api_url.assert_called_with(translator_data["url"])


# Test pour get_translator
def test_get_translator():
    """Tester la récupération d'un traducteur."""
    # Utiliser les traducteurs déjà ajoutés par test_add_translator_with_mocked_validation
    translator = config.get_translator("Translator1")

    # Vérification des données
    assert translator[["details", "name"]] == "Translator1"
    assert translator[["details", "url"]] == "https://valid-url1.api"


# Test pour list_translators
def test_list_translators():
    """Tester la récupération de la liste des traducteurs."""
    # Utiliser les traducteurs déjà ajoutés par test_add_translator_with_mocked_validation
    translators = config.list_translators()

    # Vérifie que les traducteurs sont bien dans la liste
    assert "Translator1" in translators
    assert "Translator2" in translators
    assert "Translator3" in translators


# Test pour update_translator
@pytest.mark.parametrize(
    "translator, updated_data, keys, result",
    [
        (
            "Translator1",
            {
                "details": {
                    "name": "New Translator1",
                    "translation_type": "Generative",
                },
            },
            ["details", "name"],
            "New Translator1",
        ),
        (
            "Translator2",
            {
                "technical": {
                    "api": {
                        "supported_languages": ["en-GB", "fr-CA", "es"],
                    }
                }
            },
            ["technical", "api", "supported_languages"],
            ["en-GB", "fr-CA", "es"],
        ),
        (
            "Translator3",
            {
                "pricing": {
                    "payment_plan": "year",
                }
            },
            ["pricing", "payment_plan"],
            "year",
        ),
    ],
)
def test_update_translator(translator, updated_data, keys, result):
    config.update_translator(translator, updated_data)

    # Récupère le traducteur mis à jour
    translator = config.get_translator(translator)

    # Vérifie les nouvelles données
    assert translator[keys] == result


# Test pour remove_translator
def test_remove_translator():
    """Tester la suppression d'un traducteur."""
    # Supprimer le traducteur
    config.remove_translator("Translator1")

    # Vérifie que le traducteur a été supprimé
    translators = config.list_translators()
    assert "Translator1" not in translators

    # Assurer que l'autre traducteur est toujours présent
    assert "Translator2" in translators
