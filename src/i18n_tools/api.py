"""
This module handles interactions with online translation services and provides functions to facilitate the retrieval of translations. It is responsible for communicating with various translation APIs, managing authentication, and ensuring that translations are accurately fetched and stored. Additionally, it records the translators used in the authors' section of the configuration.

Key Responsibilities:
    - Dialogue with online translators.
    - Record translators used in the authors' section.
    - Provide functions for a command-line interface (CLI) to utilize package functionalities.

"""

import requests
import validators


def validate_api_url(url: str, timeout: int = 5) -> dict:
    """
    Validates a URL by checking its format and availability.

    Error messages are always in English (DD-35). When i18n-tools reaches a stable
    version, this function will use the package's own locale mechanism to produce
    locale-aware messages.

    :param url: The URL to validate.
    :param timeout: Maximum wait time for the server response (in seconds).
    :return: A dictionary containing the validation status and details about the URL.
    """
    result = {
        "url": url,
        "is_alive": False,
        "status_code": None,
        "error": None,
    }

    # Validate URL format — message is already English (uses validators library)
    if not validators.url(url):
        result["error"] = f"URL '{url}' is not a valid format."
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
