import pytest


@pytest.fixture(autouse=True)
def _patch_api(patch_validate_api_url):
    pass
