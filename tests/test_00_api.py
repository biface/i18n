import locale as _locale

import pytest

from i18n_tools.api import validate_api_url

# ---------------------------------------------------------------------------
# Locale-aware error messages — extend with new language keys as needed.
# ---------------------------------------------------------------------------

_API_ERROR_MESSAGES: dict = {
    "timeout": {
        "fr": "Le délai de connexion a expiré.",
        "en": "Connection timed out.",
    },
    "connection": {
        "fr": "Impossible de se connecter au serveur.",
        "en": "Unable to connect to server.",
    },
}


def _mock_error(key: str) -> str:
    """Return the locale-appropriate mock error message for *key*."""
    lang, _ = _locale.getdefaultlocale()
    lang_code = (lang or "en")[:2]
    messages = _API_ERROR_MESSAGES[key]
    return messages.get(lang_code, messages["en"])


def mock_validate_api_url(url: str, timeout: int = 5) -> dict:
    """
    Simulates the validate_api_url function by returning predefined responses for various scenarios.

    The function uses hardcoded responses for specific URLs to mock behaviors like valid responses,
    errors, or connection timeouts. Error messages are locale-aware: the language returned matches
    the system locale so that assertions using _API_ERROR_MESSAGES remain consistent across
    development environments.

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
        "https://httpbin.org/status/204": {
            "url": url,
            "is_alive": True,
            "status_code": 204,
            "error": None,
        },
        "https://httpbin.org/status/401": {
            "url": url,
            "is_alive": True,
            "status_code": 401,
            "error": None,
        },
        "https://httpbin.org/status/403": {
            "url": url,
            "is_alive": True,
            "status_code": 403,
            "error": None,
        },
        "https://httpbin.org/status/405": {
            "url": url,
            "is_alive": True,
            "status_code": 405,
            "error": None,
        },
        "https://httpbin.org/status/429": {
            "url": url,
            "is_alive": True,
            "status_code": 429,
            "error": None,
        },
        "https://httpbin.org/status/500": {
            "url": url,
            "is_alive": True,
            "status_code": 500,
            "error": None,
        },
        # Simulating delays — error is locale-aware
        "https://httpbin.org/delay/10": {
            "url": url,
            "is_alive": False,
            "status_code": None,
            "error": _mock_error("timeout") if timeout < 10 else None,
        },
        "https://httpbin.org/delay/15": {
            "url": url,
            "is_alive": False,
            "status_code": None,
            "error": _mock_error("timeout") if timeout < 15 else None,
        },
        "https://httpbin.org/delay/25": {
            "url": url,
            "is_alive": False,
            "status_code": None,
            "error": _mock_error("timeout") if timeout < 25 else None,
        },
        # Error cases
        "invalid_url": {
            "url": url,
            "is_alive": False,
            "status_code": None,
            "error": "URL 'invalid_url' is not a valid format.",  # hardcoded English in api.py
        },
        "ftp://example.com": {
            "url": url,
            "is_alive": False,
            "status_code": None,
            "error": _mock_error("connection"),  # locale-aware
        },
        "http://": {
            "url": url,
            "is_alive": False,
            "status_code": None,
            "error": "Invalid URL 'http://': No host supplied",  # str(e) from requests — always English
        },
        "https://": {
            "url": url,
            "is_alive": False,
            "status_code": None,
            "error": "Invalid URL 'https://': No host supplied",  # str(e) from requests — always English
        },
        "https://thisurldoesnotexist12345.com": {
            "url": url,
            "is_alive": False,
            "status_code": None,
            "error": _mock_error("connection"),  # locale-aware
        },
    }

    return simulated_responses.get(
        url,
        {
            "url": url,
            "is_alive": False,
            "status_code": None,
            "error": f"No simulated response for URL '{url}'.",
        },
    )


@pytest.fixture
def get_validate_api_url(use_real_network_resources):
    """
    Determines which validate_api_url function to use based on the Git branch.

    If the current branch is "main" or "master", it uses the real validate_api_url function.
    Otherwise, it uses the mock_validate_api_url for testing purposes.

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
            "https://httpbin.org/status/204",
            {"is_alive": True, "status_code": 204, "error": None},
        ),
        (
            "https://httpbin.org/status/401",
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
                "error": "URL 'invalid_url' is not a valid format.",  # hardcoded English in api.py
            },
        ),
        (
            "ftp://example.com",
            {
                "is_alive": False,
                "status_code": None,
                "error": None,  # str(e) RequestException — non contrôlé
            },
        ),
        (
            "http://",
            {
                "is_alive": False,
                "status_code": None,
                "error": None,  # str(e) from requests — uncontrolled
            },
        ),
        (
            "https://",
            {
                "is_alive": False,
                "status_code": None,
                "error": None,  # str(e) from requests — uncontrolled
            },
        ),
        (
            "https://thisurldoesnotexist12345.com",
            {
                "is_alive": False,
                "status_code": None,
                "error": {
                    "fr": "Impossible de se connecter au serveur.",
                    "en": "Unable to connect to server.",
                },
            },
        ),
    ],
)
def test_validate_api_url_invalid_cases(
    url, expected, get_validate_api_url, system_lang
):
    """
    Tests the validate_api_url function with invalid or erroneous URLs.

    Uses either the real or mock function based on the current Git branch.
    Error messages that are locale-dependent are expressed as dicts keyed by language code.
    """
    result = get_validate_api_url(url)
    assert result["is_alive"] == expected["is_alive"]
    assert result["status_code"] == expected["status_code"]
    if expected["error"] is None:
        assert result["error"] is not None
    elif isinstance(expected["error"], dict):
        assert result["error"] == expected["error"].get(
            system_lang, expected["error"]["en"]
        )
    else:
        assert result["error"] == expected["error"]


