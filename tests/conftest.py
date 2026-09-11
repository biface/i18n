# ---------------------------------------------------------------------------
# TEST EXECUTION ORDER
#
# The Config class uses patterns.Singleton: only one instance exists per
# pytest process. Verified empirically after the core/api test-tree split
# (DD-41): running tests/core + tests/api together in one process (the
# test-unit job) passes in full; tests/core alone runs with zero [api]
# dependencies installed. Only tests/api/09_config/test_config.py and
# tests/api/07_repository/test_00_repository.py construct a Config/
# Repository singleton — nothing in tests/core does, despite an earlier
# version of this comment claiming otherwise.
# ---------------------------------------------------------------------------

import copy
import locale as _locale
import os
import subprocess
from pathlib import Path

import pytest
import yaml
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


def is_tag_ref():
    """
    Determines whether the current run was triggered by a tag push.

    actions/checkout leaves a detached HEAD on tag builds, so
    get_current_git_branch() cannot resolve "main"/"master" there even
    when the run should use real network resources.

    test-integration remains tag-gated
    (if: startsWith(github.ref, 'refs/tags/')), so every real run of
    that job is, by construction, a tag build. coverage was opened up
    to master/staging/**/pull_request on 2026-07-27 — it is NOT always
    a tag build anymore; see use_real_network_resources() below for how
    it still gets real network resources in those other contexts.

    Checks GITHUB_REF (GitHub) for a refs/tags/ prefix, or CI_COMMIT_TAG
    (GitLab).

    Returns:
        bool: True if this run was triggered by a tag, False otherwise.
    """
    github_ref = os.getenv("GITHUB_REF")
    if github_ref and github_ref.startswith("refs/tags/"):
        return True
    return bool(os.getenv("CI_COMMIT_TAG"))


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

    True when any of:
    - the branch is main/master,
    - the run was triggered by a tag (is_tag_ref()),
    - HTTPBIN_BASE_URL is set.

    The third condition matters specifically for the coverage job: it
    runs its own go-httpbin service container and sets HTTPBIN_BASE_URL
    to point at it — real network resources should always be used there,
    regardless of branch, since that container's whole purpose is to be
    hit for real. Before coverage was opened up to master/staging/**/
    pull_request (2026-07-27), it only ever ran on tags, so is_tag_ref()
    alone was always true there and this case never came up. On a
    pull_request event in particular, GITHUB_REF is
    "refs/pull/<n>/merge" — neither a branch nor a tag ref — so without
    this third condition the mock path would activate for a job that
    has a real container ready and waiting, and the mock's simulated
    responses (built for the public httpbingo.org URLs used elsewhere,
    never this container's own host:port) would not recognize the
    container's URL at all.

    test-unit never sets HTTPBIN_BASE_URL, so this condition does not
    widen real-network use to that job.

    Returns:
        bool: True if real network resources should be used, False if mocks should be used.
    """
    return is_main_branch or is_tag_ref() or bool(os.getenv("HTTPBIN_BASE_URL"))
