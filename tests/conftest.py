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
def tmp_repository(conf_tests, tmp_path) -> list:
    temp_path = tmp_path / conf_tests["setup"]["paths"]["application"]["base"]
    locales_dir = temp_path / "locales"
    locales_dir.mkdir(parents=True, exist_ok=True)

    config_yaml = temp_path / conf_tests["files"]["yaml"]
    config_toml = temp_path / conf_tests["files"]["toml"]
    config_err_yaml = temp_path / conf_tests["files"]["err_yaml"]

    config_yaml.write_text(
        """
        setup:
          paths:
            application:
                base: ''
                modules:
                  - mod1/
                  - mod2/pkg1/
                  - mod2/pkg2/
          languages:
            source: en
            hierarchy:
              fr: ["fr-FR", "fr-BE", "fr-CA"]
              en: ["en-IE", "en-US", "en-GB"]
            fallback: fr
          domains:
            package:
              "i18n_tools":
                - "domain1"
            application:
              "mod1":
                - "domain2"
                - "domain3"
              "mod2/pkg1/":
                - "domain4"
                - "domain5"
              "mod2/pkg2/":
                - "domain6"
                - "domain7"
        details:
            name: "Configuration test file"
            description: "This is a temporary configuration test file"
        authors:
            123e4567-e89b-12d3-a456-426614174000:
                first_name: "John"
                last_name: "Doe"
                email: "john.doe@example.com"
                url: "https://johndoe.com"
                languages:
                    - "en-US"
                    - "fr-CA"
        """
    )

    config_err_yaml.write_text(
        """
        setup:
          paths:
            application:
                base: ''
                modules:
                    - mod1/
                    - mod2/pkg1/
                    - mod2/pkg2/
          language:
            source: en
            hierarchy:
              fr: ["fr-FR", "fr-BE", "fr-CA"]
              en: ["en-IE", "en-US", "en-GB"]
            fallback: fr
          domains:
            package:
              "i18n_tools": ["domain1"]
            application:
              "mod1/": ["domain2", "domain3"]
              "mod2/pkg1/": ["domain4", "domain5"]
              "mod2/pkg2/": ["domain6", "domain7"]
        details:
            name: "Configuration test file"
            description: "This is a temporary configuration test file"
        authors:
            123e4567-e89b-12d3-a456-426614174000:
                first_name: "John"
                last_name: "Doe"
                email: "john.doe@example.com"
                url: "https://johndoe.com"
                languages:
                    - "en-US"
                    - "fr-CA"
        """
    )

    return [
        temp_path,
        locales_dir,
        temp_path.parent,
        config_yaml,
        config_toml,
        config_err_yaml,
    ]