@pytest.mark.skip(
    reason="httpbin.org behaviour unreliable on master — validate_api_url to be reviewed"
)
@pytest.mark.parametrize(
    "url,timeout,expected",
    [
        (
            "https://httpbin.org/delay/10",
            5,
            {
                "is_alive": False,
                "status_code": None,
                "error": {
                    "fr": "Le délai de connexion a expiré.",
                    "en": "Connection timed out.",
                },
            },
        ),
        (
            "https://httpbin.org/delay/15",
            5,
            {
                "is_alive": False,
                "status_code": None,
                "error": {
                    "fr": "Le délai de connexion a expiré.",
                    "en": "Connection timed out.",
                },
            },
        ),
        (
            "https://httpbin.org/delay/25",
            5,
            {
                "is_alive": False,
                "status_code": None,
                "error": {
                    "fr": "Le délai de connexion a expiré.",
                    "en": "Connection timed out.",
                },
            },
        ),
    ],
)
def test_validate_api_url_timeouts(
    url, timeout, expected, get_validate_api_url, system_lang
):
    """
    Tests the validate_api_url function with URLs simulating timeouts.

    Uses either the real or mock function based on the current Git branch.
    Timeout value is always lower than the server delay to guarantee the exception fires.
    """
    result = get_validate_api_url(url, timeout=timeout)
    assert result["is_alive"] == expected["is_alive"]
    assert result["status_code"] == expected["status_code"]
    assert result["error"] == expected["error"].get(
        system_lang, expected["error"]["en"]
    )


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
                "error": "URL 'invalid_url' is not a valid format.",
            },
        ),
    ],
)
def test_direct_validate_api_url(url, expected):
    """
    Tests the validate_api_url function directly, without using the get_validate_api_url fixture.

    The patch_validate_api_url fixture in conftest.py automatically patches the function
    based on the Git branch, so you can import and call it directly.

    On main/master branches, this will use the real function.
    On other branches, this will use the mock function.
    """
    from i18n_tools.api import validate_api_url

    result = validate_api_url(url)
    assert result["is_alive"] == expected["is_alive"]
    assert result["status_code"] == expected["status_code"]
    assert result["error"] == expected["error"]
