Settings module (internal)
==========================

Low-level settings-file I/O (JSON, YAML, TOML), at the same level as the utils
module. Internal module: imported by the handler module only.

.. automodule:: i18n_tools.loaders._settings
    :private-members: _check_config_extension, _load_toml, _save_toml
    :no-index:

    .. autofunction:: load_config_file
        :no-index:
    .. autofunction:: save_config_file
        :no-index:
    .. autofunction:: _check_config_extension
        :no-index:
    .. autofunction:: _load_toml
        :no-index:
    .. autofunction:: _save_toml
        :no-index:
