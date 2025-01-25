import pytest
import os
import subprocess

from i18n_tools.api import validate_api_url

def get_current_git_branch():
    """
    Retrieves the current Git branch name.

    First, it checks for environment variables `GITHUB_REF` (GitHub) or `CI_COMMIT_REF_NAME` (GitLab).
    If those are not available, it attempts to retrieve the branch name from the local Git repository.

    Returns:
        str: The name of the current Git branch, or None if it cannot be determined.
    """

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

def mock_validate_api_url(url: str, timeout: int = 5) -> dict:
    """
    Simulates the validate_api_url function by returning predefined responses for various scenarios.

    The function uses hardcoded responses for specific URLs to mock behaviors like valid responses,
    errors, or connection timeouts. Simulated error messages should be adapted to the developer's
    environment (locale) to ensure better clarity during testing.

    Args:
        url (str): The URL to validate.
        timeout (int): The timeout threshold (in seconds) to simulate delay-based responses.

    Returns:
        dict: A simulated response containing the keys:
              - "url" (str): The input URL.
              - "is_alive" (bool): Whether the URL is considered reachable.
              - "status_code" (int or None): The HTTP status code, if applicable.
              - "error" (str or None): An error message, if applicable.
    """
    simulated_responses = {
        # Valid cases
        "https://jsonplaceholder.typicode.com/posts": {
            "url": url, "is_alive": True, "status_code": 200, "error": None
        },
        "https://httpbin.org/get": {
            "url": url, "is_alive": True, "status_code": 200, "error": None
        },
        "https://api.github.com": {
            "url": url, "is_alive": True, "status_code": 200, "error": None
        },
        "https://httpstat.us/204": {
            "url": url, "is_alive": True, "status_code": 204, "error": None
        },
        "https://httpstat.us/401": {
            "url": url, "is_alive": True, "status_code": 401, "error": None
        },
        "https://httpstat.us/403": {
            "url": url, "is_alive": True, "status_code": 403, "error": None
        },
        "https://httpstat.us/405": {
            "url": url, "is_alive": True, "status_code": 405, "error": None
        },
        "https://httpstat.us/429": {
            "url": url, "is_alive": True, "status_code": 429, "error": None
        },
        "https://httpstat.us/500": {
            "url": url, "is_alive": True, "status_code": 500, "error": None
        },
        # Simulating delays
        "https://httpbin.org/delay/10": {
            "url": url,
            "is_alive": False,
            "status_code": None,
            "error": "Le délai de connexion a expiré." if timeout < 10 else None,
        },
        "https://httpbin.org/delay/15": {
            "url": url,
            "is_alive": False,
            "status_code": None,
            "error": "Le délai de connexion a expiré." if timeout < 15 else None,
        },
        "https://httpbin.org/delay/25": {
            "url": url,
            "is_alive": False,
            "status_code": None,
            "error": "Le délai de connexion a expiré." if timeout < 25 else None,
        },
        # Error cases
        "invalid_url": {
            "url": url, "is_alive": False, "status_code": None, "error": "L'URL 'invalid_url' n'est pas valide au format."
        },
        "ftp://example.com": {
            "url": url, "is_alive": False, "status_code": None, "error": "No connection adapters were found for 'ftp://example.com'."
        },
        "http://": {
            "url": url, "is_alive": False, "status_code": None, "error": "L'URL 'http://' n'est pas valide au format."
        },
        "https://": {
            "url": url, "is_alive": False, "status_code": None, "error": "L'URL 'https://' n'est pas valide au format."
        },
        "https://thisurldoesnotexist12345.com": {
            "url": url, "is_alive": False, "status_code": None, "error": "Impossible de se connecter au serveur."
        },
    }

    # Retourner une réponse simulée si elle existe, sinon une erreur générique
    return simulated_responses.get(
        url,
        {
            "url": url,
            "is_alive": False,
            "status_code": None,
            "error": f"Aucune réponse simulée pour l'URL '{url}'.",
        },
    )


def get_validate_api_url():
    """
    Determines which validate_api_url function to use based on the Git branch.

    If the current branch is "main" or "master", it uses the real validate_api_url function.
    Otherwise, it uses the mock_validate_api_url for testing purposes.

    Returns:
        function: The appropriate validate_api_url function to use.
    """
    if IS_MAIN_BRANCH:
        return validate_api_url
    return mock_validate_api_url

@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://jsonplaceholder.typicode.com/posts", {"is_alive": True, "status_code": 200, "error": None}),
        ("https://httpbin.org/get", {"is_alive": True, "status_code": 200, "error": None}),
        ("https://api.github.com", {"is_alive": True, "status_code": 200, "error": None}),
        ("https://httpstat.us/204", {"is_alive": True, "status_code": 204, "error": None}),
        ("https://httpstat.us/401", {"is_alive": True, "status_code": 401, "error": None}),
    ],
)
def test_mock_validate_api_url_valid_cases(url, expected):
    """
    Tests the validate_api_url function with valid URLs to ensure proper responses.
    """
    result = get_validate_api_url()(url)
    assert result["is_alive"] == expected["is_alive"]
    assert result["status_code"] == expected["status_code"]
    assert result["error"] == expected["error"]


@pytest.mark.parametrize(
    "url,expected",
    [
        ("invalid_url", {"is_alive": False, "status_code": None, "error": "L'URL 'invalid_url' n'est pas valide au format."}),
        ("ftp://example.com", {"is_alive": False, "status_code": None, "error": "No connection adapters were found for 'ftp://example.com'."}),
        ("http://", {"is_alive": False, "status_code": None, "error": "L'URL 'http://' n'est pas valide au format."}),
        ("https://", {"is_alive": False, "status_code": None, "error": "L'URL 'https://' n'est pas valide au format."}),
        ("https://thisurldoesnotexist12345.com", {"is_alive": False, "status_code": None, "error": "Impossible de se connecter au serveur."}),
    ],
)
def test_mock_validate_api_url_invalid_cases(url, expected):
    """
    Tests the validate_api_url function with invalid or erroneous URLs.
    """
    result = get_validate_api_url()(url)
    assert result["is_alive"] == expected["is_alive"]
    assert result["status_code"] == expected["status_code"]
    assert result["error"] == expected["error"]


@pytest.mark.parametrize(
    "url,timeout,expected",
    [
        ("https://httpbin.org/delay/10", 10, {"is_alive": False, "status_code": None, "error": None}),
        ("https://httpbin.org/delay/15", 15, {"is_alive": False, "status_code": None, "error": None}),
        ("https://httpbin.org/delay/25", 25, {"is_alive": False, "status_code": None, "error": None}),
    ],
)
def test_mock_validate_api_url_timeouts(url, timeout, expected):
    """
    Tests the mock_validate_api_url function with URLs simulating timeouts.
    """
    result = get_validate_api_url()(url, timeout=timeout)
    assert result["is_alive"] == expected["is_alive"]
    assert result["status_code"] == expected["status_code"]
    assert result["error"] == expected["error"]
