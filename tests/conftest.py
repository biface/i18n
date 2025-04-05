import os
import shutil
from pathlib import Path

import pytest
import yaml


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
    config_file = root_dir /test_dir_conf["config"] / test_dir_conf["settings"]
    with open(config_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    data[key]["paths"]["root"] = str(root_dir) + "/" + test_dir_conf["root"]
    data[key]["paths"]["repository"] = str(root_dir) + "/" + test_dir_conf["repository"]
    data[key]["paths"]["config"] = str(root_dir) + "/" + test_dir_conf["config"]
    data[key]["paths"]["settings"] = test_dir_conf["settings"]

    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump(data, f)

@pytest.fixture(scope="function")
def tmp_function_repository(root_conf_test, conf_tests, tmp_path) -> list:

    source_package = root_conf_test / conf_tests["configuration"]["package"]
    destination_package = tmp_path / conf_tests["repository"]["package"]["root"]
    shutil.copytree(source_package, destination_package)

    update_tmp_repository("package", tmp_path, conf_tests["repository"]["package"])

    source_application = root_conf_test / conf_tests["configuration"]["application"]
    destination_application = tmp_path / conf_tests["repository"]["application"]["root"]
    shutil.copytree(source_application, destination_application)

    update_tmp_repository("application", tmp_path, conf_tests["repository"]["application"])

    other = tmp_path / conf_tests["repository"]["other"]
    os.makedirs(other, exist_ok=True)

    return [
        [str(tmp_path), tmp_path],
        [str(destination_package), destination_package],
        [str(destination_application), destination_package],
        [str(other), other],
        conf_tests,
    ]

@pytest.fixture(scope="module")
def tmp_module_repository(root_conf_test, conf_tests, tmp_path_factory) -> list:

    tmp_path = tmp_path_factory.mktemp("module-factory")
    source_package = root_conf_test / conf_tests["configuration"]["package"]
    destination_package = tmp_path / conf_tests["repository"]["package"]["root"]
    shutil.copytree(source_package, destination_package)

    update_tmp_repository("package", tmp_path, conf_tests["repository"]["package"])

    source_application = root_conf_test / conf_tests["configuration"]["application"]
    destination_application = tmp_path / conf_tests["repository"]["application"]["root"]
    shutil.copytree(source_application, destination_application)

    update_tmp_repository("application", tmp_path, conf_tests["repository"]["application"])

    other = tmp_path / conf_tests["repository"]["other"]
    os.makedirs(other, exist_ok=True)

    return [
        [str(tmp_path), tmp_path],
        [str(destination_package), destination_package],
        [str(destination_application), destination_application],
        [str(other), other],
    ]
