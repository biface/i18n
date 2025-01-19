import pytest

from i18n_tools.api import validate_api_url

@pytest.mark.parametrize(
    "url,expected",
    [
        # Cas valides
        ("https://jsonplaceholder.typicode.com/posts", {"is_alive": True, "status_code": 200, "error": None}),
        ("https://httpbin.org/get", {"is_alive": True, "status_code": 200, "error": None}),
        ("https://api.github.com", {"is_alive": True, "status_code": 200, "error": None}),
        ("https://httpstat.us/204", {"is_alive": True, "status_code": 204, "error": None}),
        ("https://httpstat.us/401", {"is_alive": True, "status_code": 401, "error": None}),
        ("https://httpstat.us/403", {"is_alive": True, "status_code": 403, "error": None}),
        ("https://httpstat.us/405", {"is_alive": True, "status_code": 405, "error": None}),
        ("https://httpstat.us/429", {"is_alive": True, "status_code": 429, "error": None}),
        ("https://httpstat.us/500", {"is_alive": True, "status_code": 500, "error": None}),
    ],
)
def test_validate_api_url_valid(url, expected):
    result = validate_api_url(url)
    assert result["is_alive"] == expected["is_alive"]
    assert result["status_code"] == expected["status_code"]
    assert result["error"] == expected["error"]


@pytest.mark.parametrize(
    "url,expected",
    [
        # Cas invalides
        ("invalid_url", {"is_alive": False, "status_code": None, "error": "L'URL 'invalid_url' n'est pas valide au format."}),
        ("ftp://example.com", {"is_alive": False, "status_code": None, "error": "No connection adapters were found for 'ftp://example.com'"}),
        ("http://", {"is_alive": False, "status_code": None, "error": "L'URL 'http://' n'est pas valide au format."}),
        ("https://", {"is_alive": False, "status_code": None, "error": "L'URL 'https://' n'est pas valide au format."}),
        ("https://thisurldoesnotexist12345.com", {"is_alive": False, "status_code": None, "error": "Impossible de se connecter au serveur."}),
        ("https://httpstat.us/400", {"is_alive": False, "status_code": 400, "error": "Code de statut inattendu: 400"}),
        ("https://httpstat.us/404", {"is_alive": False, "status_code": 404, "error": "Code de statut inattendu: 404"}),
        ("https://httpstat.us/503", {"is_alive": False, "status_code": 503, "error": "Code de statut inattendu: 503"}),
    ],
)
def test_validate_api_url_invalid(url, expected):
    result = validate_api_url(url)
    assert result["is_alive"] == expected["is_alive"]
    assert result["status_code"] == expected["status_code"]
    assert result["error"] == expected["error"]

@pytest.mark.parametrize(
    "url,timeout,expected",
    [
        # Cas où le délai expire
        ("https://httpbin.org/delay/10", 1, {"is_alive": False, "status_code": None, "error": "Le délai de connexion a expiré."}),
    ],
)
def test_validate_api_url_timeout(url, timeout, expected):
    result = validate_api_url(url, timeout=timeout)
    assert result["is_alive"] == expected["is_alive"]
    assert result["status_code"] == expected["status_code"]
    assert result["error"] == expected["error"]