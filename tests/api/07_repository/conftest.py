"""
tmp_class_repository, moved here from tests/core/02_models/conftest.py:
it was only ever consumed by test_00_repository.py (Repository model
tests), which itself moved to tests/api/07_repository/ because
Repository's translator/author payload validation calls
api.validate_url_format() — requiring the `api` extra (`validators`),
even though Repository itself imports cleanly without it.
"""

import copy
import os

import pytest
from helpers import copy_and_update_repository


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

    # Work on a deep copy to avoid mutating the session-scoped conf_tests data
    repository_class = copy.deepcopy(conf_tests["repository-content"])
    repository_class["paths"]["root"] = str(destination_application)
    repository_class["paths"]["repository"] = str(destination_application)
    repository_class["paths"]["config"] = str(
        destination_application / "fsm_tools" / "locales" / "_i18n_tools"
    )
    repository_class["paths"]["backup"] = str(
        destination_application / "fsm_tools" / "locales" / "_i18n_tools" / "backup"
    )

    return [
        [str(tmp_path), tmp_path],
        [str(destination_package), destination_package],
        [str(destination_application), destination_application],
        [str(other), other],
        repository_class,
    ]
