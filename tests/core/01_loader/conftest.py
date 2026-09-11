import pytest


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
