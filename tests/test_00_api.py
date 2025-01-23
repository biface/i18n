import pytest
import requests
from unittest.mock import patch, MagicMock
import os
import subprocess

from i18n_tools.api import validate_api_url


def get_current_git_branch():
    github_branch = os.getenv("GITHUB_REF")
    if github_branch and github_branch.startswith("refs/heads/"):
        return github_branch.replace("refs/heads/", "")

    gitlab_branch = os.getenv("CI_COMMIT_REF_NAME")
    if gitlab_branch:
        return gitlab_branch

    try:
        branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True).strip()
        return branch
    except Exception:
        return None


IS_MAIN_BRANCH = get_current_git_branch() in {"main", "master"}


@pytest.mark.parametrize(
    "url,mock_response,expected",
    [
        # Valid cases
        (
            "https://jsonplaceholder.typicode.com/posts",
            {"status_code": 200, "content": "{}", "is_alive": True},
            {"is_alive": True, "status_code": 200, "error": None},
        ),
        (
            "https://httpbin.org/get",
            {"status_code": 200, "content": "{}", "is_alive": True},
            {"is_alive": True, "status_code": 200, "error": None},
        ),
        (
            "https://api.github.com",
            {"status_code": 200, "content": "{}", "is_alive": True},
            {"is_alive": True, "status_code": 200, "error": None},
        ),
        (
            "https://httpstat.us/204",
            {"status_code": 204, "content": "", "is_alive": True},
            {"is_alive": True, "status_code": 204, "error": None},
        ),
        (
            "https://httpstat.us/401",
            {"status_code": 401, "content": "", "is_alive": True},
            {"is_alive": True, "status_code": 401, "error": None},
        ),
        (
            "https://httpstat.us/403",
            {"status_code": 403, "content": "", "is_alive": True},
            {"is_alive": True, "status_code": 403, "error": None},
        ),
        (
            "https://httpstat.us/405",
            {"status_code": 405, "content": "", "is_alive": True},
            {"is_alive": True, "status_code": 405, "error": None},
        ),
        (
            "https://httpstat.us/429",
            {"status_code": 429, "content": "", "is_alive": True},
            {"is_alive": True, "status_code": 429, "error": None},
        ),
        (
            "https://httpstat.us/500",
            {"status_code": 500, "content": "", "is_alive": True},
            {"is_alive": True, "status_code": 500, "error": None},
        ),
        # Error and invalid cases
        (
            "invalid_url",
            {"status_code": None, "content": None, "is_alive": False, "error": "L'URL 'invalid_url' n'est pas valide au format."},
            {"is_alive": False, "status_code": None, "error": "L'URL 'invalid_url' n'est pas valide au format."},
        ),
        (
            "ftp://example.com",
            {"status_code": None, "content": None, "is_alive": False, "error": "No connection adapters were found for 'ftp://example.com'"},
            {"is_alive": False, "status_code": None, "error": "No connection adapters were found for 'ftp://example.com'"},
        ),
        (
            "http://",
            {"status_code": None, "content": None, "is_alive": False, "error": "L'URL 'http://' n'est pas valide au format."},
            {"is_alive": False, "status_code": None, "error": "L'URL 'http://' n'est pas valide au format."},
        ),
        (
            "https://",
            {"status_code": None, "content": None, "is_alive": False, "error": "L'URL 'https://' n'est pas valide au format."},
            {"is_alive": False, "status_code": None, "error": "L'URL 'https://' n'est pas valide au format."},
        ),
        (
            "https://thisurldoesnotexist12345.com",
            {"status_code": None, "content": None, "is_alive": False, "error": "Impossible de se connecter au serveur."},
            {"is_alive": False, "status_code": None, "error": "Impossible de se connecter au serveur."},
        ),
        (
            "https://httpstat.us/400",
            {"status_code": 400, "content": "", "is_alive": False, "error": "Code de statut inattendu: 400"},
            {"is_alive": False, "status_code": 400, "error": "Code de statut inattendu: 400"},
        ),
        (
            "https://httpstat.us/404",
            {"status_code": 404, "content": "", "is_alive": False, "error": "Code de statut inattendu: 404"},
            {"is_alive": False, "status_code": 404, "error": "Code de statut inattendu: 404"},
        ),
        (
            "https://httpstat.us/503",
            {"status_code": 503, "content": "", "is_alive": False, "error": "Code de statut inattendu: 503"},
            {"is_alive": False, "status_code": 503, "error": "Code de statut inattendu: 503"},
        ),
    ],
)
def test_validate_api_url_with_mock(url, mock_response, expected):
    def mock_requests_get(*args, **kwargs):
        mock_resp = MagicMock()
        mock_resp.status_code = mock_response["status_code"]
        mock_resp.text = mock_response["content"]
        return mock_resp

    # Utilisation du patch uniquement si on n'est pas sur une branche principale
    if not IS_MAIN_BRANCH:
        print("Not main")
        with patch("requests.get", side_effect=mock_requests_get):
            result = validate_api_url(url)
            assert result["is_alive"] == expected["is_alive"]
            assert result["status_code"] == expected["status_code"]
            assert result["error"] == expected["error"]
    else:
        # Test réel sur une branche principale
        print("Main")
        result = validate_api_url(url)
        assert result["is_alive"] == expected["is_alive"]
        assert result["status_code"] == expected["status_code"]
        assert result["error"] == expected["error"]


@pytest.mark.parametrize(
    "url,timeout,mock_response,expected",
    [
        # Cas où le délai expire
        (
            "https://httpbin.org/delay/10",
            1,  # Timeout très court pour forcer une expiration
            {"raise_timeout": True},  # Simule un délai d'expiration
            {"is_alive": False, "status_code": None, "error": "Le délai de connexion a expiré."},
        ),
    ],
)
def test_validate_api_url_with_mock_and_timeout(url, timeout, mock_response, expected):
    def mock_requests_get(*args, **kwargs):
        # Simuler un délai d'expiration si "raise_timeout" est dans la réponse simulée
        if mock_response.get("raise_timeout", False):
            raise requests.exceptions.Timeout("Le délai de connexion a expiré.")
        mock_resp = MagicMock()
        mock_resp.status_code = mock_response.get("status_code", 200)
        mock_resp.text = mock_response.get("content", "{}")
        return mock_resp

    # Utilisation du patch uniquement si on n'est pas sur une branche principale
    if not IS_MAIN_BRANCH:
        with patch("requests.get", side_effect=mock_requests_get):
            result = validate_api_url(url, timeout=timeout)
            assert result["is_alive"] == expected["is_alive"]
            assert result["status_code"] == expected["status_code"]
            assert result["error"] == expected["error"]
    else:
        # Test réel sur une branche principale
        result = validate_api_url(url, timeout=timeout)
        assert result["is_alive"] == expected["is_alive"]
        assert result["status_code"] == expected["status_code"]
        assert result["error"] == expected["error"]
