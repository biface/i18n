import pytest

from i18n_tools.api import validate_api_url as _real_validate_api_url


@pytest.fixture
def get_validate_api_url(use_real_network_resources):
    """
    Returns the appropriate validate_api_url function based on the current branch.

    On main/master: real validate_api_url (network calls).
    On dev branches: mock_validate_api_url from conftest.py (no network).
    """
    if use_real_network_resources:
        return _real_validate_api_url
    from tests.conftest import mock_validate_api_url as _mock

    return _mock


@pytest.mark.network
class TestValidateApiUrl:
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
    def test_validate_api_url_valid_cases(self, url, expected, get_validate_api_url):
        """
        Tests validate_api_url with valid URLs.

        Uses real or mock function based on the current branch.
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
                    "error": "URL 'invalid_url' is not a valid format.",
                },
            ),
            (
                "ftp://example.com",
                {
                    "is_alive": False,
                    "status_code": None,
                    "error": "STRUCTURE_ONLY",  # RequestException — text from requests lib, uncontrolled
                },
            ),
            (
                "http://",
                {
                    "is_alive": False,
                    "status_code": None,
                    "error": "STRUCTURE_ONLY",  # RequestException — text from requests lib, uncontrolled
                },
            ),
            (
                "https://",
                {
                    "is_alive": False,
                    "status_code": None,
                    "error": "STRUCTURE_ONLY",  # RequestException — text from requests lib, uncontrolled
                },
            ),
            (
                "https://thisurldoesnotexist12345.com",
                {
                    "is_alive": False,
                    "status_code": None,
                    "error": "Unable to connect to server.",  # controlled — api.py DD-35
                },
            ),
        ],
    )
    def test_validate_api_url_invalid_cases(self, url, expected, get_validate_api_url):
        """
        Tests validate_api_url with invalid or erroneous URLs.

        Controlled error messages (format, ConnectionError) are asserted by exact text.
        Uncontrolled messages (RequestException path) are asserted by structure only.
        """
        result = get_validate_api_url(url)
        assert result["is_alive"] == expected["is_alive"]
        assert result["status_code"] == expected["status_code"]
        if expected["error"] == "STRUCTURE_ONLY":
            assert result["error"] is not None
        else:
            assert result["error"] == expected["error"]


@pytest.mark.network
@pytest.mark.timeout
class TestValidateApiUrlTimeouts:
    @pytest.mark.parametrize(
        "url,timeout,expected",
        [
            (
                "https://httpbin.org/delay/10",
                5,
                {
                    "is_alive": False,
                    "status_code": None,
                    "error": "Connection timed out.",
                },
            ),
            (
                "https://httpbin.org/delay/15",
                5,
                {
                    "is_alive": False,
                    "status_code": None,
                    "error": "Connection timed out.",
                },
            ),
            (
                "https://httpbin.org/delay/25",
                5,
                {
                    "is_alive": False,
                    "status_code": None,
                    "error": "Connection timed out.",
                },
            ),
        ],
    )
    def test_validate_api_url_timeouts(
        self, url, timeout, expected, get_validate_api_url
    ):
        """
        Tests validate_api_url with URLs simulating timeouts.

        Decorated @pytest.mark.network — runs on master only (real httpbin.org calls).
        On dev branches, patch_validate_api_url intercepts the call via the mock.
        Error message is always English (DD-35).
        """
        result = get_validate_api_url(url, timeout=timeout)
        assert result["is_alive"] == expected["is_alive"]
        assert result["status_code"] == expected["status_code"]
        assert result["error"] == expected["error"]


@pytest.mark.network
class TestValidateApiUrlDirect:
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
    def test_direct_validate_api_url(self, url, expected):
        """
        Tests validate_api_url imported directly.

        patch_validate_api_url (autouse) in conftest.py applies automatically:
        real function on master, mock on dev branches.
        """
        from i18n_tools.api import validate_api_url

        result = validate_api_url(url)
        assert result["is_alive"] == expected["is_alive"]
        assert result["status_code"] == expected["status_code"]
        assert result["error"] == expected["error"]
