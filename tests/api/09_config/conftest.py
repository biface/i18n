import pytest


@pytest.fixture(autouse=True)
def _patches(patch_validate_api_url, patch_validate_email):
    pass
