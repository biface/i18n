"""
Fixtures shared by everything under tests/api/ (including
tests/api/integration/, which inherits this conftest.py through pytest's
normal cascade): the mock/patch machinery for validate_api_url() and
validate_email(), which only tests exercising the `api` extra need.

Moved down from the root tests/conftest.py as part of the core/api test
tree split — tests/core/ never touches these, so they no longer sit at
the root where every test collection would need to import them.
"""

from unittest import mock

import pytest
from email_validator import EmailNotValidError


def mock_validate_api_url(url: str, timeout: int = 5) -> dict:
    """
    Simulates the validate_api_url function by returning predefined responses for various scenarios.

    The function uses hardcoded responses for specific URLs to mock behaviors like valid responses,
    errors, or connection timeouts. Error messages are always in English (DD-35), consistent with api.py.

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
        "https://httpbingo.org/get": {
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
        "https://httpbingo.org/status/204": {
            "url": url,
            "is_alive": True,
            "status_code": 204,
            "error": None,
        },
        "https://httpbingo.org/status/401": {
            "url": url,
            "is_alive": True,
            "status_code": 401,
            "error": None,
        },
        "https://httpbingo.org/status/403": {
            "url": url,
            "is_alive": True,
            "status_code": 403,
            "error": None,
        },
        "https://httpbingo.org/status/405": {
            "url": url,
            "is_alive": True,
            "status_code": 405,
            "error": None,
        },
        "https://httpbingo.org/status/429": {
            "url": url,
            "is_alive": True,
            "status_code": 429,
            "error": None,
        },
        "https://httpbingo.org/status/500": {
            "url": url,
            "is_alive": True,
            "status_code": 500,
            "error": None,
        },
        # URLs used in translator tests
        "https://dupont.org": {
            "url": url,
            "is_alive": True,
            "status_code": 200,
            "error": None,
        },
        "https://dupont.com": {
            "url": url,
            "is_alive": False,
            "status_code": None,
            "error": "Unable to connect to server.",  # DD-35: always English
        },
        "https://joe.com": {
            "url": url,
            "is_alive": True,
            "status_code": 200,
            "error": None,
        },
        # "https://httpbingo.org/get" reused for the Translator3 case below
        # (was "https://doe.com", drifted to a real 404 — see integration/test_translator.py).
        "https://httpbingo.org/delay/10": {
            "url": url,
            "is_alive": False,
            "status_code": None,
            "error": "Connection timed out." if timeout < 10 else None,
        },
        "https://httpbingo.org/delay/6": {
            "url": url,
            "is_alive": False,
            "status_code": None,
            "error": "Connection timed out." if timeout < 15 else None,
        },
        "https://httpbingo.org/delay/8": {
            "url": url,
            "is_alive": False,
            "status_code": None,
            "error": "Connection timed out." if timeout < 25 else None,
        },
        # Error cases
        "invalid_url": {
            "url": url,
            "is_alive": False,
            "status_code": None,
            "error": "URL 'invalid_url' is not a valid format.",
        },
        "ftp://example.com": {
            "url": url,
            "is_alive": False,
            "status_code": None,
            "error": "No connection adapters were found for 'ftp://example.com'.",  # str(e) from requests
        },
        "http://": {
            "url": url,
            "is_alive": False,
            "status_code": None,
            "error": "Invalid URL 'http://': No host supplied",  # str(e) from requests
        },
        "https://": {
            "url": url,
            "is_alive": False,
            "status_code": None,
            "error": "Invalid URL 'https://': No host supplied",  # str(e) from requests
        },
        "https://thisurldoesnotexist12345.com": {
            "url": url,
            "is_alive": False,
            "status_code": None,
            "error": "Unable to connect to server.",  # DD-35: always English
        },
        "https://www.deepl.com": {
            "url": url,
            "is_alive": True,
            "status_code": 200,
            "error": None,
        },
        "https://translate.google.com": {
            "url": url,
            "is_alive": True,
            "status_code": 200,
            "error": None,
        },
        "https://www_unvalide_url": {
            "url": url,
            "is_alive": False,
            "status_code": None,
            "error": "URL 'https://www_unvalide_url' is not a valid format.",
        },
    }

    # Retourner une réponse simulée si elle existe, sinon une erreur générique
    print(f"mock_validate_api_url called with URL: {url}")
    return simulated_responses.get(
        url,
        {
            "url": url,
            "is_alive": False,
            "status_code": None,
            "error": f"No simulated response for URL '{url}'.",
        },
    )


def mock_validate_email(email):
    """
    Simulates the validate_email function by validating email addresses and raising EmailNotValidError for invalid ones.

    This function checks if the email address follows a basic pattern and raises EmailNotValidError
    if it doesn't. It's a simplified version of the real validate_email function for testing purposes.

    Args:
        email (str): The email address to validate.

    Returns:
        dict: A dictionary containing the normalized email address.

    Raises:
        EmailNotValidError: If the email address is invalid.
    """
    print(f"mock_validate_email called with email: {email}")

    # Basic email validation
    if "@" not in email or "." not in email.split("@")[1]:
        raise EmailNotValidError(f"The email address '{email}' is not valid.")

    # Return a dictionary with the normalized email address
    return {"email": email}


@pytest.fixture(scope="function")
def patch_validate_api_url(use_real_network_resources):
    """
    Conditionally patches the validate_api_url function based on the Git branch
    or tag build (see use_real_network_resources / is_tag_ref).

    If real network resources should be used (main/master branch, or a
    tag-triggered CI run), the real validate_api_url function is used.
    Otherwise, the mock_validate_api_url function is used.

    Args:
        use_real_network_resources: Fixture (defined in the root conftest.py,
            reachable here through the normal pytest cascade) determining
            whether to use real network resources (main/master branch or
            tag build) or mocks.

    Yields:
        None: This fixture doesn't yield a value, it just applies the patch.
    """
    if use_real_network_resources:
        # On main/master branches or tag builds, use the real function
        yield
    else:
        # On other branches, use the mock function
        # Patch both the direct import in api module and the import in config module
        with (
            mock.patch("i18n_tools.api.validate_api_url", mock_validate_api_url),
            mock.patch("i18n_tools.config.validate_api_url", mock_validate_api_url),
        ):
            yield


@pytest.fixture(scope="function")
def patch_validate_email(use_real_network_resources):
    """
    Conditionally patches the validate_email function based on the Git branch
    or tag build (see use_real_network_resources / is_tag_ref).

    If real network resources should be used (main/master branch, or a
    tag-triggered CI run), the real validate_email function is used.
    Otherwise, the mock_validate_email function is used.

    Args:
        use_real_network_resources: Fixture (defined in the root conftest.py,
            reachable here through the normal pytest cascade) determining
            whether to use real network resources (main/master branch or
            tag build) or mocks.

    Yields:
        None: This fixture doesn't yield a value, it just applies the patch.
    """
    if use_real_network_resources:
        # On main/master branches or tag builds, use the real function
        yield
    else:
        # On other branches, use the mock function.
        # Since DD-41 (#118), config.py imports validate_email lazily inside
        # each method (add_author/get_author/remove_author) rather than at
        # module load time — there is no more i18n_tools.config.validate_email
        # module attribute to patch. Patching email_validator.validate_email
        # itself is now sufficient: the local `from email_validator import
        # validate_email` re-reads the (patched) attribute at call time.
        with mock.patch("email_validator.validate_email", mock_validate_email):
            yield
