import shutil

import yaml


def update_tmp_repository(key, root_dir, test_dir_conf):
    config_file = root_dir / test_dir_conf["config"] / test_dir_conf["settings"]
    with open(config_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    data[key]["paths"]["root"] = str(root_dir) + "/" + test_dir_conf["root"]
    data[key]["paths"]["repository"] = str(root_dir) + "/" + test_dir_conf["repository"]
    data[key]["paths"]["config"] = str(root_dir) + "/" + test_dir_conf["config"]
    data[key]["paths"]["settings"] = test_dir_conf["settings"]

    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump(data, f)


def copy_and_update_repository(root_conf_test, tmp_path, conf_tests, key):
    conf = conf_tests["repository"][key]
    source = root_conf_test / conf_tests["configuration"][key]
    destination = tmp_path / conf["root"]
    shutil.copytree(source, destination)
    update_tmp_repository(key, tmp_path, conf)
    return destination
