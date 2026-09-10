"""
This module handles interactions with online translation services and provides functions to facilitate the retrieval of translations. It is responsible for communicating with various translation APIs, managing authentication, and ensuring that translations are accurately fetched and stored. Additionally, it records the translators used in the authors' section of the configuration.

Key Responsibilities:
    - Dialogue with online translators.
    - Record translators used in the authors' section.
    - Provide functions for a command-line interface (CLI) to utilize package functionalities.

"""

from typing import Any


def validate_url_format(url: str) -> dict[str, Any]:
    """
    Validates the syntactic format of a URL — no network call.

    Structural-only check intended for synchronous model methods that must
    never perform I/O (e.g. Repository.add_translator()). The full
    availability check remains validate_api_url(), to be invoked explicitly
    and separately (DD-14c, DD-NN, KI-01).

    Requires the ``api`` extra (``validators``). Imported lazily so that
    core .i18t usage never pulls this dependency in (DD-41).

    :param url: The URL to validate.
    :return: A dictionary with the URL and an error message if the format is invalid.
    :raises ModuleNotFoundError: if the ``api`` extra is not installed.
    """
    try:
        import validators
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            "validate_url_format() requires the 'api' extra — "
            "install with: pip install pyi18t-tools[api]"
        ) from e

    result: dict[str, Any] = {"url": url, "error": None}
    if not validators.url(url):
        result["error"] = f"URL '{url}' is not a valid format."
    return result


def validate_api_url(url: str, timeout: int = 5) -> dict[str, Any]:
    """
    Validates a URL by checking its format and availability.

    Error messages are always in English (DD-35). When i18n-tools reaches a stable
    version, this function will use the package's own locale mechanism to produce
    locale-aware messages.

    Requires the ``api`` extra (``requests``, and transitively ``validators``
    via validate_url_format()). Imported lazily so that core .i18t usage
    never pulls this dependency in (DD-41).

    :param url: The URL to validate.
    :param timeout: Maximum wait time for the server response (in seconds).
    :return: A dictionary containing the validation status and details about the URL.
    :raises ModuleNotFoundError: if the ``api`` extra is not installed.
    """
    try:
        import requests
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            "validate_api_url() requires the 'api' extra — "
            "install with: pip install pyi18t-tools[api]"
        ) from e

    result: dict[str, Any] = {
        "url": url,
        "is_alive": False,
        "status_code": None,
        "error": None,
    }

    # Format check delegated to validate_url_format() — single source of truth
    # (raises its own ModuleNotFoundError first if 'validators' is missing)
    format_check = validate_url_format(url)
    if format_check["error"]:
        result["error"] = format_check["error"]
        return result

    # Check URL accessibility
    try:
        response = requests.get(url, timeout=timeout)
        result["status_code"] = response.status_code

        # Server is alive despite specific error codes
        if response.status_code in {401, 403, 405, 429, 500}:
            result["is_alive"] = (
                True  # Server alive but correct access needs adjustment
            )
        elif 200 <= response.status_code < 300:
            result["is_alive"] = True  # Server accessible and responding correctly
        else:
            result["error"] = f"Unexpected status code: {response.status_code}"
    except requests.exceptions.Timeout:
        result["error"] = "Connection timed out."
    except requests.exceptions.ConnectionError:
        result["error"] = "Unable to connect to server."
    except requests.exceptions.RequestException as e:
        result["error"] = str(e)

    return result
