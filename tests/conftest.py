import os
import shutil
from pathlib import Path

import pytest
import yaml
from dill.pointers import parent


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


@pytest.fixture(scope="function")
def tmp_full_repository(root_conf_test, conf_tests, tmp_path) -> list:
    def update_file(key, file_path):
        with open(
            file_path / "locales/_i18n_tools/i18n-tools.yaml", "r", encoding="utf-8"
        ) as f:
            data = yaml.safe_load(f)

        data[key]["paths"]["root"] = str(file_path)
        data[key]["paths"]["repository"] = str(file_path / "locales")
        data[key]["paths"]["config"] = str(file_path / "locales/_i18n_tools/")
        data[key]["paths"]["settings"] = str(
            file_path / "locales/_i18n_tools/error/i18n-tools.yaml"
        )

        with open(
            file_path / "locales/_i18n_tools/i18n-tools.yaml", "w", encoding="utf-8"
        ) as f:
            yaml.dump(data, f)

    source_package = root_conf_test / conf_tests["configuration"]["package"]
    destination_package = tmp_path / conf_tests["repository"]["package"]
    shutil.copytree(source_package, destination_package)

    update_file("package", destination_package)

    source_application = root_conf_test / conf_tests["configuration"]["application"]
    destination_application = tmp_path / conf_tests["repository"]["application"]
    shutil.copytree(source_application, destination_application)

    update_file("application", destination_application)

    other = tmp_path / conf_tests["repository"]["other"]
    os.makedirs(other, exist_ok=True)

    return [
        str(tmp_path),
        str(destination_package),
        str(destination_application),
        other,
        conf_tests,
    ]
