import os
import shutil
import subprocess
from pathlib import Path
from unittest import mock

import pytest
import yaml
from email_validator import EmailNotValidError

from i18n_tools.api import validate_api_url
from i18n_tools.config import Config


@pytest.fixture(scope="session")
def root_conf_test() -> Path:
    return Path(__file__).parent


@pytest.fixture(scope="session")
def conf_tests(root_conf_test) -> dict:
    config_path = root_conf_test / "parametrize.yaml"
    with open(config_path, "r") as file:
        return yaml.safe_load(file)


@pytest.fixture(scope="function")
def tmp_repository(root_conf_test, conf_tests, tmp_path) -> list:
    repository_config = conf_tests["repository"]
    files_config = conf_tests["files"]

    temp_path = tmp_path / conf_tests["setup"]["paths"]["application"]["base"]
    locales_dir = temp_path / "locales"
    locales_dir.mkdir(parents=True, exist_ok=True)

    config_yaml = temp_path / files_config["yaml"]
    config_toml = temp_path / files_config["toml"]
    config_err_yaml = temp_path / files_config["err_yaml"]

    valid_repository_conf = (
        root_conf_test
        / repository_config["locale"]
        / repository_config["configuration"]["valid"]
    )
    error_repository_conf = (
        root_conf_test
        / repository_config["locale"]
        / repository_config["configuration"]["error"]
    )

    with open(valid_repository_conf, "r", encoding="utf-8") as f:
        config_content = f.read()
        config_yaml.write_text(config_content)

    with open(error_repository_conf, "r", encoding="utf-8") as f:
        err_content = f.read()
        config_err_yaml.write_text(err_content)

    return [
        temp_path,
        locales_dir,
        temp_path.parent,
        config_yaml,
        config_toml,
        config_content,
        err_content,
    ]


def update_tmp_repository(key, root_dir, test_dir_conf):
    config_file = root_dir / test_dir_conf["config"] / test_dir_conf["settings"]
    with open(config_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    data[key]["paths"]["root"] = str(root_dir) + "/" + test_dir_conf["root"]
    data[key]["paths"]["repository"] = str(root_dir) + "/" + test_dir_conf["repository"]
    data[key]["paths"]["config"] = str(root_dir) + "/" + test_dir_conf["config"]
    data[key]["paths"]["settings"] = test_dir_conf["settings"]

    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump(data, f)


def copy_and_update_repository(root_conf_test, tmp_path, conf_tests, key):
    conf = conf_tests["repository"][key]
    source = root_conf_test / conf_tests["configuration"][key]
    destination = tmp_path / conf["root"]
    shutil.copytree(source, destination)
    update_tmp_repository(key, tmp_path, conf)
    return destination


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


@pytest.fixture(scope="class")
def tmp_class_repository(root_conf_test, conf_tests, tmp_path_factory) -> list:

    tmp_path = tmp_path_factory.mktemp("class-factory")
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
            "error": "Le délai de connexion a expiré.",
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
    print(f"mock_validate_api_url called with URL: {url}")
    return simulated_responses.get(
        url,
        {
            "url": url,
            "is_alive": False,
            "status_code": None,
            "error": f"Aucune réponse simulée pour l'URL '{url}'.",
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
        ), mock.patch("i18n_tools.config.validate_api_url", mock_validate_api_url):
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
