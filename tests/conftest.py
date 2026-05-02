# ---------------------------------------------------------------------------
# TEST EXECUTION ORDER — MANDATORY
#
# The Config class uses patterns.Singleton: only one instance exists per
# pytest process. Directory prefixes enforce the required execution order:
#
#   00_api, 00_locale  → no Config dependency
#   01_loader          → initializes the Singleton
#   02_models          → no Config dependency
#   09_config          → inherits the Singleton from 01_loader
#
# Changing this order will cause failures in 09_config (54 tests).
# ---------------------------------------------------------------------------

import copy
import locale as _locale
import os
import subprocess
from pathlib import Path
from unittest import mock

import pytest
import yaml
from email_validator import EmailNotValidError
from helpers import copy_and_update_repository

from i18n_tools.config import Config


@pytest.fixture(scope="session")
def system_lang() -> str:
    """Two-letter system locale language code (e.g. 'fr', 'en')."""
    lang, _ = _locale.getdefaultlocale()
    return (lang or "en")[:2]


@pytest.fixture(scope="session")
def root_conf_test() -> Path:
    return Path(__file__).parent


@pytest.fixture(scope="session")
def conf_tests(root_conf_test) -> dict:
    config_path = root_conf_test / "parametrize.yaml"
    with open(config_path, "r") as file:
        return yaml.safe_load(file)


def config_data(config_path_test, config_file_test):
    config = Config()
    config.application[["paths", "config"]] = config_path_test
    config.application[["paths", "settings"]] = config_file_test
    config.load()
    return config


@pytest.fixture(scope="function")
def tmp_function_repository(root_conf_test, conf_tests, tmp_path) -> list:
    destination_package = copy_and_update_repository(
        root_conf_test, tmp_path, conf_tests, "package"
    )
    destination_application = copy_and_update_repository(
        root_conf_test, tmp_path, conf_tests, "application"
    )

    other = tmp_path / conf_tests["repository"]["other"]
    os.makedirs(other, exist_ok=True)

    return [
        [str(tmp_path), tmp_path],
        [str(destination_package), destination_package],
        [str(destination_application), destination_package],
        [str(other), other],
        config_data(
            str(destination_application / "fsm_tools" / "locales" / "_i18n_tools"),
            "i18n-tools.yaml",
        ),
    ]


@pytest.fixture(scope="module")
def tmp_module_repository(root_conf_test, conf_tests, tmp_path_factory) -> list:

    tmp_path = tmp_path_factory.mktemp("module-factory")
    destination_package = copy_and_update_repository(
        root_conf_test, tmp_path, conf_tests, "package"
    )
    destination_application = copy_and_update_repository(
        root_conf_test, tmp_path, conf_tests, "application"
    )

    other = tmp_path / conf_tests["repository"]["other"]
    os.makedirs(other, exist_ok=True)

    return [
        [str(tmp_path), tmp_path],
        [str(destination_package), destination_package],
        [str(destination_application), destination_application],
        [str(other), other],
        config_data(
            str(destination_application / "fsm_tools" / "locales" / "_i18n_tools"),
            "i18n-tools.yaml",
        ),
    ]


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
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True
        ).strip()
        return branch
    except Exception:
        return None


@pytest.fixture(scope="session")
def is_main_branch():
    """
    Determines if the current Git branch is a main branch (main or master).

    Returns:
        bool: True if the current branch is main or master, False otherwise.
    """
    return get_current_git_branch() in {"main", "master"}


@pytest.fixture(scope="session")
def use_real_network_resources(is_main_branch):
    """
    Determines whether to use real network resources or mocked versions.

    On main/master branches, real network resources are used.
    On other branches, mocked versions are used to avoid network dependencies.

    Returns:
        bool: True if real network resources should be used, False if mocks should be used.
    """
    return is_main_branch


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
        "https://doe.com": {
            "url": url,
            "is_alive": True,
            "status_code": 200,
            "error": None,
        },
        # Simulating delays — DD-35: always English
        "https://httpbin.org/delay/10": {
            "url": url,
            "is_alive": False,
            "status_code": None,
            "error": "Connection timed out." if timeout < 10 else None,
        },
        "https://httpbin.org/delay/15": {
            "url": url,
            "is_alive": False,
            "status_code": None,
            "error": "Connection timed out." if timeout < 15 else None,
        },
        "https://httpbin.org/delay/25": {
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


@pytest.fixture(scope="function", autouse=True)
def patch_validate_api_url(is_main_branch):
    """
    Conditionally patches the validate_api_url function based on the Git branch.

    If the current branch is "main" or "master", the real validate_api_url function is used.
    Otherwise, the mock_validate_api_url function is used.

    This fixture is automatically applied to all tests (autouse=True).

    Args:
        is_main_branch: Fixture that determines if the current branch is main or master.

    Yields:
        None: This fixture doesn't yield a value, it just applies the patch.
    """
    if is_main_branch:
        # On main/master branches, use the real function
        yield
    else:
        # On other branches, use the mock function
        # Patch both the direct import in api module and the import in config module
        with mock.patch(
            "i18n_tools.api.validate_api_url", mock_validate_api_url
        ), mock.patch(
            "i18n_tools.config.validate_api_url", mock_validate_api_url
        ), mock.patch(
            "i18n_tools.models.repository.validate_api_url", mock_validate_api_url
        ):
            yield


@pytest.fixture(scope="function", autouse=True)
def patch_validate_email(is_main_branch):
    """
    Conditionally patches the validate_email function based on the Git branch.

    If the current branch is "main" or "master", the real validate_email function is used.
    Otherwise, the mock_validate_email function is used.

    This fixture is automatically applied to all tests (autouse=True).

    Args:
        is_main_branch: Fixture that determines if the current branch is main or master.

    Yields:
        None: This fixture doesn't yield a value, it just applies the patch.
    """
    if is_main_branch:
        # On main/master branches, use the real function
        yield
    else:
        # On other branches, use the mock function
        # Patch both the direct import in email_validator module and the import in config module
        with mock.patch(
            "email_validator.validate_email", mock_validate_email
        ), mock.patch("i18n_tools.config.validate_email", mock_validate_email):
            yield
