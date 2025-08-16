import pytest

from i18n_tools.api import validate_api_url


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
            "url": url,
            "is_alive": True,
            "status_code": 200,
            "error": None,
        },
        "https://httpbin.org/get": {
            "url": url,
            "is_alive": True,
            "status_code": 200,
            "error": None,
        },
        "https://api.github.com": {
            "url": url,
            "is_alive": True,
            "status_code": 200,
            "error": None,
        },
        "https://httpstat.us/204": {
            "url": url,
            "is_alive": True,
            "status_code": 204,
            "error": None,
        },
        "https://httpstat.us/401": {
            "url": url,
            "is_alive": True,
            "status_code": 401,
            "error": None,
        },
        "https://httpstat.us/403": {
            "url": url,
            "is_alive": True,
            "status_code": 403,
            "error": None,
        },
        "https://httpstat.us/405": {
            "url": url,
            "is_alive": True,
            "status_code": 405,
            "error": None,
        },
        "https://httpstat.us/429": {
            "url": url,
            "is_alive": True,
            "status_code": 429,
            "error": None,
        },
        "https://httpstat.us/500": {
            "url": url,
            "is_alive": True,
            "status_code": 500,
            "error": None,
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
            "url": url,
            "is_alive": False,
            "status_code": None,
            "error": "L'URL 'invalid_url' n'est pas valide au format.",
        },
        "ftp://example.com": {
            "url": url,
            "is_alive": False,
            "status_code": None,
            "error": "No connection adapters were found for 'ftp://example.com'.",
        },
        "http://": {
            "url": url,
            "is_alive": False,
            "status_code": None,
            "error": "L'URL 'http://' n'est pas valide au format.",
        },
        "https://": {
            "url": url,
            "is_alive": False,
            "status_code": None,
            "error": "L'URL 'https://' n'est pas valide au format.",
        },
        "https://thisurldoesnotexist12345.com": {
            "url": url,
            "is_alive": False,
            "status_code": None,
            "error": "Impossible de se connecter au serveur.",
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


@pytest.fixture
def get_validate_api_url(use_real_network_resources):
    """
    Determines which validate_api_url function to use based on the Git branch.

    If the current branch is "main" or "master", it uses the real validate_api_url function.
    Otherwise, it uses the mock_validate_api_url for testing purposes.

    Note: This fixture is now redundant with the `patch_validate_api_url` fixture in conftest.py,
    which automatically patches the validate_api_url function based on the Git branch.
    For new tests, consider importing and calling validate_api_url directly instead of using this fixture.

    Args:
        use_real_network_resources: Fixture that determines if real network resources should be used.

    Returns:
        function: The appropriate validate_api_url function to use.
    """
    if use_real_network_resources:
        return validate_api_url
    return mock_validate_api_url


@pytest.mark.parametrize(
    "url,expected",
    [
        (
            "https://jsonplaceholder.typicode.com/posts",
            {"is_alive": True, "status_code": 200, "error": None},
        ),
        (
            "https://httpbin.org/get",
            {"is_alive": True, "status_code": 200, "error": None},
        ),
        (
            "https://api.github.com",
            {"is_alive": True, "status_code": 200, "error": None},
        ),
        (
            "https://httpstat.us/204",
            {"is_alive": True, "status_code": 204, "error": None},
        ),
        (
            "https://httpstat.us/401",
            {"is_alive": True, "status_code": 401, "error": None},
        ),
    ],
)
def test_validate_api_url_valid_cases(url, expected, get_validate_api_url):
    """
    Tests the validate_api_url function with valid URLs to ensure proper responses.

    Uses either the real or mock function based on the current Git branch.
    """
    result = get_validate_api_url(url)
    assert result["is_alive"] == expected["is_alive"]
    assert result["status_code"] == expected["status_code"]
    assert result["error"] == expected["error"]


@pytest.mark.parametrize(
    "url,expected",
    [
        (
            "invalid_url",
            {
                "is_alive": False,
                "status_code": None,
                "error": "L'URL 'invalid_url' n'est pas valide au format.",
            },
        ),
        (
            "ftp://example.com",
            {
                "is_alive": False,
                "status_code": None,
                "error": "No connection adapters were found for 'ftp://example.com'.",
            },
        ),
        (
            "http://",
            {
                "is_alive": False,
                "status_code": None,
                "error": "L'URL 'http://' n'est pas valide au format.",
            },
        ),
        (
            "https://",
            {
                "is_alive": False,
                "status_code": None,
                "error": "L'URL 'https://' n'est pas valide au format.",
            },
        ),
        (
            "https://thisurldoesnotexist12345.com",
            {
                "is_alive": False,
                "status_code": None,
                "error": "Impossible de se connecter au serveur.",
            },
        ),
    ],
)
def test_validate_api_url_invalid_cases(url, expected, get_validate_api_url):
    """
    Tests the validate_api_url function with invalid or erroneous URLs.

    Uses either the real or mock function based on the current Git branch.
    """
    result = get_validate_api_url(url)
    assert result["is_alive"] == expected["is_alive"]
    assert result["status_code"] == expected["status_code"]
    assert result["error"] == expected["error"]


@pytest.mark.parametrize(
    "url,timeout,expected",
    [
        (
            "https://httpbin.org/delay/10",
            10,
            {"is_alive": False, "status_code": None, "error": None},
        ),
        (
            "https://httpbin.org/delay/15",
            15,
            {"is_alive": False, "status_code": None, "error": None},
        ),
        (
            "https://httpbin.org/delay/25",
            25,
            {"is_alive": False, "status_code": None, "error": None},
        ),
    ],
)
def test_validate_api_url_timeouts(url, timeout, expected, get_validate_api_url):
    """
    Tests the validate_api_url function with URLs simulating timeouts.

    Uses either the real or mock function based on the current Git branch.
    """
    result = get_validate_api_url(url, timeout=timeout)
    assert result["is_alive"] == expected["is_alive"]
    assert result["status_code"] == expected["status_code"]
    assert result["error"] == expected["error"]


@pytest.mark.parametrize(
    "url,expected",
    [
        (
            "https://jsonplaceholder.typicode.com/posts",
            {"is_alive": True, "status_code": 200, "error": None},
        ),
        (
            "invalid_url",
            {
                "is_alive": False,
                "status_code": None,
                "error": "L'URL 'invalid_url' n'est pas valide au format.",
            },
        ),
    ],
)
def test_direct_validate_api_url(url, expected):
    """
    Tests the validate_api_url function directly, without using the get_validate_api_url fixture.

    This test demonstrates how to use the patched validate_api_url function directly.
    The patch_validate_api_url fixture in conftest.py automatically patches the function
    based on the Git branch, so you can import and call it directly.

    On main/master branches, this will use the real function.
    On other branches, this will use the mock function.
    """
    # Import the function directly - it will be patched automatically by the patch_validate_api_url fixture
    from i18n_tools.api import validate_api_url

    result = validate_api_url(url)
    assert result["is_alive"] == expected["is_alive"]
    assert result["status_code"] == expected["status_code"]
    assert result["error"] == expected["error"]
